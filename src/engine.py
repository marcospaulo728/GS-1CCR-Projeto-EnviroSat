import os
import json
from ollama import Client
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

load_dotenv()

# Identificação da trilha
TRILHA = "envirosat"

client = Client(
    host="https://ollama.com",
    headers={"Authorization": "Bearer " + os.environ.get("OLLAMA_API_KEY", "")}
)


def llm(prompt, system=None, max_tokens=800, temperature=0.3):
    """Envia prompt ao gpt-oss:120b via Ollama Cloud.

    Parâmetros:
        prompt       -- texto principal enviado ao modelo
        system       -- system prompt (opcional); carregado do .md por padrão
        max_tokens   -- limite de tokens na resposta
        temperature  -- criatividade do modelo (0 = determinístico)

    Retorna:
        String com a resposta do modelo ou mensagem de erro.
    """
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
    """Lê o system prompt do arquivo prompts/system_prompt.md.

    Fallback genérico caso o arquivo não exista — não deve acontecer
    em produção, mas evita crash durante o desenvolvimento.
    """
    path = Path(__file__).parent.parent / "prompt" / "system_prompt.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    # Fallback mínimo — substitua pelo seu system_prompt.md real
    return (
        "Você é ARIA (Ambiental Remote Intelligence Assistant), "
        "analista de operações do satélite EnviroSat. "
        "Sempre conecte a análise técnica com o impacto terrestre: "
        "desmatamento, incêndios e monitoramento de áreas protegidas."
    )


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------

class MissionEngine:
    """Motor de análise EnviroSat.

    Combina telemetria simulada + lógica de alertas em Python +
    IA generativa via Ollama Cloud para produzir análises contextualizadas.

    Diferenciais implementados:
        - Múltiplas chamadas LLM: primeira classifica a severidade em JSON
          estruturado; segunda gera a análise completa em linguagem natural.
        - Memória de contexto: mantém histórico dos últimos N ciclos e injeta
          no prompt, simulando consciência temporal da missão.
    """

    MAX_HISTORICO = 5  # Número de ciclos mantidos na memória

    def __init__(self):
        self.trilha = TRILHA
        self.system_prompt = load_system_prompt()
        self.historico: list[dict] = []  # Memória de contexto

    # ------------------------------------------------------------------
    # Interface pública exigida pela src/ui.py
    # ------------------------------------------------------------------

    def is_ready(self) -> bool:
        """Sinaliza para a UI que o motor está implementado."""
        return True

    def status_snapshot(self) -> str:
        """Retorna um painel de texto com o estado atual da telemetria.

        Chamado pelo comando /status na CLI.
        """
        dados, alertas = self._coletar()
        self._registrar_ciclo(dados, alertas)
        severidade = self._classificar_severidade(dados, alertas)
        return self._montar_painel(dados, alertas, severidade)

    def analyze(self, pergunta_usuario: str) -> str:
        """Analisa a pergunta com base na telemetria + alertas + IA.

        Fluxo:
            1. Coleta telemetria       → src/telemetria.py
            2. Avalia alertas          → src/alertas.py
            3. Registra ciclo          → memória de contexto
            4. 1ª chamada LLM          → classifica severidade (JSON)
            5. 2ª chamada LLM          → análise completa em linguagem natural
            6. Retorna resposta final
        """
        dados, alertas = self._coletar()
        self._registrar_ciclo(dados, alertas)

        # --- 1ª chamada LLM: classificação de severidade (saída estruturada) ---
        severidade = self._classificar_severidade(dados, alertas)
        nivel = severidade.get("severidade", "NORMAL")
        motivo = severidade.get("motivo", "")

        # --- 2ª chamada LLM: análise completa ---
        prompt = self._montar_prompt_analise(
            dados, alertas, nivel, motivo, pergunta_usuario
        )
        return llm(prompt, system=self.system_prompt, max_tokens=800, temperature=0.3)

    # ------------------------------------------------------------------
    # Métodos internos — coleta e formatação
    # ------------------------------------------------------------------

    def _coletar(self) -> tuple[dict, list[str]]:
        """Importa e executa telemetria + alertas.

        Retorna:
            (dados, alertas) onde dados é dict e alertas é list[str].
        """
        try:
            from src.telemetria import coletar
            from src.alertas import avaliar
        except ImportError as e:
            # Dados de fallback para não travar a interface durante dev
            dados_fallback = {
                "sensor_termico_celsius": 38.5,
                "sensor_optico_status": "OPERACIONAL",
                "buffer_imagens_nao_transmitidas": 12,
                "precisao_geolocalizacao_metros": 15.3,
                "energia_disponivel_pct": 72.0,
            }
            return dados_fallback, [f"⚠️  Módulo não encontrado: {e}"]

        dados = coletar()
        alertas = avaliar(dados)
        return dados, alertas

    def _registrar_ciclo(self, dados: dict, alertas: list[str]) -> None:
        """Adiciona o ciclo atual ao histórico e descarta os mais antigos."""
        ciclo = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "dados": dict(dados),
            "alertas": list(alertas),
        }
        self.historico.append(ciclo)
        if len(self.historico) > self.MAX_HISTORICO:
            self.historico.pop(0)

    # ------------------------------------------------------------------
    # Métodos internos — chamadas LLM
    # ------------------------------------------------------------------

    def _classificar_severidade(self, dados: dict, alertas: list[str]) -> dict:
        """1ª chamada LLM: classifica a severidade e retorna JSON estruturado.

        Força a IA a responder apenas com JSON para parse seguro no Python.
        Fallback automático se o JSON não for parseável.
        """
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
            # Remove marcadores markdown que o modelo eventualmente inclui
            resposta_limpa = (
                resposta.strip()
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )
            return json.loads(resposta_limpa)
        except (json.JSONDecodeError, ValueError):
            # Fallback determinístico baseado em alertas
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
        """Monta o prompt completo injetando telemetria + alertas + histórico."""

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

    # ------------------------------------------------------------------
    # Métodos internos — formatação de texto
    # ------------------------------------------------------------------

    def _formatar_dados(self, dados: dict) -> str:
        """Converte o dicionário de telemetria em texto legível."""
        return "\n".join(f"  • {chave}: {valor}" for chave, valor in dados.items())

    def _formatar_historico(self) -> str:
        """Formata o histórico de ciclos para injeção no prompt."""
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
        """Monta o painel de texto exibido pelo comando /status."""
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
