// Fora do Tauri (ex.: navegador), usa uma simulação para testar a interface.
const tauri = window.__TAURI__ ?? criarSimulacao();
const { invoke } = tauri.core;
const { listen } = tauri.event;

const selectArquivo = document.getElementById("arquivo");
const btnAtualizar = document.getElementById("btn-atualizar");
const btnIniciar = document.getElementById("btn-iniciar");
const statusTexto = document.getElementById("status-texto");
const barra = document.getElementById("barra");
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

function mostrarVelocidade() {
  const v = Number(velocidade.value);
  velValor.textContent = v.toFixed(2) + "×";
  chips.forEach((c) => c.classList.toggle("ativo", Number(c.dataset.v) === v));
}
velocidade.addEventListener("input", mostrarVelocidade);
velocidade.addEventListener("change", salvarConfig);
chips.forEach((c) =>
  c.addEventListener("click", () => {
    velocidade.value = c.dataset.v;
    mostrarVelocidade();
    salvarConfig();
  })
);

// Piper tem uma única voz; a escolha de voz só existe no Kokoro.
function atualizarMotor() {
  const piper = selEngine.value === "piper";
  selVoz.hidden = piper;
  vozPiper.hidden = !piper;
}
selEngine.addEventListener("change", () => { atualizarMotor(); salvarConfig(); });
selVoz.addEventListener("change", salvarConfig);

