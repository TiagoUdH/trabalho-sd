import requests

with open("C:\\Users\\tiago\\Downloads\\vermelho.png", 'rb') as f:
    r = requests.post('http://localhost:5000/analisar', files={'imagem': f})
    print(r.json())