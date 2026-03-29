from flask import Flask, request, jsonify
import cv2
import numpy as np
import requests
import concurrent.futures

app = Flask(__name__)

NOS = {
    "quadrante_1": "http://no-1:5000/processar", 
    "quadrante_2": "http://no-2:5000/processar", 
    "quadrante_3": "http://no-3:5000/processar", 
    "quadrante_4": "http://no-4:5000/processar"  
}

def enviar_para_no(url_do_no, nome_quadrante, imagem_cortada):
    sucesso, img_encoded = cv2.imencode('.png', imagem_cortada)
    
    if not sucesso:
        return {"erro": "Falha ao gerar pacote", "no_responsavel": url_do_no}

    files = {'imagem': (f'{nome_quadrante}.png', img_encoded.tobytes(), 'image/png')}
    
    try:
        resposta = requests.post(url_do_no, files=files)
        
        # Tenta ler o JSON. Se falhar, captura o erro real que o Worker está cuspindo!
        try:
            return resposta.json()
        except ValueError:
            return {
                "erro": f"Erro interno do Worker (Status {resposta.status_code}): {resposta.text[:100]}", 
                "no_responsavel": url_do_no
            }
            
    except Exception as e:
        return {"erro": f"Erro de rede: {str(e)}", "no_responsavel": url_do_no}

@app.route('/analisar', methods=['POST'])
def analisar_imagem():
    if 'imagem' not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada"}), 400

    file = request.files['imagem']
    np_img = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"erro": "Mestre não conseguiu ler a imagem original"}), 400

    altura, largura, _ = img.shape
    metade_a, metade_l = altura // 2, largura // 2

    quadrantes = {
        "quadrante_1": img[:metade_a, :metade_l].copy(),
        "quadrante_2": img[:metade_a, metade_l:].copy(),
        "quadrante_3": img[metade_a:, :metade_l].copy(),
        "quadrante_4": img[metade_a:, metade_l:].copy() 
    }

    resultados_finais = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for nome, pedaco_img in quadrantes.items():
            url = NOS[nome]
            futures.append(executor.submit(enviar_para_no, url, nome, pedaco_img))
        
        for future in concurrent.futures.as_completed(futures):
            resultado = future.result()
            nome_no = resultado.get('no_responsavel', 'Worker Desconhecido')
            
            if 'encontrou_vermelho' in resultado:
                resultados_finais[nome_no] = resultado['encontrou_vermelho']
            else:
                resultados_finais[nome_no] = f"FALHA: {resultado.get('erro', 'Erro desconhecido')}"

    tem_vermelho_geral = any(val is True for val in resultados_finais.values())

    return jsonify({
        "status": "Processamento Distribuído Concluído",
        "detalhes_por_no": resultados_finais,
        "conclusao_final": f"A cor vermelha {'FOI' if tem_vermelho_geral else 'NÃO FOI'} detectada na imagem."
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)