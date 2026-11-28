const tauri = window.__TAURI__ ?? criarSimulacao();
const invoke = tauri?.core?.invoke;
const listen = tauri?.event?.listen;

const selectArquivo = document.getElementById("arquivo");
const btnAtualizar = document.getElementById("btn-atualizar");
const btnIniciar = document.getElementById("btn-iniciar");
const statusTexto = document.getElementById("status-texto");
const barra = document.getElementById("barra");
const progressoPct = document.getElementById("progresso-pct");
const logs = document.getElementById("logs");
const velocidade = document.getElementById("velocidade");
const velValor = document.getElementById("vel-valor");

const selModo = document.getElementById("modo");
const modoDica = document.getElementById("modo-dica");
const selEngine = document.getElementById("engine");
const selVoz = document.getElementById("voz");
const vozPiper = document.getElementById("voz-piper");
const livroInfo = document.getElementById("livro-info");
const pastaEntrada = document.getElementById("pasta-entrada");
const pastaSaida = document.getElementById("pasta-saida");
const autoAbrir = document.getElementById("auto-abrir");
const avisoConfig = document.getElementById("aviso-config");
const chips = document.querySelectorAll("#chips-vel button");

let avisoTimer = null;
let ultimoDestinoConcluido = "";

function atualizarProgresso(valor) {
  const pct = Math.max(0, Math.min(100, Number(valor) || 0));
  barra.value = pct;
  if (progressoPct) {
    progressoPct.textContent = `${Math.round(pct)}%`;
  }
}

function mostrarVelocidade() {
  const v = Number(velocidade.value) || 0.85;
  velValor.textContent = `${v.toFixed(2)}×`;
  chips.forEach((chip) => {
    chip.classList.toggle("ativo", Math.abs(Number(chip.dataset.v) - v) < 0.001);
  });
}

velocidade.addEventListener("input", mostrarVelocidade);
velocidade.addEventListener("change", () => {
  mostrarVelocidade();
  salvarConfig();
});

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    velocidade.value = chip.dataset.v;
    mostrarVelocidade();
    salvarConfig();
  });
});

function atualizarMotor() {
  const isPiper = selEngine.value === "piper";
  selVoz.hidden = isPiper;
  vozPiper.hidden = !isPiper;
}

selEngine.addEventListener("change", () => {
  atualizarMotor();
  salvarConfig();
});

selVoz.addEventListener("change", () => salvarConfig());

function atualizarArquivo() {
  const nome = selectArquivo.value || "";
  const ext = nome.includes(".") ? nome.split(".").pop().toLowerCase() : "";
  livroInfo.textContent = ext ? ext.toUpperCase() : "";

  if (ext === "txt") {
    selModo.value = "unico";
    selModo.disabled = true;
    modoDica.textContent = "Arquivos .txt são sempre gerados como arquivo único.";
  } else {
    selModo.disabled = false;
    modoDica.textContent = "";
  }
}

selectArquivo.addEventListener("change", atualizarArquivo);

function avisar(texto, erro = false) {
  avisoConfig.textContent = texto;
  avisoConfig.classList.toggle("erro", Boolean(erro));
  clearTimeout(avisoTimer);
  if (texto) {
    avisoTimer = setTimeout(() => {
      avisoConfig.textContent = "";
      avisoConfig.classList.remove("erro");
    }, 3500);
  }
}

function aplicarConfig(config) {
  if (!config) return;
  if (typeof config.input_dir === "string") pastaEntrada.value = config.input_dir;
  if (typeof config.output_dir === "string") pastaSaida.value = config.output_dir;
  if (typeof config.auto_open === "boolean") autoAbrir.checked = config.auto_open;
  if (config.engine) selEngine.value = config.engine;
  if (config.voz) selVoz.value = config.voz;
  if (config.velocidade !== undefined && config.velocidade !== null) {
    velocidade.value = Number(config.velocidade);
  }
  atualizarMotor();
  mostrarVelocidade();
}

async function carregarConfig() {
  if (!invoke) return;
  try {
    const config = await invoke("obter_configuracoes");
    aplicarConfig(config);
  } catch (err) {
    adicionarLog("Erro ao ler configurações: " + err);
  }
}

