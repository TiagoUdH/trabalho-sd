import requests

with open(r"C:\www\trabalho-sd\images\bitela.jpeg", 'rb') as f:
    r = requests.post('http://localhost:5000/analisar', files={'imagem': f})
    print(r.json())