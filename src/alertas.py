def avaliar(dados):

    alertas = []

    if dados["energia_solar"] < 20:
        alertas.append(
            "Energia insuficiente para transmissão das imagens ambientais."
        )

    if dados["bateria"] < 30:
        alertas.append(
            "Bateria crítica"
        )

    if dados["comunicacao"] == "OFFLINE":
        alertas.append(
            "Falha de comunicação com risco de perda do monitoramento de queimadas."
        )

    if dados["sensor_termico"] == "FALHA":
        alertas.append(
            "Sensor térmico indisponível."
        )

    if dados["precisao_geolocalizacao"] < 80:
        alertas.append(
            "Baixa precisão de geolocalização."
        )

    return alertas

def resposta_automatica(dados):

    acoes = []

    if dados["bateria"] < 20:
        acoes.append(
            "Ativar modo de economia de energia"
        )

    if dados["energia_solar"] < 15:
        acoes.append(
            "Suspender sensores secundários"
        )

    if dados["comunicacao"] == "OFFLINE":
        acoes.append(
            "Priorizar transmissão de alertas ambientais"
        )

    if dados["sensor_termico"] == "FALHA":
        acoes.append(
            "Utilizar imagens ópticas como redundância"
        )

    if dados["precisao_geolocalizacao"] < 80:
        acoes.append(
            "Solicitar recalibração orbital"
        )

    return acoes