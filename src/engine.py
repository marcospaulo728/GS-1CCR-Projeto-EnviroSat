from pathlib import Path
import os

from dotenv import load_dotenv
from ollama import chat

from src.telemetria import coletar
from src.alertas import avaliar
from src.alertas import resposta_automatica

class MissionEngine:
    def __init__(self):

        load_dotenv()

        self.model_name = os.getenv(
            "OLLAMA_MODEL",
            "gpt-oss:120b"
        )

        BASE_DIR = Path(__file__).resolve().parent.parent

        prompt_path = BASE_DIR / "prompts" / "system_prompt.md"

        self.system_prompt = (
            prompt_path.read_text(encoding="utf-8")
        )

    def status_snapshot(self):
        dados = coletar()
        texto = f"""
Temperatura: {dados['temperatura']}°C
Energia Solar: {dados['energia_solar']}%
Bateria: {dados['bateria']}%
Comunicação: {dados ['comunicacao']}
Sensor Térmico: {dados['sensor_termico']}
Precisão GPS: {dados['precisao_geolocalizacao']} %
"""
        return texto

    def analyze(self, pergunta_usuario):
        dados = coletar()
        alertas = avaliar(dados)
        acoes = resposta_automatica(dados)
        prompt = f"""
TELEMETRIA
Temperatura:
{dados['temperatura']} °C

Energia Solar:
{dados['energia_solar']} %

Bateria:
{dados['bateria']} %

Comunicação:
{dados['comunicacao']}

Sensor Térmico:
{dados['sensor_termico']}

Precisão GPS:
{dados['precisao_geolocalizacao']} %

ALERTAS
{alertas}

AÇÕES AUTOMÁTICAS
{acoes}

PERGUNTA
{pergunta_usuario}
"""
        resposta = chat(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content":self.system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return resposta.message.content