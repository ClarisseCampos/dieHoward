# dieHoward — Pipeline TTS Local para Audiobooks

<div align="center">

  ![Logo Text](icons/logo.png)

</div>

---

## 1. Sobre

**dieHoward** é o nome do núcleo de processamento de texto/áudio baseado em IA que estou desenvolvendo.

A ideia do projeto é transformar livros e textos extensos em uma experiência de áudio confortável e natural, funcionando como um sistema local de conversão de texto em fala (TTS). O objetivo principal é evitar a dependência de APIs pagas ou serviços em nuvem. Utilizo **modelos locais e software open source**, desenhados especificamente para lidar com o processamento pesado de textos longos.

### Origem do Nome

O nome nasceu como uma homenagem a um monólogo do filme *Pearl* (2022), no qual a atriz Mia Goth interpreta magistralmente uma conversa dissecante com seu marido, Howard, por mais de oito minutos.

> *"Howard... Eu te odeio tanto por ter me deixado aqui. Às vezes eu espero que você morra. Me desculpa. É horrível admitir isso, mas é a verdade"* — [Trecho do Monólogo](https://youtu.be/kj8UiWw2lxg)

Este texto serviu de *benchmark* (base de testes) para rastrear a evolução do projeto. Ele expôs os desafios mais difíceis da síntese de voz: o ritmo, a entonação emotiva e a pronúncia de palavras estrangeiras como "Howard". Tal qual a Pearl espera que Howard morra, eu espero que o problema da pronúncia robótica também morra — por isso, **dieHoward**.

---

## 2. Destaques (v1.0.0)

* **100% Local e Privado:** Nenhuma dependência de APIs externas ou conexão com a nuvem.
* **Múltiplos Formatos de Entrada:** Suporte nativo para leitura e extração de arquivos `.txt`, `.pdf` e `.epub`.
* **Exportação Flexível:** Gere o livro completo em um único arquivo `.wav` ou dividido automaticamente em uma pasta com um áudio por capítulo.
* **Aceleração de Hardware Inteligente:** Detecção automática de GPU NVIDIA (CUDA) com fallback transparente para CPU via `onnxruntime`.
* **Arquitetura Dual-Engine:**
  * **Kokoro-82M:** Alta expressividade e naturalidade com múltiplas vozes em PT-BR (`pf_dora`, `pm_alex`, `pm_santa`).
  * **Piper TTS:** Processamento leve (`pt_BR-faber-medium`) aliado à normalização de texto, suporte a regras IPA e dicionário léxico.
* **Controle de Velocidade e Configurações Persistentes:** Presets prontos (`0.75x` a `1.30x`), ajuste fino personalizado (`0.50x` a `2.00x`) e escolha de diretórios padrão salvos localmente.
* **Instalação Plug & Play:** Script instalador que configura o ambiente virtual, baixa os modelos necessários automaticamente e cria o atalho gráfico no menu de aplicativos do Linux.

---

## 3. Instalação e Uso (Linux)

### Opção 1: Instalação Direta (Não requer `git`)

```bash
curl -fL [https://github.com/ClarisseCampos/dieHoward/archive/refs/heads/main.tar.gz](https://github.com/ClarisseCampos/dieHoward/archive/refs/heads/main.tar.gz) -o dieHoward.tar.gz
tar -xzf dieHoward.tar.gz
cd dieHoward-main
chmod +x install.sh
./install.sh

### Instalação Automatizada

```bash
git clone https://github.com/ClarisseCampos/die-howard.git
cd die-howard
chmod +x install.sh
./install.sh
```

O script `install.sh` realiza todo o preparo automaticamente:
1. Cria o ambiente virtual Python (`.venv`) e instala as dependências do `requirements.txt`.
2. Baixa os modelos oficiais do **Kokoro-82M** e do **Piper TTS** para a pasta `models/`.
3. Gera o atalho **DieHoward TTS** (com ícone personalizado) no menu de aplicativos do sistema.

### Execução

* Abra **DieHoward TTS** diretamente pelo menu iniciar do seu ambiente gráfico, ou execute pelo terminal:
  ```bash
  ./diehoward.sh
  ```
* Coloque seus livros (`.txt`, `.pdf` ou `.epub`) em `data/input/` (ou configure suas pastas preferidas no menu **Configurações** da interface).
* Os audiobooks gerados serão salvos em `data/output/`.

---

## 4. Ambiente de Desenvolvimento e Premissa de Engenharia

* **SO:** Linux Mint
* **CPU:** AMD Ryzen 5 3400G
* **GPU Integrada:** Radeon Vega Graphics

**Premissa de Engenharia:** Não se deve presumir a existência de uma GPU moderna com grande quantidade de VRAM. Toda solução implementada deve levar em conta o custo computacional e rodar satisfatoriamente em configurações modestas, aproveitando aceleração NVIDIA (CUDA) automaticamente apenas quando disponível no sistema.

---

## 5. Árvore do Projeto

```text
die-howard/
├── app.py                     # Ponto de entrada da interface de terminal (TUI)
├── install.sh                 # Instalador automatizado e criador de atalho .desktop
├── diehoward.sh               # Lançador portável do ambiente virtual
├── requirements.txt           # Dependências do ambiente Python
├── icons/                     # Logotipo oficial da aplicação
│   └── logo.png
├── common/                    # Núcleo compartilhado e lógica de negócio
│   ├── pipeline.py            # Orquestração central (extração, normalização e síntese)
│   ├── settings.py            # Gerenciamento persistente de configurações e caminhos
│   ├── parser.py              # Extração de texto e capítulos (TXT, PDF, EPUB)
│   ├── normalizer.py          # Normalizador textual e léxico fonético
│   ├── model_downloader.py    # Download automático dos modelos ONNX/BIN
│   ├── tui.py                 # Interface gráfica de terminal (Rich)
│   └── config/                # Dicionários de substituição e regras IPA
│       ├── ipa_rules.json
│       └── lexicon.json
├── engines/                   # Motores de síntese isolados
│   ├── kokoro/
│   │   └── kokoro_engine.py   # Wrapper ONNX do Kokoro-82M (CUDA/CPU)
│   └── piper/
│       └── piper_engine.py    # Wrapper do Piper TTS
├── models/                    # Modelos baixados localmente (ignorados pelo Git)
│   ├── kokoro/                # kokoro-v1.0.onnx e voices-v1.0.bin
│   └── piper/                 # pt_BR-faber-medium.onnx e .json
├── data/                      # Estrutura centralizada de I/O (ignorada pelo Git)
│   ├── input/                 # Coloque seus livros (.txt, .pdf, .epub) aqui
│   ├── output/                # Áudios .wav gerados pelo pipeline
│   └── temp/                  # Arquivos intermediários e cache
└── .gitignore                 # Filtros para Git
```

---

## 6. Problemas Mapeados e Engenharia Acústico-Fonética

### Problemas Mapeados na Síntese Neural

1. **Ritmo Linear:** O motor percorre as palavras em sequência, ignorando a dinâmica de pausas reais e ênfases de diálogo.
2. **Estrangeirismos:** Nomes em inglês (como *Howard*) quebram o conversor grafêmico do modelo em português.
3. **Anomalias Fonéticas (O Backend espeak-ng):** A conversão de certos dígrafos e sons nasais no Piper pt-BR gera áudios robóticos, soletração de caracteres (fallback) ou oclusões abafadas.

### Transliteração Ortográfica Guiada

Para resolver as falhas fonéticas do modelo `pt_BR-faber-medium` sem ter que treinar a rede neural do zero, o dieHoward implementa um sistema de **Transliteração Ortográfica Guiada (Guided Orthographic Transliteration)**.

Como o motor G2P (*Grafo-Fonêmico*) nativo do Piper é baseado no `espeak-ng` — que rejeita símbolos fonéticos IPA complexos para o português —, nós manipulamos a rede acústica deformando a grafia das palavras antes que elas cheguem ao sintetizador.

#### 6.1. Resolução de Dígrafos Palatais (O Hack do Hífen e Dupla Consoante)

O motor falhava catastroficamente ao processar dígrafos como "LH" e "NH", travando a articulação.

* **A Solução:** Substituição por fronteiras prosódicas e transições líquidas. Palavras como *olhos* são convertidas para `ó-llios`.
* **Ciência por trás:** O hífen atua como um separador prosódico (*prosodic boundary*), forçando a rede neural a sustentar o ataque da vogal "Ó". A dupla consoante `ll` sinaliza uma transição contínua ao motor, impedindo que ele feche o trato vocal e eliminando o som anasalado ou robótico.

#### 6.2. Controle de Oclusão Labial e Ressonância

* **O Problema do "M" Final:** Palavras como *mim* e *com* soavam abafadas porque o "M" no final da palavra obriga o modelo acústico a simular uma oclusão bilabial (fechar os lábios totalmente).
* **A Solução Alveolar (`mín`, `cõn`):** Ao trocar pelo "N", a articulação passa para o alvéolo (a língua toca o céu da boca). Isso interrompe o fluxo de ar de forma abrupta e limpa, devolvendo a naturalidade da fala brasileira.

#### 6.3. Manipulação de Timbre via Diacríticos

Para evitar o "Nasal Bleeding" (quando a IA espalha o som nasal para vogais adjacentes, lendo "boa" como "bõa"), criamos uma matriz matemática de acentuação:

* **Acento Agudo (`´`):** Força a abertura máxima da cavidade oral (`bóa`, `cóisa`). Garante um timbre claro e projetado.
* **Circunflexo (`^`):** Força o fechamento aveludado da vogal tônica em dígrafos (`es-pê-llio`, `es-cô-llia`), prevenindo estalos metálicos na transição.
* **Til (`~`):** Usado estritamente para demarcar passagem obrigatória de ar pela cavidade nasal (`quãn-do`, `Hũm`).

#### 6.4. Modelagem de Prosódia Emocional

Textos literários exigem suspiros, risadas e interjeições (fricativas glotais) que motores TTS não sabem ler naturalmente.

* **Sustentação de Vogal (`Ôuh`, `Áah`):** Modifica o *duration model* da IA. O "H" final força o áudio a esticar a sílaba, simulando um lamento melancólico.
* **Risadas e Sopros Acústicos (`Ra-rá-ra`, `Rí-ri-ri`):** O "R" inicial aciona a fricativa glotal do modelo (som de ar raspando), enquanto a hifenização impede que a voz emende tudo de forma mecânica.

---

## 7. Arquitetura e Direção Futura

O objetivo a longo prazo é evoluir de uma execução linear para uma arquitetura modular inteligente em múltiplas camadas de processamento.

### Evolução do Pipeline

**Atual (v1.0.0):**

```text
Livro (TXT/PDF/EPUB) → Parser (Capítulos) → Normalização → Pipeline (Kokoro/Piper) → Áudio WAV
```

**Direção Futura:**

```text
              ┌──────────────┐
              │    Livro     │
              └──────┬───────┘
                     ↓
             ┌───────────────┐
             │    Parser     │
             └───────┬───────┘
                     ↓
        ┌─────────────────────────┐
        │ Análise / Normalização  │ (lexicon.json, ipa_rules.json)
        └────────────┬────────────┘
                     ↓
          ┌─────────────────────┐
          │ Segmentação textual │
          └──────────┬──────────┘
                     ↓
        ┌────────────────────────┐
        │ Preparação para TTS    │ (Controle de Ritmo Dinâmico)
        └────────────┬───────────┘
                     ↓
              ┌───────────┐
              │    TTS    │
              └─────┬─────┘
                    ↓
          ┌──────────────────┐
          │ Pós-processamento│
          └────────┬─────────┘
                   ↓
             ┌───────────┐
             │   Áudio   │
             └───────────┘
```

### Roadmap de Funcionalidades

* [x] Identificar o hardware do usuário para configurações ideais (detecção dinâmica de GPU CUDA com fallback para CPU).
* [x] Separação automática de audiobooks por capítulos (`.pdf` e `.epub`).
* [x] Controle de velocidade de reprodução e configurações persistentes.
* [x] Instalador portável e download automático dos modelos na primeira execução.
* [ ] Detecção automática de idioma e dicionário de pronúncias estrangeiras.
* [ ] Múltiplas vozes e detecção dinâmica de diálogos (vozes diferentes para personagens).
* [ ] Controle automático de velocidade com inserção matemática de pausas baseada na pontuação.
* [ ] Geração de metadados e capítulos embutidos (exportação em `.m4b`).
* [ ] Processamento inteligente de silêncio (remoção de estalos).
* [ ] Retomada segura de processamento (*resume*) caso o programa seja interrompido durante textos longos.