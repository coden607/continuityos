from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Protocol


class SpeechToTextProvider(Protocol):
    name: str
    def available(self) -> bool: ...
    def transcribe(self, audio_path: str | Path) -> str: ...


class WhisperCppAdapter:
    name = "whisper.cpp"

    def __init__(self, model_path: str | Path | None = None, binary: str = "whisper-cli", command: str | None = None) -> None:
        self.model_path = Path(model_path) if model_path else None
        self.binary = command or binary

    def available(self) -> bool:
        binary_ok = shutil.which(self.binary) is not None
        model_ok = self.model_path is None or self.model_path.exists()
        return binary_ok and model_ok

    def command(self, audio_path: str | Path) -> list[str]:
        cmd = [self.binary]
        if self.model_path:
            cmd.extend(["-m", str(self.model_path)])
        cmd.extend(["-f", str(audio_path), "-otxt", "-nt"])
        return cmd

    def transcribe(self, audio_path: str | Path) -> str:
        if not self.available():
            raise RuntimeError("whisper.cpp binary/model unavailable")
        audio_path = Path(audio_path)
        subprocess.run(self.command(audio_path), check=True, capture_output=True, text=True)
        candidates = [Path(str(audio_path) + ".txt"), audio_path.with_suffix(audio_path.suffix + ".txt")]
        for output in candidates:
            if output.exists():
                return output.read_text(encoding="utf-8").strip()
        raise RuntimeError("whisper.cpp completed without a transcript file")


# Backward-compatible name from v0.2.
LocalWhisperAdapter = WhisperCppAdapter


class VoiceRouter:
    def __init__(self, stt_providers: list[SpeechToTextProvider]) -> None:
        self.stt_providers = stt_providers

    def select_stt(self, *, require_local: bool = False) -> SpeechToTextProvider:
        available = [p for p in self.stt_providers if p.available()]
        if require_local:
            available = [p for p in available if p.name == "whisper.cpp"]
        if not available:
            raise LookupError("no speech-to-text provider available")
        return available[0]
