import random

def coletar():
    return {
        "temperatura": random.randint(-20, 90),
        "energia_solar": random.randint(0, 100),
        "bateria": random.randint(0, 100),
        "comunicacao": random.choice([
            "ONLINE",
            "OFFLINE"
        ]),
        "sensor_termico": random.choice([
            "OPERACIONAL",
             "FALHA"
        ]),
        "precisao_geolocalizacao": random.randint(70, 100)
    }