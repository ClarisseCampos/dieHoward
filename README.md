# dieHoward — Pipeline TTS Local para Audiobooks
![Logo Text](icons/logo.png)

## 1. Sobre

**dieHoward** é o nome do núcleo de processamento de texto/áudio baseado em IA que estou desenvolvendo.

A ideia do projeto é transformar livros e textos extensos em uma experiência de áudio confortável e natural, funcionando como um sistema local de conversão de texto em fala (TTS). O objetivo principal é evitar a dependência de APIs pagas ou serviços em nuvem. Utilizo **modelos locais e software open source**, desenhados especificamente para lidar com o processamento pesado de textos longos.

### Origem do Nome

O nome nasceu como uma homenagem a um monólogo do filme *Pearl* (2022), no qual a atriz Mia Goth interpreta magistralmente uma conversa dissecante com seu marido, Howard, por mais de oito minutos.

> *"Howard... Eu te odeio tanto por ter me deixado aqui. Às vezes eu espero que você morra. Me desculpa. É horrível admitir isso, mas é a verdade"* — [Trecho do Monólogo](https://youtu.be/kj8UiWw2lxg)

Este texto serviu de *benchmark* (base de testes) para rastrear a evolução do projeto. Ele expôs os desafios mais difíceis da síntese de voz: o ritmo, a entonação emotiva e a pronúncia de palavras estrangeiras como "Howard". Tal qual a Pearl espera que Howard morra, eu espero que o problema da pronúncia robótica também morra — por isso, **dieHoward**.

---
## Destaques

- **100% Local e Privado**: Nenhuma dependência de APIs externas ou conexão com a nuvem.
- **Otimizado para CPU**: Execução performática via `onnxruntime`.
- **TUI Interativa (Rich)**: Menu visual para seleção de arquivos, motores, vozes e progresso em tempo real com porcentagem.
- **Arquitetura Dual-Engine**:
  - **Kokoro-82M**: Processamento de texto bruto (raw text) com alta expressividade.
  - **Piper TTS**: Processamento com normalização de texto, suporte a regras IPA e dicionário léxico.


### Ambiente de Desenvolvimento

* **SO:** Linux Mint
* **CPU:** AMD Ryzen 5 3400G
* **GPU Integrada:** Radeon Vega Graphics

**Premissa de Engenharia:** Não se deve presumir a existência de uma GPU moderna com grande quantidade de VRAM. Toda solução implementada deve levar em conta o custo computacional e rodar satisfatoriamente em configurações modestas.

---

```text
die-howard/
├── app.py                     # Ponto de entrada único com TUI unificada
├── common/                    # Módulos compartilhados
│   ├── config/                # Dicionários de substituição e regras IPA
│   │   ├── ipa_rules.json
│   │   └── lexicon.json
│   ├── normalizer.py          # Normalizador de texto (utilizado pelo Piper)
│   └── tui.py                 # Interface gráfica de terminal (Rich)
├── engines/                   # Motores de síntese isolados
│   ├── kokoro/
│   │   ├── kokoro_engine.py   # Wrapper ONNX do Kokoro
│   │   └── models/            # kokoro-v1.0.onnx e voices-v1.0.bin
│   └── piper/
│       └── models/            # pt_BR-faber-medium.onnx e .json
├── data/                      # Estrutura centralizada de I/O
│   ├── input/                 # Coloque seus arquivos .txt aqui
│   ├── output/                # Áudios .wav gerados pelo pipeline
│   └── temp/                  # Arquivos intermediários e cache
├── requirements.txt           # Dependências congeladas do ambiente
└── .gitignore                 # Filtros para git
```

### Problemas Mapeados:

1. **Ritmo Linear:** O motor percorre as palavras em sequência, ignorando a dinâmica de pausas reais e ênfases de diálogo.
2. **Estrangeirismos:** Nomes em inglês (como *Howard*) quebram o conversor grafêmico do modelo em português.
3. **Anomalias Fonéticas (O Backend espeak-ng):** A conversão de certos dígrafos e sons nasais no Piper pt-BR gera áudios robóticos, soletração de caracteres (fallback) ou oclusões abafadas.

---

## 4. Engenharia Acústico-Fonética

Para resolver as falhas fonéticas do modelo `pt_BR-faber-medium` sem ter que treinar a rede neural do zero, o DieHoward implementa um sistema de **Transliteração Ortográfica Guiada (Guided Orthographic Transliteration)**.

Como o motor G2P (*Grafo-Fonêmico*) nativo do Piper é baseado no `espeak-ng` — que rejeita símbolos fonéticos IPA complexos para o português —, nós manipulamos a rede acústica deformando a grafia das palavras antes que elas cheguem ao sintetizador.

### 4.1. Resolução de Dígrafos Palatais (O Hack do Hífen e Dupla Consoante)

O motor falhava catastroficamente ao processar dígrafos como "LH" e "NH", travando a articulação.

* **A Solução:** Substituição por fronteiras prosódicas e transições líquidas. Palavras como *olhos* são convertidas para `ó-llios`.
* **Ciência por trás:** O hífen atua como um separador prosódico (*prosodic boundary*), forçando a rede neural a sustentar o ataque da vogal "Ó". A dupla consoante `ll` sinaliza uma transição contínua ao motor, impedindo que ele feche o trato vocal e eliminando o som anasalado ou robótico.

### 4.2. Controle de Oclusão Labial e Ressonância

* **O Problema do "M" Final:** Palavras como *mim* e *com* soavam abafadas porque o "M" no final da palavra obriga o modelo acústico a simular uma oclusão bilabial (fechar os lábios totalmente).
* **A Solução Alveolar (`mín`, `cõn`):** Ao trocar pelo "N", a articulação passa para o alvéolo (a língua toca o céu da boca). Isso interrompe o fluxo de ar de forma abrupta e limpa, devolvendo a naturalidade da fala brasileira.

### 4.3. Manipulação de Timbre via Diacríticos

Para evitar o "Nasal Bleeding" (quando a IA espalha o som nasal para vogais adjacentes, lendo "boa" como "bõa"), criamos uma matriz matemática de acentuação:

* **Acento Agudo (`´`):** Força a abertura máxima da cavidade oral (`bóa`, `cóisa`). Garante um timbre claro e projetado.
* **Circunflexo (`^`):** Força o fechamento aveludado da vogal tônica em dígrafos (`es-pê-llio`, `es-cô-llia`), prevenindo estalos metálicos na transição.
* **Til (`~`):** Usado estritamente para demarcar passagem obrigatória de ar pela cavidade nasal (`quãn-do`, `Hũm`).

### 4.4. Modelagem de Prosódia Emocional

Textos literários exigem suspiros, risadas e interjeições (fricativas glotais) que motores TTS não sabem ler naturalmente.

* **Sustentação de Vogal (`Ôuh`, `Áah`):** Modifica o *duration model* da IA. O "H" final força o áudio a esticar a sílaba, simulando um lamento melancólico.
* **Risadas e Sopros Acústicos (`Ra-rá-ra`, `Rí-ri-ri`):** O "R" inicial aciona a fricativa glotal do modelo (som de ar raspando), enquanto a hifenização impede que a voz emende tudo de forma mecânica.

---

## 5. Arquitetura e Direção Futura

O objetivo a longo prazo é transicionar de um script de execução linear (`Texto -> Piper -> MP3`) para uma arquitetura modular inteligente em múltiplas camadas de processamento.

### Evolução do Pipeline

**De (Atual):**

```text
Livro → Parser → Normalização → TTS → Áudio Final

```

**Para (Futuro):**

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

### Funcionalidades Planejadas no Roadmap:

* Detecção automática de idioma e dicionário de pronúncias estrangeiras.
* Múltiplas vozes e detecção dinâmica de diálogos (vozes diferentes para personagens).
* Controle automático de velocidade com inserção matemática de pausas baseada na pontuação.
* Geração de metadados e capítulos embutidos.
* Processamento inteligente de silêncio (remoção de estalos).
* Retomada segura de processamento (resume) caso o programa seja interrompido durante textos longos.
* Identificar o hardware do usuário para configurações ideais