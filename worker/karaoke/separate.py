"""Separate vocals from audio using Demucs."""

import os
import subprocess
import sys
from pathlib import Path

# htdemucs_ft: higher quality, ~3GB RAM
# htdemucs: lighter, ~1.5GB RAM — use when memory is tight
DEMUCS_MODEL = os.getenv("DEMUCS_MODEL", "htdemucs_ft")


def separate(audio_path: Path, output_dir: Path, device: str = "cpu", model: str | None = None) -> tuple[Path, Path]:
    """
    Run Demucs htdemucs model to separate vocals and instrumental.

    Returns:
        (instrumental_path, vocals_path)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    use_model = model or DEMUCS_MODEL

    cmd = [
        sys.executable, "-m", "demucs",
        "-n", use_model,
        "--two-stems", "vocals",
        "-d", device,
        "--out", str(output_dir),
        str(audio_path),
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=None, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Demucs failed (exit {result.returncode})")

    # Demucs outputs to: output_dir/<model>/<stem_name>/{vocals,no_vocals}.wav
    stem_name = audio_path.stem
    demucs_out = output_dir / use_model / stem_name
    instrumental_path = demucs_out / "no_vocals.wav"
    vocals_path = demucs_out / "vocals.wav"

    if not instrumental_path.exists():
        raise FileNotFoundError(f"Demucs output not found: {instrumental_path}")

    return instrumental_path, vocals_path
