"""Interface CLI estilo Claude Code — usa Rich + prompt-toolkit."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
import pyfiglet
from datetime import datetime

# --- Instâncias globais usadas em todas as funções ---
console = Console()
session = PromptSession(style=Style.from_dict({"prompt": "#06B6D4 bold"}))


def show_banner():
    """Exibe banner ASCII colorido no início."""
    banner = pyfiglet.figlet_format("Mission Control", font="ansi_shadow")
    console.print(Text(banner, style="bold #06B6D4"))
    console.print(Panel.fit(
        "🌳 EnviroSat — Monitoramento Ambiental por IA Generativa\n"
        "Use /help para ver os comandos · /exit para sair.\n"
        "Modelo: gpt-oss:120b via Ollama Cloud",
        title="◆ MISSION CONTROL",
        border_style="#06B6D4"
    ))


def show_response(text):
    """Renderiza resposta da IA em painel com timestamp."""
    now = datetime.now().strftime("%H:%M")
    console.print(Panel(
        text,
        title="◆ Mission Control",
        subtitle=now,
        border_style="#06B6D4"
    ))


def run_cli(engine):
    """Loop principal da CLI."""
    show_banner()

    if not engine.is_ready():
        console.print(
            " ⚠ Engine status: AGUARDANDO IMPLEMENTAÇÃO ✗\n",
            style="yellow"
        )

    while True:
        try:
            user_input = session.prompt("❯ ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        if user_input == "/exit":
            break

        if user_input == "/help":
            console.print("Comandos: /help /status /clear /exit")
            continue

        if user_input == "/status":
            show_response(engine.status_snapshot())
            continue

        if user_input == "/clear":
            console.clear()
            show_banner()
            continue

        resposta = engine.analyze(user_input)
        show_response(resposta)