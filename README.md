# dieHoward — Pipeline TTS Local para Audiobooks

<div align="center">

  ![Logo Text](icons/logo.png)

</div>

---

## 1. Sobre

**dieHoward** é o nome do núcleo de processamento de texto/áudio baseado em IA desenvolvido para transformar livros e textos extensos em uma experiência de áudio confortável e natural, funcionando como um sistema local de conversão de texto em fala (TTS). O objetivo principal é evitar a dependência de APIs pagas ou serviços em nuvem, utilizando **modelos locais e software open source** desenhados especificamente para lidar com o processamento pesado de textos longos.

### Origem do Nome

O nome nasceu como uma homenagem a um monólogo do filme *Pearl* (2022), no qual a atriz Mia Goth interpreta magistralmente uma conversa dissecante com seu marido, Howard, por mais de oito minutos.

> *"Howard... Eu te odeio tanto por ter me deixado aqui. Às vezes eu espero que você morra. Me desculpa. É horrível admitir isso, mas é a verdade"* — [Trecho do Monólogo](https://youtu.be/kj8UiWw2lxg)

Este texto serviu de *benchmark* (base de testes) para rastrear a evolução do projeto. Ele expôs os desafios mais difíceis da síntese de voz: o ritmo, a entonação emotiva e a pronúncia de palavras estrangeiras como "Howard". Tal qual a Pearl espera que Howard morra, espera-se que o problema da pronúncia robótica também morra — por isso, **dieHoward**.

---

## 2. Destaques (v1.0.0)

* **100% Local e Privado:** Nenhuma dependência de APIs externas ou envio de textos para a nuvem.
* **Múltiplos Formatos de Entrada:** Suporte nativo para arquivos `.txt`, `.pdf` e `.epub`.
* **Exportação Flexível:** Gere o livro completo em um único arquivo `.wav` ou dividido automaticamente em uma pasta com um áudio por capítulo.
* **Aceleração de Hardware Inteligente:** Detecção automática de GPU NVIDIA (CUDA) com fallback transparente para CPU via `onnxruntime`.
* **Arquitetura Dual-Engine:**
  * **Kokoro-82M:** Alta expressividade e naturalidade com múltiplas vozes em PT-BR (`pf_dora`, `pm_alex`, `pm_santa`).
  * **Piper TTS:** Modelo leve (`pt_BR-faber-medium`) aliado à normalização fonética e dicionário léxico.
* **Controle de Velocidade e Configurações Persistentes:** Presets prontos (`0.75x` a `1.30x`), ajuste personalizado (`0.50x` a `2.00x`) e escolha de diretórios padrão salvos localmente.
* **Instalação Plug & Play:** Script instalador que cria o ambiente virtual, baixa os modelos necessários automaticamente e registra o atalho gráfico no menu de aplicativos do Linux.

---

## 3. Instalação e Uso (Linux)

### Instalação Automatizada

```bash
git clone [https://github.com/SEU-USUARIO/die-howard.git](https://github.com/SEU-USUARIO/die-howard.git)
cd die-howard
chmod +x install.sh
./install.sh