// Arquivos .txt não têm capítulos: sempre arquivo único.
function atualizarArquivo() {
  const nome = selectArquivo.value;
  const ext = nome.split(".").pop().toLowerCase();
  livroInfo.textContent = nome ? ext.toUpperCase() : "";
  if (nome && ext === "txt") {
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
  avisoConfig.classList.toggle("erro", erro);
  clearTimeout(avisar.t);
  avisar.t = setTimeout(() => (avisoConfig.textContent = ""), 3000);
}

function aplicarConfig(c) {
  pastaEntrada.value = c.input_dir;
  pastaSaida.value = c.output_dir;
  autoAbrir.checked = c.auto_open;
  selEngine.value = c.engine;
  selVoz.value = c.voz;
  velocidade.value = c.velocidade;
  atualizarMotor();
  mostrarVelocidade();
}

async function carregarConfig() {
  try {
    aplicarConfig(await invoke("obter_configuracoes"));
  } catch (err) {
    adicionarLog("Erro ao ler configurações: " + err);
  }
}

async function salvarConfig() {
  try {
    const c = await invoke("salvar_configuracoes", {
      config: {
        input_dir: pastaEntrada.value.trim(),
        output_dir: pastaSaida.value.trim(),
        auto_open: autoAbrir.checked,
        engine: selEngine.value,
        voz: selVoz.value,
        velocidade: Number(velocidade.value),
      },
    });
    if (c) aplicarConfig(c);
    avisar("✔ Configurações salvas");
    return true;
  } catch (err) {
    avisar(String(err), true);
    return false;
  }
}

async function trocarPasta(campo, recarregar) {
  if (await salvarConfig()) {
    if (recarregar) carregarLivros();
  } else {
    carregarConfig();
  }
}
pastaEntrada.addEventListener("change", () => trocarPasta(pastaEntrada, true));
pastaSaida.addEventListener("change", () => trocarPasta(pastaSaida, false));
autoAbrir.addEventListener("change", salvarConfig);

async function escolherPasta(campo, recarregar) {
  const dialog = tauri.dialog;
  if (!dialog) {
    campo.focus();
    campo.select();
    avisar("Digite o caminho e pressione Enter");
    return;
  }
  const pasta = await dialog.open({ directory: true, defaultPath: campo.value });
  if (pasta) {
    campo.value = pasta;
    trocarPasta(campo, recarregar);
  }
}
document.getElementById("btn-escolher-entrada").addEventListener("click", () => escolherPasta(pastaEntrada, true));
document.getElementById("btn-escolher-saida").addEventListener("click", () => escolherPasta(pastaSaida, false));

document.getElementById("btn-restaurar").addEventListener("click", async () => {
  try {
    aplicarConfig(await invoke("restaurar_padrao"));
    avisar("✔ Padrões restaurados");
    carregarLivros();
  } catch (err) {
    avisar(String(err), true);
  }
});

function adicionarLog(texto) {
  logs.textContent += texto + "\n";
  logs.scrollTop = logs.scrollHeight;
}

async function carregarLivros() {
  selectArquivo.innerHTML = "";
  try {
    const livros = await invoke("listar_livros");
    if (livros.length === 0) {
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
  }
}

listen("diehoward-evento", (event) => {
  const dados = event.payload;
  if (dados.tipo === "status" || dados.tipo === "log") {
    statusTexto.textContent = dados.mensagem;
    adicionarLog(dados.mensagem);
  } else if (dados.tipo === "etapa") {
    statusTexto.textContent = dados.rotulo;
    adicionarLog(">> " + dados.rotulo);
  } else if (dados.tipo === "progresso") {
    barra.value = dados.porcentagem;
    statusTexto.textContent = `${dados.rotulo} (${dados.porcentagem}%)`;
  } else if (dados.tipo === "concluido") {
    barra.value = 100;
    statusTexto.textContent = "Concluído! Salvo em: " + dados.destino;
    adicionarLog("CONCLUÍDO: " + dados.destino);
    btnIniciar.disabled = false;
  } else if (dados.tipo === "erro") {
    statusTexto.textContent = "Erro!";
    adicionarLog("ERRO: " + dados.mensagem);
    btnIniciar.disabled = false;
  }
});

btnAtualizar.addEventListener("click", carregarLivros);

btnIniciar.addEventListener("click", async () => {
  const arquivo = selectArquivo.value;
  if (!arquivo) {
    adicionarLog("Selecione um arquivo válido.");
    return;
  }
  btnIniciar.disabled = true;
  barra.value = 0;
  logs.textContent = "";
  statusTexto.textContent = "Iniciando...";
  try {
    await invoke("iniciar_sintese", {
      arquivo,
      modo: selModo.value,
      engine: selEngine.value,
      voz: selEngine.value === "kokoro" ? selVoz.value : null,
      velocidade: velocidade.value,
    });
  } catch (err) {
    adicionarLog("ERRO: " + err);
    btnIniciar.disabled = false;
  }
});

carregarConfig().then(carregarLivros);

function criarSimulacao() {
  const padrao = { input_dir: "~/DieHoward/data/input", output_dir: "~/DieHoward/data/output", auto_open: true, engine: "kokoro", voz: "pf_dora", velocidade: 0.85 };
  let config = { ...padrao };
  const ouvintes = {};
  const emitir = (nome, payload) => (ouvintes[nome] || []).forEach((f) => f({ payload }));
  return {
    core: {
      async invoke(cmd, args) {
        if (cmd === "obter_configuracoes") return { ...config };
        if (cmd === "restaurar_padrao") return (config = { ...padrao }), { ...config };
        if (cmd === "salvar_configuracoes") {
          const v = args.config.velocidade;
          if (!args.config.input_dir || !args.config.output_dir) throw "O caminho da pasta não pode ficar vazio.";
          if (v < 0.5 || v > 2) throw "Velocidade deve ficar entre 0.50 e 2.00.";
          return (config = { ...args.config }), { ...config };
        }
        if (cmd === "listar_livros") return ["dom_casmurro.epub", "o_alienista.txt", "memorias_postumas.pdf"];
        if (cmd === "iniciar_sintese") {
          const e = (p) => emitir("diehoward-evento", p);
          e({ tipo: "status", mensagem: `Simulação: ${args.arquivo} | ${args.engine === "kokoro" ? "Kokoro-82M (" + args.voz + ")" : "Piper TTS (faber)"}` });
          e({ tipo: "etapa", rotulo: "Extraindo texto" });
          let p = 0;
          const t = setInterval(() => {
            p += 10;
            e({ tipo: "progresso", rotulo: "Sintetizando", porcentagem: p });
            if (p % 30 === 0) e({ tipo: "log", mensagem: `Trecho ${p / 10} gerado` });
            if (p >= 100) {
              clearInterval(t);
              e({ tipo: "concluido", destino: config.output_dir + "/" + args.arquivo.replace(/\.\w+$/, ".wav") });
            }
          }, 300);
        }
      },
    },
    event: {
      listen(nome, f) {
        (ouvintes[nome] ||= []).push(f);
      },
    },
  };
}
