const { invoke } = window.__TAURI__.core;
const { listen } = window.__TAURI__.event;

const selectArquivo = document.getElementById("arquivo");
const btnAtualizar = document.getElementById("btn-atualizar");
const btnIniciar = document.getElementById("btn-iniciar");
const statusTexto = document.getElementById("status-texto");
const barra = document.getElementById("barra");
const logs = document.getElementById("logs");

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
      opt.textContent = "(Nenhum livro em data/input)";
      selectArquivo.appendChild(opt);
      return;
    }
    for (const nome of livros) {
      const opt = document.createElement("option");
      opt.value = nome;
      opt.textContent = nome;
      selectArquivo.appendChild(opt);
    }
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

  await invoke("iniciar_sintese", {
    arquivo,
    modo: document.getElementById("modo").value,
    engine: document.getElementById("engine").value,
    voz: document.getElementById("voz").value,
    velocidade: document.getElementById("velocidade").value,
  });
});

carregarLivros();