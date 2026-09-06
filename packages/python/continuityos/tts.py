from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Protocol


class TextToSpeechProvider(Protocol):
    name: str
    def available(self) -> bool: ...
    def synthesize(self, text: str, output_path: str | Path) -> Path: ...


class PiperAdapter:
    name = "piper"

    def __init__(self, model_path: str | Path, binary: str = "piper") -> None:
        self.model_path = Path(model_path)
        self.binary = binary

    def available(self) -> bool:
        return shutil.which(self.binary) is not None and self.model_path.exists()

    def synthesize(self, text: str, output_path: str | Path) -> Path:
        if not self.available():
            raise RuntimeError("piper binary/model unavailable")
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([self.binary, "--model", str(self.model_path), "--output_file", str(output)], input=text, text=True, check=True, capture_output=True)
        return output
