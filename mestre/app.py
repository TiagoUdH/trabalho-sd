from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import numpy as np
import pika
import base64
import threading
import time
import os
import uuid
import json
import logging
import unicodedata

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def _log(request_id, evento, **kwargs):
    logger.info(json.dumps({
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S'),
        "servico": "mestre",
        "request_id": request_id,
        "evento": evento,
        **kwargs
    }, ensure_ascii=False))

app = Flask(__name__)
CORS(app)

os.makedirs('/app/logs', exist_ok=True)

RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')
FILA_TAREFAS = 'tarefas'
SLICES = int(os.environ.get('SLICES', 10))
TIMEOUT_RESULTADO = int(os.environ.get('TIMEOUT_RESULTADO', 30))


def _ascii(texto):
    """Remove acentos para compatibilidade com cv2.putText (não suporta Unicode)."""
    return unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')


def salvar_log_visual(request_id, fatias, resultados):
    """Empilha todas as fatias, anota o worker responsável e o resultado,
    e salva uma imagem única em /app/logs/resultado_<request_id>.png."""
    fatias_anotadas = []
    for i, fatia in enumerate(fatias):
        nome_fatia = f'fatia_{i + 1}'
        info = resultados.get(nome_fatia, {})
        copia = fatia.copy()
        # Garante altura mínima para o texto ficar visível
        if copia.shape[0] < 30:
            copia = cv2.copyMakeBorder(copia, 0, 30 - copia.shape[0], 0, 0, cv2.BORDER_CONSTANT)

        if 'encontrou_vermelho' in info:
            cor = (0, 0, 220) if info['encontrou_vermelho'] else (0, 180, 0)
            label = _ascii(f"{nome_fatia} | {info['no_responsavel']} | {'VERMELHO' if info['encontrou_vermelho'] else 'sem vermelho'}")
        else:
            cor = (100, 100, 100)
            label = _ascii(f"{nome_fatia} | FALHA")

        cv2.rectangle(copia, (0, 0), (copia.shape[1] - 1, copia.shape[0] - 1), cor, 3)
        cv2.putText(copia, label, (8, min(22, copia.shape[0] - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, cor, 2, cv2.LINE_AA)
        fatias_anotadas.append(copia)

    imagem_completa = np.vstack(fatias_anotadas)
    caminho = f'/app/logs/resultado_{request_id}.png'
    cv2.imwrite(caminho, imagem_completa)
    _log(request_id, 'log_visual_salvo', caminho=caminho)


@app.route('/analisar', methods=['POST'])
def analisar_imagem():
    if 'imagem' not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada"}), 400

    file = request.files['imagem']
    np_img = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"erro": "Mestre não conseguiu ler a imagem original"}), 400

    request_id = str(uuid.uuid4())[:8]
    t0 = time.time()
    _log(request_id, 'requisicao_recebida', slices=SLICES)

    altura, _, _ = img.shape
    m = max(1, SLICES)
    tamanho_fatia = altura // m
    fatias = []
    for i in range(m):
        inicio = i * tamanho_fatia
        fim = (i + 1) * tamanho_fatia if i < m - 1 else altura
        fatias.append(img[inicio:fim, :].copy())

    # Conecta ao broker e cria a fila de resposta exclusiva para este request
    try:
        conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        ch = conn.channel()
        ch.queue_declare(queue=FILA_TAREFAS, durable=True)
        reply_queue = ch.queue_declare(queue='', exclusive=True).method.queue
    except Exception as e:
        _log(request_id, 'erro_conexao_rabbitmq', erro=str(e))
        return jsonify({'erro': 'Falha ao conectar ao broker'}), 503

    # Publica cada fatia na fila de tarefas; workers competem para consumi-las
    for i, fatia in enumerate(fatias):
        nome = f'fatia_{i + 1}'
        _, buf = cv2.imencode('.png', fatia)
        ch.basic_publish(
            exchange='',
            routing_key=FILA_TAREFAS,
            body=json.dumps({
                'request_id': request_id,
                'nome_fatia': nome,
                'imagem': base64.b64encode(buf).decode('utf-8')
            }),
            properties=pika.BasicProperties(
                delivery_mode=2,
                reply_to=reply_queue,
                correlation_id=request_id
            )
        )
        _log(request_id, 'fatia_publicada', fatia=nome)

    # Coleta resultados via fila de resposta exclusiva até completar ou expirar
    resultados = {}
    stop = threading.Event()

    def on_result(channel, method, properties, body):
        data = json.loads(body)
        resultados[data['nome_fatia']] = data
        channel.basic_ack(delivery_tag=method.delivery_tag)
        _log(request_id, 'resultado_recebido', fatia=data['nome_fatia'], no=data.get('no_responsavel'))
        if len(resultados) >= len(fatias):
            stop.set()

    ch.basic_consume(queue=reply_queue, on_message_callback=on_result)

    deadline = time.time() + TIMEOUT_RESULTADO
    while not stop.is_set() and time.time() < deadline:
        conn.process_data_events(time_limit=0.5)

    conn.close()
    salvar_log_visual(request_id, fatias, resultados)

    _log(request_id, 'processamento_concluido',
         processadas=len([v for v in resultados.values() if 'encontrou_vermelho' in v]),
         falhas=len([v for v in resultados.values() if 'encontrou_vermelho' not in v]))

    carga_por_no = {}
    sucessos = []
    falhas = []
    for nome_fatia, info in resultados.items():
        if 'encontrou_vermelho' in info:
            sucessos.append(info['encontrou_vermelho'])
            carga_por_no[info['no_responsavel']] = carga_por_no.get(info['no_responsavel'], 0) + 1
        else:
            falhas.append({"fatia": nome_fatia, "erro": info.get('erro', 'Sem resposta (timeout)')})

    tem_vermelho_geral = any(sucessos)

    if len(sucessos) == 0:
        status_http = 500
        status_msg = "Falha Total: nenhuma fatia processada"
    elif falhas:
        status_http = 207
        status_msg = "Falha Parcial: algumas fatias não foram processadas"
    else:
        status_http = 200
        status_msg = "Processamento Distribuído Concluído"

    tempo_ms = round((time.time() - t0) * 1000)

    return jsonify({
        "request_id": request_id,
        "status": status_msg,
        "encontrou_vermelho": tem_vermelho_geral,
        "fatias_processadas": len(sucessos),
        "fatias_com_falha": falhas,
        "carga_por_no": carga_por_no,
        "detalhes_por_fatia": resultados,
        "conclusao_final": f"A cor vermelha {'FOI' if tem_vermelho_geral else 'NÃO FOI'} detectada na imagem.",
        "tempo_ms": tempo_ms
    }), status_http


@app.route('/resultado/<request_id>/imagem', methods=['GET'])
def obter_imagem_resultado(request_id):
    caminho = f'/app/logs/resultado_{request_id}.png'
    if not os.path.exists(caminho):
        return jsonify({"erro": "Imagem de resultado nao encontrada"}), 404
    return send_file(caminho, mimetype='image/png')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)