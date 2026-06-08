from src.engine import MissionEngine
from src.ui import exibir_boas_vindas

def main():
    exibir_boas_vindas()
    engine = MissionEngine()

    while True:
        pergunta = input(
            "\n❯ "
        )
        if pergunta == "/exit":
            break
        if pergunta == "/status":

            print(
                engine.status_snapshot()
            )
            continue

        resposta = engine.analyze(
            pergunta
        )
        print()
        print(resposta)

if __name__ == "__main__":
    main()