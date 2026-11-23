use serde_json::{json, Value};
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::thread;
use tauri::{Emitter, Window};

fn encontrar_raiz_projeto() -> PathBuf {
    let mut candidatos = Vec::new();

    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            candidatos.push(exe_dir.to_path_buf());
        }
    }
    if let Ok(cwd) = std::env::current_dir() {
        candidatos.push(cwd);
    }

    for base in candidatos {
        let mut dir = base;
        for _ in 0..5 {
            if dir.join("gui_bridge.py").exists() {
                return dir;
            }
            if let Some(pai) = dir.parent() {
                dir = pai.to_path_buf();
            } else {
                break;
            }
        }
    }

    PathBuf::from(".")
}

#[tauri::command]
fn listar_livros() -> Result<Vec<String>, String> {
    let pasta_input = encontrar_raiz_projeto().join("data").join("input");
    let entries = fs::read_dir(&pasta_input)
        .map_err(|e| format!("Erro ao ler {}: {}", pasta_input.display(), e))?;

    let mut livros = Vec::new();
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_file() {
            if let Some(nome) = path.file_name().and_then(|n| n.to_str()) {
                if nome.starts_with('.') {
                    continue;
                }
                let lower = nome.to_lowercase();
                if lower.ends_with(".txt") || lower.ends_with(".pdf") || lower.ends_with(".epub") {
                    livros.push(nome.to_string());
                }
            }
        }
    }
    livros.sort_by_key(|a| a.to_lowercase());
    Ok(livros)
}

#[tauri::command]
fn iniciar_sintese(
    window: Window,
    arquivo: String,
    modo: String,
    engine: String,
    voz: String,
    velocidade: String,
) -> Result<(), String> {
    let raiz = encontrar_raiz_projeto();

    let python_venv = if cfg!(target_os = "windows") {
        raiz.join(".venv").join("Scripts").join("python.exe")
    } else {
        raiz.join(".venv").join("bin").join("python")
    };

    let python_bin = if python_venv.exists() {
        python_venv
    } else {
        PathBuf::from(if cfg!(target_os = "windows") { "python" } else { "python3" })
    };

    let caminho_arquivo = if Path::new(&arquivo).is_absolute() {
        PathBuf::from(&arquivo)
    } else {
        raiz.join("data").join("input").join(&arquivo)
    };

    thread::spawn(move || {
        let processo = Command::new(&python_bin)
            .current_dir(&raiz)
            .arg("gui_bridge.py")
            .arg("--arquivo")
            .arg(&caminho_arquivo)
            .arg("--modo")
            .arg(&modo)
            .arg("--engine")
            .arg(&engine)
            .arg("--voz")
            .arg(&voz)
            .arg("--velocidade")
            .arg(&velocidade)
            .env("PYTHONUTF8", "1")
            .env("PYTHONIOENCODING", "utf-8")
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn();

        match processo {
            Ok(mut child) => {
                if let Some(stdout) = child.stdout.take() {
                    let reader = BufReader::new(stdout);
                    for linha in reader.lines().map_while(Result::ok) {
                        let payload: Value = serde_json::from_str(&linha)
                            .unwrap_or_else(|_| json!({ "tipo": "log", "mensagem": linha }));
                        let _ = window.emit("diehoward-evento", payload);
                    }
                }
                let _ = child.wait();
            }
            Err(e) => {
                let _ = window.emit(
                    "diehoward-evento",
                    json!({ "tipo": "erro", "mensagem": format!("Falha ao iniciar Python: {}", e) }),
                );
            }
        }
    });

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![listar_livros, iniciar_sintese])
        .run(tauri::generate_context!())
        .expect("erro ao executar aplicacao Tauri");
}