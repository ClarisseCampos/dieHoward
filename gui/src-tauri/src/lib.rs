use serde_json::{json, Value};
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::thread;
use tauri::{Emitter, Window};

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

#[cfg(target_os = "windows")]
const CREATE_NO_WINDOW: u32 = 0x08000000;

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
        for _ in 0..6 {
            if dir.join("app").join("gui_bridge.py").exists() {
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

fn encontrar_python(raiz: &Path) -> PathBuf {
    #[cfg(target_os = "windows")]
    let venv_py = raiz.join(".venv").join("Scripts").join("python.exe");

    #[cfg(not(target_os = "windows"))]
    let venv_py = raiz.join(".venv").join("bin").join("python");

    if venv_py.exists() {
        return venv_py;
    }

    #[cfg(target_os = "windows")]
    {
        PathBuf::from("python")
    }

    #[cfg(not(target_os = "windows"))]
    {
        PathBuf::from("python3")
    }
}

fn preparar_comando_python(raiz: &Path) -> Command {
    let python = encontrar_python(raiz);
    let mut cmd = Command::new(python);
    cmd.current_dir(raiz)
        .arg("app/gui_bridge.py")
        .env("PYTHONPATH", raiz)
        .env("PYTHONUTF8", "1")
        .env("PYTHONIOENCODING", "utf-8");

    #[cfg(target_os = "windows")]
    cmd.creation_flags(CREATE_NO_WINDOW);

    cmd
}

fn executar_bridge_json(args: &[String]) -> Result<Value, String> {
    let raiz = encontrar_raiz_projeto();
    let mut cmd = preparar_comando_python(&raiz);
    cmd.args(args);

    let output = cmd
        .output()
        .map_err(|e| format!("Falha ao executar o Python: {e}"))?;

    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();

    if !output.status.success() {
        let detalhe = if !stderr.is_empty() { stderr } else { stdout };
        return Err(format!("Erro no backend Python: {detalhe}"));
    }

    if stdout.is_empty() {
        return Ok(Value::Null);
    }

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Resposta inválida do gui_bridge.py: {e}\nSaída: {stdout}"))
}

#[tauri::command]
fn obter_configuracoes() -> Result<Value, String> {
    executar_bridge_json(&["obter-config".to_string()])
}

#[tauri::command]
fn salvar_configuracoes(config: Value) -> Result<Value, String> {
    let payload = serde_json::to_string(&config)
        .map_err(|e| format!("Erro ao serializar configurações: {e}"))?;
    executar_bridge_json(&["salvar-config".to_string(), payload])
}

#[tauri::command]
fn restaurar_padrao() -> Result<Value, String> {
    executar_bridge_json(&["restaurar-padrao".to_string()])
}

#[tauri::command]
fn listar_livros() -> Result<Value, String> {
    executar_bridge_json(&["listar-livros".to_string()])
}

#[tauri::command]
fn abrir_pasta(caminho: String) -> Result<(), String> {
    let limpo = caminho.trim();
    if limpo.is_empty() {
        return Err("O caminho da pasta está vazio.".to_string());
    }

    let raiz = encontrar_raiz_projeto();
    let pasta_bruta = PathBuf::from(limpo);
    let pasta = if pasta_bruta.is_absolute() {
        pasta_bruta
    } else {
        raiz.join(pasta_bruta)
    };

    if !pasta.exists() {
        fs::create_dir_all(&pasta)
            .map_err(|e| format!("Não foi possível criar a pasta: {e}"))?;
    }

    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .arg(&pasta)
            .spawn()
            .map_err(|e| format!("Falha ao abrir o Explorador de Arquivos: {e}"))?;
    }

    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(&pasta)
            .spawn()
            .map_err(|e| format!("Falha ao abrir o gerenciador de arquivos: {e}"))?;
    }

    Ok(())
}

#[tauri::command]
fn iniciar_sintese(
    window: Window,
    arquivo: String,
    modo: Option<String>,
    engine: String,
    voz: Option<String>,
    velocidade: Option<Value>,
) -> Result<(), String> {
    let raiz = encontrar_raiz_projeto();
    let mut cmd = preparar_comando_python(&raiz);

    cmd.arg("sintetizar")
        .arg("--arquivo")
        .arg(&arquivo)
        .arg("--engine")
        .arg(&engine);

    if let Some(m) = modo {
        if !m.trim().is_empty() {
            cmd.arg("--modo").arg(m);
        }
    }

    if let Some(v) = voz {
        if !v.trim().is_empty() {
            cmd.arg("--voz").arg(v);
        }
    }

    if let Some(vel) = velocidade {
        let vel_str = match vel {
            Value::String(s) => s,
            Value::Number(n) => n.to_string(),
            other => other.to_string(),
        };
        if !vel_str.trim().is_empty() {
            cmd.arg("--velocidade").arg(vel_str);
        }
    }

    cmd.stdout(Stdio::piped()).stderr(Stdio::piped());

    thread::spawn(move || match cmd.spawn() {
        Ok(mut child) => {
            if let Some(stdout) = child.stdout.take() {
                let reader = BufReader::new(stdout);
                for linha in reader.lines().map_while(Result::ok) {
                    let payload: Value = serde_json::from_str(&linha)
                        .unwrap_or_else(|_| json!({ "tipo": "log", "mensagem": linha }));
                    let _ = window.emit("diehoward-evento", payload);
                }
            }
            if let Some(stderr) = child.stderr.take() {
                let reader = BufReader::new(stderr);
                for linha in reader.lines().map_while(Result::ok) {
                    if !linha.trim().is_empty() {
                        let _ = window.emit(
                            "diehoward-evento",
                            json!({ "tipo": "log", "mensagem": linha }),
                        );
                    }
                }
            }
            let _ = child.wait();
        }
        Err(e) => {
            let _ = window.emit(
                "diehoward-evento",
                json!({ "tipo": "erro", "mensagem": format!("Falha ao iniciar Python: {e}") }),
            );
        }
    });

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            obter_configuracoes,
            salvar_configuracoes,
            restaurar_padrao,
            listar_livros,
            iniciar_sintese,
            abrir_pasta,
        ])
        .run(tauri::generate_context!())
        .expect("erro ao executar aplicacao Tauri");
}