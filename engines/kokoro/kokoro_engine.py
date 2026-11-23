import os
import numpy as np
import soundfile as sf
import onnxruntime as ort
from kokoro_onnx import Kokoro


class KokoroCPUEngine:
    def __init__(
        self,
        model_path="models/kokoro/kokoro-v1.0.onnx",
        voices_path="models/kokoro/voices-v1.0.bin",
    ):
        # Suprime mensagens internas em C++ do ONNX caso o fallback de GPU -> CPU ocorra
        ort.set_default_logger_severity(4)

        opts = ort.SessionOptions()
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        opts.intra_op_num_threads = os.cpu_count() or 4

        provedores_disponiveis = ort.get_available_providers()
        if "CUDAExecutionProvider" in provedores_disponiveis:
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        else:
            providers = ["CPUExecutionProvider"]

        session = ort.InferenceSession(
            model_path,
            sess_options=opts,
            providers=providers,
        )

        # Consulta qual provedor foi realmente ativado após eventual fallback
        self.active_provider = session.get_providers()[0]
        self.kokoro = Kokoro.from_session(session, voices_path)

        hardware_label = (
            "GPU (CUDA)" if self.active_provider == "CUDAExecutionProvider" else "CPU"
        )
        print(f"[Kokoro] Hardware ativo: {hardware_label}")

    def gerar_audio_com_progresso(
        self,
        texto: str,
        output_path: str,
        voice: str = "pf_dora",
        speed: float = 1.0,
        progress_callback=None,
    ):
        lang = "pt-br" if voice.startswith(("p", "pt")) else "en-us"

        paragrafos = [p.strip() for p in texto.split("\n") if p.strip()]
        if not paragrafos:
            paragrafos = [texto]

        todos_samples = []
        sample_rate = 24000
        total_passos = len(paragrafos)

        for idx, trecho in enumerate(paragrafos):
            samples, sr = self.kokoro.create(
                text=trecho,
                voice=voice,
                speed=speed,
                lang=lang,
            )
            sample_rate = sr
            todos_samples.append(samples)

            if progress_callback:
                porcentagem = int(((idx + 1) / total_passos) * 100)
                progress_callback(porcentagem, idx + 1, total_passos)

        if todos_samples:
            audio_final = np.concatenate(todos_samples)
            sf.write(output_path, audio_final, sample_rate)
        else:
            raise RuntimeError("Falha na geração de áudio. Nenhum bloco válido foi sintetizado.")