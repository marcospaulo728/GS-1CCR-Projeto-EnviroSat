# 🌳 Mission Control AI — EnviroSat

Sistema de monitoramento operacional do satélite **EnviroSat-1**, que combina telemetria simulada, lógica de alertas em Python e **IA generativa via Ollama Cloud** para análise contextualizada em linguagem natural. A IA é operada pela persona **ARIA** *(Ambiental Remote Intelligence Assistant)*, analista de missão especializada em conectar dados orbitais ao impacto terrestre: desmatamento, incêndios florestais e monitoramento de áreas protegidas.

---

## 👤 Integrantes

| Nome | RM | Turma |
|------|----|-------|
| Gabriela Angel Silva | *570808* | 1CCR |
| Izabelly Menezes | *570673* | 1CCR |
| Marcos Sampaio | *573987* | 1CCR |

**Modalidade:** Trio

---

## 🛰️ O que o projeto faz

O EnviroSat Mission Control AI recebe dados simulados de seis parâmetros de telemetria do satélite ambiental EnviroSat-1 e os processa em três camadas:

1. **Camada Python** — lógica de thresholds e respostas automáticas em `src/alertas.py`, sem depender da IA para decisões binárias.
2. **1ª chamada LLM** — classificação de severidade da missão com saída em JSON estruturado, parseada no código.
3. **2ª chamada LLM** — análise completa em linguagem natural com injeção dinâmica de telemetria, alertas, severidade e histórico dos últimos ciclos (memória de contexto).

A interface é uma CLI estilo Claude Code com banner ASCII, painéis renderizados via Rich e prompt editável via prompt-toolkit.

---

## 🎯 Persona atendida

**Operador de centro de controle ambiental** — perfil equivalente ao de analistas do INPE ou órgãos estaduais de monitoramento. O sistema foi desenhado para que o operador consiga, em linguagem natural, perguntar sobre o estado da missão e receber tanto o diagnóstico técnico quanto a tradução do impacto terrestre: quais áreas podem deixar de ser monitoradas, quais brigadas podem perder dados de focos de calor, quais alertas de desmatamento podem ser atrasados.

---

## 📡 Parâmetros monitorados

| Parâmetro | Normal | Atenção | Crítico |
|-----------|--------|---------|---------|
| `energia_solar` | > 50% | 20–50% | < 20% |
| `bateria` | > 50% | 30–50% | < 30% |
| `comunicacao` | ONLINE | — | OFFLINE |
| `sensor_termico` | OPERACIONAL | — | FALHA |
| `precisao_geolocalizacao` | > 80% | — | < 80% |
| `temperatura` | ≤ 60°C | 61–70°C | > 70°C |

---

## ⚠️ Lógica de alertas e respostas automáticas

Todos os alertas e ações automáticas são definidos em **código Python puro** (`src/alertas.py`), antes de qualquer chamada à IA:

**Alertas gerados automaticamente:**
- `energia_solar < 20` → Energia insuficiente para transmissão das imagens ambientais
- `bateria < 30` → Bateria crítica
- `comunicacao == OFFLINE` → Falha de comunicação com risco de perda do monitoramento de queimadas
- `sensor_termico == FALHA` → Sensor térmico indisponível
- `precisao_geolocalizacao < 80` → Baixa precisão de geolocalização

**Respostas automáticas para crises:**
- `bateria < 20` → Ativar modo de economia de energia
- `energia_solar < 15` → Suspender sensores secundários
- `comunicacao == OFFLINE` → Priorizar transmissão de alertas ambientais
- `sensor_termico == FALHA` → Utilizar imagens ópticas como redundância
- `precisao_geolocalizacao < 80` → Solicitar recalibração orbital

---

## 🤖 Integração com IA generativa

**Modelo:** `gpt-oss:120b` via Ollama Cloud  
**Ponto de integração:** função `llm()` em `src/engine.py`  
**Persona da IA:** ARIA — analista ambiental do EnviroSat

### Diferenciais implementados

**Múltiplas chamadas LLM encadeadas:**
- A primeira chamada força o modelo a responder em JSON (`{"severidade": ..., "motivo": ...}`), que é parseado no Python para compor o prompt da segunda chamada.
- A segunda chamada gera a análise completa em linguagem natural, com telemetria, alertas, severidade e histórico injetados dinamicamente.

**Memória de contexto:**
- O `MissionEngine` mantém os últimos 5 ciclos de telemetria na memória da sessão e os injeta no prompt, permitindo que a IA perceba tendências (ex: bateria caindo progressivamente entre os ciclos).

**Saída estruturada:**
- A classificação de severidade usa JSON estruturado com fallback determinístico (baseado na contagem de alertas) caso o modelo retorne resposta malformada.

---

## 🖥️ Tecnologias utilizadas

