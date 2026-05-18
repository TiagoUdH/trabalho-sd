from flask import Flask, request, jsonify
import cv2
import numpy as np
import os
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
nome_do_no = os.environ.get('NOME_NO', 'Worker Desconhecido')

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


@app.route('/processar', methods=['POST'])
def processar_quadrante():
    try:
        request_id = request.headers.get('X-Request-ID', 'sem-id')

        if 'imagem' not in request.files:
            return jsonify({"erro": "Nenhum arquivo recebido", "no_responsavel": nome_do_no}), 400
            
        file = request.files['imagem']
        image_bytes = file.read()

        np_img = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({"erro": "A imagem chegou corrompida no nó", "no_responsavel": nome_do_no}), 422

        altura, largura, canais = img.shape
        _log(request_id, 'fragmento_recebido', largura=largura, altura=altura)


        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        mask1 = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([160, 50, 50]), np.array([180, 255, 255]))
        mascara = cv2.bitwise_or(mask1, mask2)

        tem_vermelho = bool(np.any(mascara > 0))

        _log(request_id, 'fragmento_processado', encontrou_vermelho=tem_vermelho)

        return jsonify({
            "no_responsavel": nome_do_no,
            "request_id": request_id,
            "encontrou_vermelho": tem_vermelho
        })
    except Exception as e:
        return jsonify({"erro": f"Crash interno: {str(e)}", "no_responsavel": nome_do_no}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)