async function salvarConfig({ sincronizarCampos = false } = {}) {
  if (!invoke) return false;
  try {
    const atualizada = await invoke("salvar_configuracoes", {
      config: {
        input_dir: pastaEntrada.value.trim(),
        output_dir: pastaSaida.value.trim(),
        auto_open: autoAbrir.checked,
        engine: selEngine.value,
        voz: selVoz.value,
        velocidade: Number(velocidade.value),
      },
    });
    if (sincronizarCampos && atualizada) {
      aplicarConfig(atualizada);
    }
    avisar("✔ Configurações salvas");
    return true;
  } catch (err) {
    avisar(String(err), true);
    return false;
  }
}

async function trocarPasta(recarregar) {
  const ok = await salvarConfig({ sincronizarCampos: true });
  if (ok) {
    if (recarregar) await carregarLivros();
  } else {
    await carregarConfig();
  }
}

pastaEntrada.addEventListener("change", () => trocarPasta(true));
pastaSaida.addEventListener("change", () => trocarPasta(false));
autoAbrir.addEventListener("change", () => salvarConfig());

async function abrirPastaNoSistema(caminho) {
  if (!caminho) {
    throw "O caminho da pasta está vazio.";
  }
  if (typeof invoke === "function") {
    await invoke("abrir_pasta", { caminho });
  }
}

async function escolherPasta(campo, recarregar) {
  const caminhoAtual = campo.value.trim();
  try {
    await abrirPastaNoSistema(caminhoAtual);
    avisar("Pasta aberta no sistema.");
    if (recarregar) {
      await carregarLivros();
    }
  } catch (err) {
    campo.focus();
    campo.select();
    avisar(String(err) || "Digite o caminho da pasta e pressione Enter", true);
  }
}

document
  .getElementById("btn-escolher-entrada")
  .addEventListener("click", () => escolherPasta(pastaEntrada, true));

document
  .getElementById("btn-escolher-saida")
  .addEventListener("click", () => escolherPasta(pastaSaida, false));

document.getElementById("btn-restaurar").addEventListener("click", async () => {
  if (!invoke) return;
  try {
    const padrao = await invoke("restaurar_padrao");
    aplicarConfig(padrao);
    avisar("✔ Padrões restaurados");
    await carregarLivros();
  } catch (err) {
    avisar(String(err), true);
  }
});

function adicionarLog(texto) {
  const linha = String(texto ?? "");
  logs.textContent += linha + "\n";
  logs.scrollTop = logs.scrollHeight;
}

async function carregarLivros() {
  selectArquivo.innerHTML = "";
  if (!invoke) return;

  try {
    const livros = await invoke("listar_livros");
    if (!Array.isArray(livros) || livros.length === 0) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "(Nenhum .txt, .pdf ou .epub na pasta de entrada)";
      selectArquivo.appendChild(opt);
      atualizarArquivo();
      return;
    }

    for (const nome of livros) {
      const opt = document.createElement("option");
      opt.value = nome;
      opt.textContent = nome;
      selectArquivo.appendChild(opt);
    }
    atualizarArquivo();
  } catch (err) {
    adicionarLog("Erro ao listar livros: " + err);
    atualizarArquivo();
  }
}

if (typeof listen === "function") {
  listen("diehoward-evento", async (event) => {
    const dados = event?.payload || {};
    if (dados.tipo === "status" || dados.tipo === "log") {
      statusTexto.textContent = dados.mensagem;
      adicionarLog(dados.mensagem);
    } else if (dados.tipo === "etapa") {
      statusTexto.textContent = dados.rotulo;
      adicionarLog(">> " + dados.rotulo);
    } else if (dados.tipo === "progresso") {
      atualizarProgresso(dados.porcentagem);
      statusTexto.textContent = `${dados.rotulo} (${dados.porcentagem}%)`;
    } else if (dados.tipo === "concluido") {
      atualizarProgresso(100);
      ultimoDestinoConcluido = dados.destino || pastaSaida.value.trim();
      statusTexto.textContent = "Concluído! Salvo em: " + ultimoDestinoConcluido;
      adicionarLog("CONCLUÍDO: " + ultimoDestinoConcluido);
      btnIniciar.disabled = false;

      if (autoAbrir.checked && pastaSaida.value.trim()) {
        try {
          await abrirPastaNoSistema(pastaSaida.value.trim());
        } catch (err) {
          adicionarLog("Aviso ao abrir pasta de saída: " + err);
        }
      }
    } else if (dados.tipo === "erro") {
      statusTexto.textContent = "Erro!";
      adicionarLog("ERRO: " + dados.mensagem);
      btnIniciar.disabled = false;
    }
  });
}

