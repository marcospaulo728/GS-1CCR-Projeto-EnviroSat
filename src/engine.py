import os
import json
from ollama import Client
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

load_dotenv()

TRILHA = "envirosat"

client = Client(
    host="https://ollama.com",
    headers={"Authorization": "Bearer " + os.environ.get("OLLAMA_API_KEY", "")}
)


def llm(prompt, system=None, max_tokens=800, temperature=0.3):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        return client.chat(
            model="gpt-oss:120b",
            messages=messages,
            options={"num_predict": max_tokens, "temperature": temperature},
            stream=False
        )["message"]["content"].strip()
    except Exception as e:
        return f"⚠️  Erro ao consultar IA: {e}"


def load_system_prompt():
    path = Path(__file__).parent.parent / "prompts" / "system_prompt.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return (
        "Você é o EnviroSat Mission Control AI. Sua única função é analisar dados operacionais do satélite EnviroSat-1 e auxiliar operadores humanos do centro de controle. "
        "O EnviroSat-1 monitora: focos de incêndio florestal, desmatamento, áreas de preservação e gera dados ambientais para decisão em solo. "
        "Sempre conecte a análise técnica com o impacto terrestre: "
        "desmatamento, incêndios e monitoramento de áreas protegidas."
    )


class MissionEngine:

    MAX_HISTORICO = 5

    def __init__(self):
        self.trilha = TRILHA
        self.system_prompt = load_system_prompt()
        self.historico: list[dict] = []

    def is_ready(self) -> bool:
        return True

    def status_snapshot(self) -> str:
        dados, alertas = self._coletar()
        self._registrar_ciclo(dados, alertas)
        severidade = self._classificar_severidade(dados, alertas)
        return self._montar_painel(dados, alertas, severidade)

    def analyze(self, pergunta_usuario: str) -> str:
        dados, alertas = self._coletar()
        self._registrar_ciclo(dados, alertas)

        severidade = self._classificar_severidade(dados, alertas)
        nivel = severidade.get("severidade", "NORMAL")
        motivo = severidade.get("motivo", "")

        prompt = self._montar_prompt_analise(
            dados, alertas, nivel, motivo, pergunta_usuario
        )
        return llm(prompt, system=self.system_prompt, max_tokens=800, temperature=0.3)

    def _coletar(self) -> tuple[dict, list[str]]:
        try:
            from src.telemetria import coletar
            from src.alertas import avaliar
        except ImportError as e:
            dados_fallback = {
                "temperatura": 38,
                "energia_solar": 85,
                "bateria": 90,
                "precisao_geolocalizacao": 95
            }
            return dados_fallback, [f"⚠️  Módulo não encontrado: {e}"]

        dados = coletar()
        alertas = avaliar(dados)
        return dados, alertas

    def _registrar_ciclo(self, dados: dict, alertas: list[str]) -> None:
        ciclo = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "dados": dict(dados),
            "alertas": list(alertas),
        }
        self.historico.append(ciclo)
        if len(self.historico) > self.MAX_HISTORICO:
            self.historico.pop(0)

    def _classificar_severidade(self, dados: dict, alertas: list[str]) -> dict:
        prompt = (
            "Analise os dados de telemetria do satélite EnviroSat abaixo "
            "e classifique a severidade da missão.\n\n"
            f"Telemetria atual:\n{self._formatar_dados(dados)}\n\n"
            f"Alertas ativos: {', '.join(alertas) if alertas else 'Nenhum'}\n\n"
            "Responda SOMENTE com um objeto JSON, sem markdown, sem texto extra:\n"
            '{"severidade": "NORMAL" | "ATENÇÃO" | "CRÍTICO", '
            '"motivo": "<uma frase curta explicando>"}'
        )

        resposta = llm(prompt, max_tokens=120, temperature=0.1)

        try:
            resposta_limpa = (
                resposta.strip()
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )
            return json.loads(resposta_limpa)
        except (json.JSONDecodeError, ValueError):
            if len(alertas) >= 3:
                nivel = "CRÍTICO"
            elif len(alertas) >= 1:
                nivel = "ATENÇÃO"
            else:
                nivel = "NORMAL"
            return {"severidade": nivel, "motivo": "Classificação automática por presença de alertas."}

    def _montar_prompt_analise(
        self,
        dados: dict,
        alertas: list[str],
        nivel: str,
        motivo: str,
        pergunta: str,
    ) -> str:

        alertas_fmt = (
            "\n".join(f"  ❗ {a}" for a in alertas)
            if alertas
            else "  ✅ Nenhum alerta ativo no momento."
        )

        return (
            "=== TELEMETRIA ATUAL DO EnviroSat ===\n"
            f"{self._formatar_dados(dados)}\n\n"
            "=== ALERTAS ATIVOS ===\n"
            f"{alertas_fmt}\n\n"
            "=== SEVERIDADE CLASSIFICADA ===\n"
            f"  Nível : {nivel}\n"
            f"  Motivo: {motivo}\n\n"
            "=== HISTÓRICO DOS ÚLTIMOS CICLOS ===\n"
            f"{self._formatar_historico()}\n\n"
            "=== PERGUNTA DO OPERADOR ===\n"
            f"{pergunta}\n\n"
            "Responda de forma clara e objetiva. "
            "Sempre conecte a análise técnica ao impacto terrestre "
            "(desmatamento, incêndios, áreas protegidas). "
            "Se a situação for crítica, indique ações imediatas recomendadas."
        )

    def _formatar_dados(self, dados: dict) -> str:
        return "\n".join(f"  • {chave}: {valor}" for chave, valor in dados.items())

    def _formatar_historico(self) -> str:
        if not self.historico:
            return "  Nenhum ciclo anterior registrado nesta sessão."

        linhas = []
        total = len(self.historico)
        for i, ciclo in enumerate(self.historico):
            indice = i - total  # -4, -3, -2, -1, 0 (ciclo atual)
            rotulo = "atual" if i == total - 1 else f"{indice}"
            linhas.append(f"  [Ciclo {rotulo} | {ciclo['timestamp']}]")
            for chave, valor in ciclo["dados"].items():
                linhas.append(f"    {chave}: {valor}")
            if ciclo["alertas"]:
                linhas.append(f"    Alertas: {', '.join(ciclo['alertas'])}")
            else:
                linhas.append("    Alertas: nenhum")

        return "\n".join(linhas)

    def _montar_painel(self, dados: dict, alertas: list, severidade: dict) -> str:
        nivel = severidade.get("severidade", "DESCONHECIDO")
        emoji_nivel = {"NORMAL": "🟢", "ATENÇÃO": "🟡", "CRÍTICO": "🔴"}.get(nivel, "⚪")
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        linhas = [
            "=" * 52,
            "   🛰️   EnviroSat — PAINEL DE STATUS DA MISSÃO",
            f"   🕐   {agora}",
            "=" * 52,
            "",
            "📡 TELEMETRIA ATUAL:",
            self._formatar_dados(dados),
            "",
            f"⚠️  ALERTAS ATIVOS: {len(alertas)}",
        ]

        if alertas:
            for alerta in alertas:
                linhas.append(f"  ❗ {alerta}")
        else:
            linhas.append("  ✅ Nenhum alerta no momento.")

        linhas += [
            "",
            f"{emoji_nivel} SEVERIDADE: {nivel}",
            f"   {severidade.get('motivo', '')}",
            "",
            "=" * 52,
        ]

        return "\n".join(linhas)
