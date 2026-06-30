"""Testes de integração — sistema mestre-worker com RabbitMQ.

Pré-requisito: cluster Docker em execução.
    docker-compose up -d

Execução:
    pip install -r tests/requirements.txt
    pytest tests/ -v
"""
import io
import os
import subprocess
import time

import pytest
import requests
from PIL import Image

BASE_URL = os.getenv('MESTRE_URL', 'http://127.0.0.1:60363')
TIMEOUT = 60  # segundos aguardados para o mestre coletar todos os resultados


def _png(cor_rgb: tuple, tamanho: int = 100) -> io.BytesIO:
    """Gera um PNG de cor sólida em memória sem depender do OpenCV."""
    img = Image.new('RGB', (tamanho, tamanho), color=cor_rgb)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


@pytest.fixture(scope='session', autouse=True)
def cluster_ativo():
    """Pula toda a suíte se o mestre não estiver acessível."""
    try:
        requests.post(f'{BASE_URL}/analisar', timeout=5)
    except requests.exceptions.ConnectionError:
        pytest.skip(
            f'Mestre não acessível em {BASE_URL}. Suba o cluster: docker-compose up -d'
        )


# ── 1. Validação de entrada ──────────────────────────────────────────────────

def test_sem_arquivo_retorna_400():
    """POST sem arquivo deve retornar 400."""
    resp = requests.post(f'{BASE_URL}/analisar', timeout=TIMEOUT)
    assert resp.status_code == 400


def test_bytes_invalidos_retorna_400():
    """Arquivo corrompido (não é imagem) deve retornar 400."""
    resp = requests.post(
        f'{BASE_URL}/analisar',
        files={'imagem': ('fake.png', b'\x00\x01\x02\x03', 'image/png')},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 400


# ── 2. Detecção de cor ───────────────────────────────────────────────────────

def test_imagem_azul_nao_detecta_vermelho():
    """Imagem inteiramente azul: encontrou_vermelho deve ser false."""
    resp = requests.post(
        f'{BASE_URL}/analisar',
        files={'imagem': ('azul.png', _png((50, 50, 220)), 'image/png')},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    assert resp.json()['encontrou_vermelho'] is False


def test_imagem_vermelha_detecta_vermelho():
    """Imagem inteiramente vermelha: encontrou_vermelho deve ser true."""
    resp = requests.post(
        f'{BASE_URL}/analisar',
        files={'imagem': ('vermelho.png', _png((220, 30, 30)), 'image/png')},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    assert resp.json()['encontrou_vermelho'] is True


# ── 3. Contrato da resposta ──────────────────────────────────────────────────

def test_campos_obrigatorios_na_resposta():
    """Resposta 200 deve conter todos os campos do contrato."""
    resp = requests.post(
        f'{BASE_URL}/analisar',
        files={'imagem': ('verde.png', _png((30, 180, 30)), 'image/png')},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    data = resp.json()
    for campo in ('request_id', 'status', 'fatias_processadas', 'carga_por_no', 'conclusao_final'):
        assert campo in data, f'Campo ausente na resposta: {campo}'


# ── 4. Tolerância a falhas ───────────────────────────────────────────────────

def _detecta_ambiente():
    """Detecta se estamos no Docker Compose ou Kubernetes."""
    try:
        subprocess.run(
            ['kubectl', '-n', 'sistema-sd', 'get', 'deployment', 'worker'],
            check=True, capture_output=True
        )
        return 'k8s'
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'docker'


def test_worker_parado_redistribui():
    """
    Com um worker a menos, o RabbitMQ redistribui as fatias para os demais.
    O sistema deve concluir o processamento sem intervencao manual.
    Funciona tanto no Docker Compose (docker stop no-1) quanto no K8s (scale down).
    """
    ambiente = _detecta_ambiente()

    if ambiente == 'k8s':
        # Reduz de 5 para 4 replicas, simulando um worker parado
        subprocess.run(
            ['kubectl', '-n', 'sistema-sd', 'scale', 'deployment/worker', '--replicas=4'],
            check=True, capture_output=True
        )
        time.sleep(5)  # Aguarda o scale-down e rebalance do RabbitMQ
        try:
            resp = requests.post(
                f'{BASE_URL}/analisar',
                files={'imagem': ('test.png', _png((220, 30, 30)), 'image/png')},
                timeout=TIMEOUT,
            )
            data = resp.json()
            assert resp.status_code in (200, 207)
            assert data.get('fatias_processadas', 0) > 0
        finally:
            subprocess.run(
                ['kubectl', '-n', 'sistema-sd', 'scale', 'deployment/worker', '--replicas=5'],
                capture_output=True
            )
    else:
        subprocess.run(['docker', 'stop', 'no-1'], check=True, capture_output=True)
        try:
            time.sleep(2)
            resp = requests.post(
                f'{BASE_URL}/analisar',
                files={'imagem': ('test.png', _png((220, 30, 30)), 'image/png')},
                timeout=TIMEOUT,
            )
            data = resp.json()
            assert resp.status_code in (200, 207)
            assert data.get('fatias_processadas', 0) > 0
            assert 'Nó 1' not in data.get('carga_por_no', {}), (
                'No 1 estava parado mas apareceu como responsavel por alguma fatia'
            )
        finally:
            subprocess.run(['docker', 'start', 'no-1'], capture_output=True)