btnAtualizar.addEventListener("click", carregarLivros);

btnIniciar.addEventListener("click", async () => {
  const arquivo = selectArquivo.value;
  if (!arquivo) {
    adicionarLog("Selecione um arquivo válido na pasta de entrada.");
    return;
  }
  if (!invoke) {
    adicionarLog("ERRO: comando de síntese indisponível.");
    return;
  }

  btnIniciar.disabled = true;
  atualizarProgresso(0);
  logs.textContent = "";
  statusTexto.textContent = "Iniciando...";

  try {
    await invoke("iniciar_sintese", {
      arquivo,
      modo: selModo.value,
      engine: selEngine.value,
      voz: selEngine.value === "kokoro" ? selVoz.value : null,
      velocidade: Number(velocidade.value),
    });
  } catch (err) {
    adicionarLog("ERRO: " + err);
    statusTexto.textContent = "Erro ao iniciar";
    btnIniciar.disabled = false;
  }
});

(async function inicializar() {
  mostrarVelocidade();
  atualizarMotor();
  atualizarProgresso(0);
  await carregarConfig();
  await carregarLivros();
})();

function criarSimulacao() {
  const padrao = {
    input_dir: "data/input",
    output_dir: "data/output",
    auto_open: false,
    engine: "kokoro",
    voz: "pf_dora",
    velocidade: 0.85,
  };
  let config = { ...padrao };
  let timerAtivo = null;
  const ouvintes = {};
  const emitir = (nome, payload) => {
    (ouvintes[nome] || []).forEach((fn) => fn({ payload }));
  };

  return {
    core: {
      async invoke(cmd, args = {}) {
        if (cmd === "obter_configuracoes") return { ...config };
        if (cmd === "restaurar_padrao") {
          config = { ...padrao };
          return { ...config };
        }
        if (cmd === "salvar_configuracoes") {
          const v = Number(args?.config?.velocidade);
          if (!args?.config?.input_dir || !args?.config?.output_dir) {
            throw "O caminho da pasta não pode ficar vazio.";
          }
          if (Number.isNaN(v) || v < 0.5 || v > 2) {
            throw "Velocidade deve ficar entre 0.50 e 2.00.";
          }
          config = { ...args.config, velocidade: v };
          return { ...config };
        }
        if (cmd === "abrir_pasta") {
          return null;
        }
        if (cmd === "listar_livros") {
          return ["dom_casmurro.epub", "o_alienista.txt", "memorias_postumas.pdf"];
        }
        if (cmd === "iniciar_sintese") {
          if (timerAtivo) clearInterval(timerAtivo);
          const motorLabel =
            args.engine === "kokoro"
              ? `Kokoro-82M (${args.voz})`
              : "Piper TTS (faber)";
          emitir("diehoward-evento", {
            tipo: "status",
            mensagem: `Simulação: ${args.arquivo} | ${motorLabel}`,
          });
          emitir("diehoward-evento", {
            tipo: "etapa",
            rotulo: "Extraindo texto",
          });
          let pct = 0;
          timerAtivo = setInterval(() => {
            pct += 10;
            emitir("diehoward-evento", {
              tipo: "progresso",
              rotulo: "Sintetizando",
              porcentagem: pct,
            });
            if (pct % 30 === 0) {
              emitir("diehoward-evento", {
                tipo: "log",
                mensagem: `Trecho ${pct / 10} gerado`,
              });
            }
            if (pct >= 100) {
              clearInterval(timerAtivo);
              timerAtivo = null;
              const base = String(args.arquivo).replace(/\.\w+$/, ".wav");
              emitir("diehoward-evento", {
                tipo: "concluido",
                destino: `${config.output_dir}/${base}`,
              });
            }
          }, 250);
        }
      },
    },
    event: {
      listen(nome, fn) {
        (ouvintes[nome] ||= []).push(fn);
      },
    },
  };
}