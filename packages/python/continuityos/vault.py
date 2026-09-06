from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class SopsAgeVault:
    """Optional encrypted vault wrapper. Secrets remain usable without it via .env.local."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def available(self) -> bool:
        return shutil.which("sops") is not None and shutil.which("age") is not None

    def encrypt(self, plaintext: str | Path, encrypted: str | Path, *, age_recipient: str) -> Path:
        if not self.available():
            raise RuntimeError("sops and age CLIs are required for encrypted vault operations")
        plaintext = Path(plaintext)
        encrypted = Path(encrypted)
        encrypted.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["sops", "--encrypt", "--age", age_recipient, "--output", str(encrypted), str(plaintext)],
            check=True,
            capture_output=True,
            text=True,
        )
        return encrypted

    def decrypt(self, encrypted: str | Path, output: str | Path) -> Path:
        if not self.available():
            raise RuntimeError("sops and age CLIs are required for encrypted vault operations")
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["sops", "--decrypt", "--output", str(output), str(encrypted)], check=True, capture_output=True, text=True)
        return output
