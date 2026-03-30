# Sistema Distribuído de Processamento de Imagens

Um sistema de computação distribuída que detecta cores em imagens dividindo o processamento entre múltiplos nós workers em paralelo.

## 📋 O que o Projeto Faz

Este projeto implementa um **sistema mestre-worker distribuído** que:

1. **Recebe uma imagem** via requisição HTTP
2. **Divide a imagem em 4 quadrantes** (superior-esquerdo, superior-direito, inferior-esquerdo, inferior-direito)
3. **Distribui o processamento** de forma paralela para 4 nós workers diferentes
4. **Detecta cor vermelha** em cada quadrante usando visão computacional (OpenCV)
5. **Consolida os resultados** de todos os nós e retorna um relatório completo

### Arquitetura

```
┌─────────────────────┐
│   Cliente HTTP      │
└──────────┬──────────┘
           │ POST /analisar
┌──────────▼──────────────────┐
│   Nó Mestre (Master)        │
│   - Recebe imagem            │
│   - Divide em quadrantes     │
│   - Distribui para workers   │
│   - Consolida resultados     │
└──────────┬──────────────────┘
       ┌───┼───┬───┬───┐
       │   │   │   │   │
   ┌───▼┐ ┌─▼──┐ ┌─▼──┐ ┌─▼──┐
   │Nó 1│ │Nó 2│ │Nó 3│ │Nó 4│  (Workers)
   └────┘ └────┘ └────┘ └────┘
```

## 🚀 Setup

### Pré-requisitos

- Docker
- Docker Compose

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/TiagoUdH/trabalho-sd.git
cd trabalho-sd
```

2. Inicie os containers com Docker Compose:
```bash
docker-compose up --build
```

Isso irá:
- Construir as imagens Docker para o mestre e workers
- Iniciar 1 nó mestre (porta 5000)
- Iniciar 4 nós workers em uma rede interna isolada
- Configurar a rede compartilhada (`rede-cluster`) para comunicação

### Parar o Sistema

```bash
docker-compose down
```

## 💻 Como Usar

### Enviando uma Imagem para Análise

Faça uma requisição POST para o nó mestre com uma imagem:

```bash
curl -X POST \
  -F "imagem=@sua_imagem.jpg" \
  http://localhost:5000/analisar
```

### Resposta Esperada

```json
{
  "status": "Processamento Distribuído Concluído",
  "detalhes_por_no": {
    "http://no-1:5000/processar": true,
    "http://no-2:5000/processar": false,
    "http://no-3:5000/processar": true,
    "http://no-4:5000/processar": false
  },
  "conclusao_final": "A cor vermelha FOI detectada na imagem."
}
```

### Exemplos com Python

```python
import requests

# Enviar imagem para análise
with open('imagem.jpg', 'rb') as f:
    files = {'imagem': f}
    resposta = requests.post('http://localhost:5000/analisar', files=files)
    resultado = resposta.json()
    
print(resultado)
```

### Usando cURL (Linux/Mac/Windows)

```bash
# Analisar uma imagem
curl -X POST \
  -F "imagem=@minhaFoto.png" \
  http://localhost:5000/analisar | jq .
```

## 📝 Estrutura do Projeto

```
trabalho-sd/
├── docker-compose.yml      # Configuração dos containers
├── mestre/
│   ├── app.py             # Aplicação do nó mestre
│   ├── Dockerfile         # Imagem Docker
│   └── requirements.txt    # Dependências Python
└── worker/
    ├── app.py             # Aplicação do nó worker
    ├── Dockerfile         # Imagem Docker
    └── requirements.txt    # Dependências Python
```

## 🔍 Detalhes Técnicos

### Nó Mestre (`mestre/app.py`)

- **Framework**: Flask
- **Endpoint**: `POST /analisar`
- **Funcionalidades**:
  - Recebe imagem em qualquer formato suportado pelo OpenCV
  - Divide a imagem em 4 quadrantes iguais
  - Usa `ThreadPoolExecutor` para enviar requisições em paralelo aos workers
  - Aguarda respostas de todos os nós
  - Consolida e retorna os resultados

### Nó Worker (`worker/app.py`)

- **Framework**: Flask
- **Endpoint**: `POST /processar`
- **Funcionalidades**:
  - Recebe um quadrante de imagem
  - Converte de BGR para HSV (melhor para detecção de cores)
  - Aplica máscara para detectar vermelho (duas faixas: 0-10 e 160-180 em H)
  - Retorna `true` se detectou vermelho, `false` caso contrário

### Detecção de Vermelho

A detecção usa conversão HSV e máscaras:
- **Vermelho claro**: H entre 0-10
- **Vermelho escuro**: H entre 160-180
- Com saturação e valor mínimos para evitar falsos positivos

## 🛠️ Dependências

### Mestre
- `flask` - Framework web
- `opencv-python-headless` - Processamento de imagens (sem interface gráfica)
- `numpy` - Operações numéricas
- `requests` - Requisições HTTP paralelas

### Worker
- `flask` - Framework web
- `opencv-python-headless` - Processamento de imagens
- `numpy` - Operações numéricas

## 📊 Fluxo de Execução

1. Cliente envia imagem via HTTP POST para `/analisar`
2. Mestre carrega a imagem e a divide em 4 quadrantes
3. Mestre dispara 4 requisições HTTP em paralelo para os workers
4. Cada worker processa seu quadrante independentemente
5. Workers retornam resultado booleano (detectou vermelho ou não)
6. Mestre coleta todos os resultados
7. Mestre consolida: retorna detalhes por nó e conclusão geral
8. Resposta é entregue ao cliente

## 🔧 Troubleshooting

### Erro: "Connection refused"
- Verifique se os containers estão rodando: `docker-compose ps`
- Espere alguns segundos para todos os serviços iniciarem

### Erro: "Imagem corrompida"
- Certifique-se de enviar um formato válido (JPG, PNG, BMP, etc.)
- Verifique se o arquivo existe e não está vazio

### Verificar Logs
```bash
docker-compose logs          # Todos os serviços
docker-compose logs no-mestre   # Apenas mestre
docker-compose logs no-1        # Apenas worker 1
```

## 📚 Conceitos Aprendidos

Este projeto demonstra:
- ✅ Arquitetura Mestre-Worker distribuída
- ✅ Processamento paralelo de tarefas
- ✅ Comunicação entre serviços via HTTP
- ✅ Containerização com Docker
- ✅ Visão computacional com OpenCV
- ✅ Tolerância a falhas (tratamento de erros)

## 📄 Licença

Projeto educacional para estudo de sistemas distribuídos.

---

**Autor**: Você  
**Data**: 2026
