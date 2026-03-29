from flask import Flask, request, jsonify
import cv2
import numpy as np
import os

app = Flask(__name__)
nome_do_no = os.environ.get('NOME_NO', 'Worker Desconhecido')

@app.route('/processar', methods=['POST'])
def processar_quadrante():
    try:
        # Verifica se recebeu o arquivo
        if 'imagem' not in request.files:
            return jsonify({"erro": "Nenhum arquivo recebido", "no_responsavel": nome_do_no})
            
        file = request.files['imagem']
        image_bytes = file.read()

        # Decodifica a imagem
        np_img = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({"erro": "A imagem chegou corrompida no nó", "no_responsavel": nome_do_no})

        # Processamento de IA / Visão Computacional
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Máscara ajustada para pegar tanto o vermelho claro quanto o vermelho escuro (Paint)
        mask1 = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([160, 50, 50]), np.array([180, 255, 255]))
        mascara = cv2.bitwise_or(mask1, mask2)

        # bool() garante que o Flask consiga converter para JSON
        tem_vermelho = bool(np.any(mascara > 0))

        return jsonify({
            "no_responsavel": nome_do_no,
            "encontrou_vermelho": tem_vermelho
        })
    except Exception as e:
        return jsonify({"erro": f"Crash interno: {str(e)}", "no_responsavel": nome_do_no})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)