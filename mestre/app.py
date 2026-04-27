from flask import Flask, request, jsonify
import cv2
import numpy as np
import requests
import threading
import queue
import os

app = Flask(__name__)

_workers_env = os.environ.get(
    'WORKERS',
    'http://no-1:5000/processar,http://no-2:5000/processar,http://no-3:5000/processar,http://no-4:5000/processar'
)
NOS = [url.strip() for url in _workers_env.split(',') if url.strip()]

# Quantas fatias gerar a partir da imagem. Maior que len(NOS) permite que
# workers rápidos peguem mais trabalho que workers lentos (load balancing real).
SLICES = int(os.environ.get('SLICES', len(NOS) * 2))

# Quantas vezes uma fatia pode ser reenviada antes de ser dada como perdida.
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', 3))


def enviar_para_no(url_do_no, nome_fatia, imagem_cortada):
    sucesso, img_encoded = cv2.imencode('.png', imagem_cortada)

    if not sucesso:
        return {"erro": "Falha ao gerar pacote", "no_responsavel": url_do_no}

    files = {'imagem': (f'{nome_fatia}.png', img_encoded.tobytes(), 'image/png')}

    try:
        resposta = requests.post(url_do_no, files=files, timeout=10)
        try:
            return resposta.json()
        except ValueError:
            return {
                "erro": f"Erro interno do Worker (Status {resposta.status_code}): {resposta.text[:100]}",
                "no_responsavel": url_do_no
            }
    except requests.exceptions.ConnectionError:
        return {"erro": f"Worker indisponível (sem conexão)", "no_responsavel": url_do_no}
    except requests.exceptions.Timeout:
        return {"erro": f"Worker não respondeu no tempo limite (10s)", "no_responsavel": url_do_no}
    except Exception as e:
        return {"erro": f"Erro inesperado: {type(e).__name__}", "no_responsavel": url_do_no}


def consumidor(url_do_no, fila, resultados, lock):
    """Loop de um worker: puxa tarefas da fila, processa, e em caso de falha
    devolve a tarefa para a fila para que outro worker tente."""
    while True:
        try:
            tarefa = fila.get_nowait()
        except queue.Empty:
            return

        nome_fatia, fatia, tentativas = tarefa
        resultado = enviar_para_no(url_do_no, nome_fatia, fatia)

        if 'encontrou_vermelho' in resultado:
            with lock:
                resultados[nome_fatia] = {
                    "no_responsavel": resultado.get('no_responsavel', url_do_no),
                    "encontrou_vermelho": resultado['encontrou_vermelho'],
                    "tentativas": tentativas + 1
                }
            fila.task_done()
        else:
            # Falha: devolve a tarefa para a fila se ainda houver tentativas.
            if tentativas + 1 < MAX_RETRIES:
                fila.put((nome_fatia, fatia, tentativas + 1))
                fila.task_done()
            else:
                with lock:
                    resultados[nome_fatia] = {
                        "no_responsavel": url_do_no,
                        "erro": resultado.get('erro', 'Erro desconhecido'),
                        "tentativas": tentativas + 1
                    }
                fila.task_done()


@app.route('/analisar', methods=['POST'])
def analisar_imagem():
    if 'imagem' not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada"}), 400

    file = request.files['imagem']
    np_img = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"erro": "Mestre não conseguiu ler a imagem original"}), 400

    if not NOS:
        return jsonify({"erro": "Nenhum worker configurado"}), 500

    altura, _, _ = img.shape
    m = max(1, SLICES)
    tamanho_fatia = altura // m
    fila = queue.Queue()
    for i in range(m):
        inicio = i * tamanho_fatia
        fim = (i + 1) * tamanho_fatia if i < m - 1 else altura
        fila.put((f'fatia_{i + 1}', img[inicio:fim, :].copy(), 0))

    resultados = {}
    lock = threading.Lock()

    # Uma thread consumidora por worker. Workers ociosos puxam mais tarefas;
    # tarefas de workers que falharem são redistribuídas via fila.
    threads = [
        threading.Thread(target=consumidor, args=(url, fila, resultados, lock))
        for url in NOS
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Conta carga distribuída por nó (quantas fatias cada worker processou com sucesso).
    carga_por_no = {}
    sucessos = []
    falhas = []
    for nome_fatia, info in resultados.items():
        if 'encontrou_vermelho' in info:
            sucessos.append(info['encontrou_vermelho'])
            carga_por_no[info['no_responsavel']] = carga_por_no.get(info['no_responsavel'], 0) + 1
        else:
            falhas.append({"fatia": nome_fatia, "erro": info['erro']})

    tem_vermelho_geral = any(sucessos)

    return jsonify({
        "status": "Processamento Distribuído Concluído",
        "fatias_processadas": len(sucessos),
        "fatias_com_falha": falhas,
        "carga_por_no": carga_por_no,
        "detalhes_por_fatia": resultados,
        "conclusao_final": f"A cor vermelha {'FOI' if tem_vermelho_geral else 'NÃO FOI'} detectada na imagem."
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)