- Python 3.10+
- [Ollama Cloud API](https://ollama.com) — modelo `gpt-oss:120b`
- `ollama==0.5.1` — cliente Python para Ollama Cloud
- `python-dotenv==1.1.0` — carregamento seguro de credenciais
- `rich==14.0.0` — painéis e formatação no terminal
- `prompt-toolkit` — input editável com histórico
- `pyfiglet` — banner ASCII

---

## 🗂️ Estrutura do projeto

```
GS-1CCR-Projeto-EnviroSat/
│
├── README.md
├── main.py                  # Ponto de entrada — instancia engine e inicia CLI
├── banner_ascii.py          # Gerador standalone do banner ASCII
├── requirements.txt         # Dependências com versões fixadas
├── .env.example             # Template de variáveis de ambiente
├── .gitignore               # Ignora .env, __pycache__, .venv
│
├── src/
│   ├── __init__.py
│   ├── ui.py                # CLI estilo Claude Code (Rich + prompt-toolkit)
│   ├── engine.py            # Motor de análise — telemetria + alertas + IA
│   ├── alertas.py           # Thresholds, geração de alertas e respostas automáticas
│   └── telemetria.py        # Geração dos dados simulados do satélite
│
└── prompt/
    └── system_prompt.md     # System prompt da IA (persona ARIA)
```

---

## ▶️ Como executar

### Pré-requisitos

- Python 3.10 ou superior
- Conta gratuita no [Ollama Cloud](https://ollama.com) com API Key gerada

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/marcospaulo728/GS-1CCR-Projeto-EnviroSat.git
cd GS-1CCR-Projeto-EnviroSat

# 2. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as credenciais
cp .env.example .env
# Edite o arquivo .env e insira sua chave Ollama:
# OLLAMA_API_KEY=sua_chave_aqui

# 5. Execute
python main.py
```

### Comandos disponíveis na CLI

| Comando | Descrição |
|---------|-----------|
| *(qualquer pergunta)* | Analisa a missão com base na telemetria atual |
| `/status` | Exibe painel completo de telemetria e severidade |
| `/help` | Lista os comandos disponíveis |
| `/clear` | Limpa o terminal e reexibe o banner |
| `/exit` | Encerra o sistema |

---

## 🧪 Cenários de teste demonstrados

1. **Operação normal** — todos os parâmetros dentro dos ranges, IA confirma continuidade da missão e monitoramento ativo de áreas florestais.
2. **Bateria crítica** — `bateria < 30%` dispara alerta e resposta automática de economia de energia; IA explica risco de interrupção de downlink de imagens.
3. **Sensor térmico em falha** — `sensor_termico == FALHA` gera alerta de indisponibilidade de detecção de focos de calor; IA recomenda uso de imagens ópticas como redundância e alerta sobre impacto para brigadas.
4. **Comunicação OFFLINE** — IA conecta a perda de sinal à impossibilidade de enviar alertas de queimadas em tempo real para o IBAMA e órgãos estaduais.
5. **Múltiplos alertas simultâneos** — memória de contexto mostra degradação progressiva entre ciclos; IA classifica como CRÍTICO e detalha impacto acumulado.

---

## 💼 Proposta de valor / modelo de negócio

**1. Problema real terrestre que esta missão resolve**

O Brasil perde anualmente milhões de hectares de vegetação nativa para desmatamento e incêndios. A resposta tardia das brigadas ambientais ocorre, em grande parte, pela demora na interpretação dos dados de telemetria orbital — dados que chegam brutos e exigem especialistas para transformá-los em decisões. O EnviroSat Mission Control AI resolve exatamente esse gap: transforma telemetria crua em diagnóstico operacional em linguagem natural, disponível a qualquer operador, não apenas a engenheiros espaciais.

**2. Quem paga pela solução**

Modelo híbrido: o núcleo do sistema é contratado pelo **setor público** (INPE, IBAMA, secretarias estaduais de meio ambiente) via contrato de serviço gerenciado. Uma camada de dados derivados — alertas de focos processados, relatórios de cobertura florestal — pode ser comercializada como **dado-como-serviço** para seguradoras rurais, empresas de certificação ambiental e cooperativas agrícolas que precisam comprovar compliance.

**3. Métrica de impacto**

Se o EnviroSat-1 operar com disponibilidade de 99% por 12 meses, estima-se o monitoramento contínuo de aproximadamente **50 milhões de hectares** de área florestal no bioma Amazônia e Cerrado, com geração de alertas de focos de calor em janelas de até 6 horas — reduzindo em até 30% o tempo de mobilização de brigadas em relação ao modelo atual de análise manual.

**4. Modelo de negócio**

**SaaS + Dado-como-serviço:** o centro de controle paga uma assinatura mensal pelo acesso à plataforma de análise operacional (SaaS). Relatórios periódicos e feeds de alertas processados são comercializados separadamente para clientes privados do agronegócio e do mercado de carbono.

---

## ⚠️ Limitações conhecidas

- `telemetria.py` gera dados aleatórios — não há séries temporais realistas baseadas em órbita real.
- O sistema não persiste histórico entre sessões; a memória de contexto é reiniciada a cada execução de `python main.py`.
- A classificação de severidade por JSON depende da consistência do modelo; o fallback determinístico é conservador (conta alertas) e pode classificar como CRÍTICO cenários que seriam apenas ATENÇÃO.
- O `system_prompt.md` não é versionado neste repositório por questões de iteração — o fallback em `engine.py` garante funcionamento mesmo sem o arquivo.
- Não há autenticação ou controle de acesso na CLI — adequado apenas para uso em ambiente de desenvolvimento/demo.

---

## 🎬 Vídeo de demonstração

🔗 *(link do YouTube)*

---

*FIAP · Ciência da Computação · Global Solution 2026.1 · Prompt Engineering and Artificial Intelligence*
