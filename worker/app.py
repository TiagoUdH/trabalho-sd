from flask import Flask, jsonify
import cv2
import numpy as np
import pika
import base64
import os
import json
import logging
import time
import threading

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
nome_do_no = os.environ.get('NOME_NO', 'Worker Desconhecido')
RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')
FILA_TAREFAS = 'tarefas'

# Garante que a pasta de logs exista dentro do container
os.makedirs('/app/logs', exist_ok=True)

def _log(request_id, evento, **kwargs):
    logger.info(json.dumps({
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S'),
        "servico": nome_do_no,
        "request_id": request_id,
        "evento": evento,
        **kwargs
    }, ensure_ascii=False))

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "no": nome_do_no}), 200


def on_task(ch, method, properties, body):
    data = json.loads(body)
    request_id = data.get('request_id', 'sem-id')
    nome_fatia = data['nome_fatia']
    try:
        img_bytes = base64.b64decode(data['imagem'])
        img_array = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            _log(request_id, 'erro_imagem_corrompida', fatia=nome_fatia)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        altura, largura, _ = img.shape
        _log(request_id, 'fragmento_recebido', fatia=nome_fatia, largura=largura, altura=altura)

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([160, 50, 50]), np.array([180, 255, 255]))
        mascara = cv2.bitwise_or(mask1, mask2)
        tem_vermelho = bool(np.any(mascara > 0))

        _log(request_id, 'fragmento_processado', fatia=nome_fatia, encontrou_vermelho=tem_vermelho)

        if properties.reply_to:
            ch.basic_publish(
                exchange='',
                routing_key=properties.reply_to,
                body=json.dumps({
                    'request_id': request_id,
                    'nome_fatia': nome_fatia,
                    'no_responsavel': nome_do_no,
                    'encontrou_vermelho': tem_vermelho
                }),
                properties=pika.BasicProperties(
                    correlation_id=properties.correlation_id
                )
            )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        _log(request_id, 'erro_processamento', fatia=nome_fatia, erro=str(e))
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consumer():
    while True:
        try:
            conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            ch = conn.channel()
            ch.queue_declare(queue=FILA_TAREFAS, durable=True)
            ch.basic_qos(prefetch_count=1)
            ch.basic_consume(queue=FILA_TAREFAS, on_message_callback=on_task)
            _log('startup', 'consumer_iniciado', no=nome_do_no)
            ch.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            _log('startup', 'rabbitmq_indisponivel_aguardando')
            time.sleep(5)
        except Exception as e:
            _log('startup', 'erro_consumer', erro=str(e))
            time.sleep(5)


if __name__ == '__main__':
    threading.Thread(target=start_consumer, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)