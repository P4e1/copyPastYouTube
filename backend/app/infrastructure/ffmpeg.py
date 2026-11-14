"""Кадр превью и длительность через ffmpeg."""

import subprocess
import tempfile
from pathlib import Path


class FfmpegExtractor:
    def preview(self, source: bytes) -> tuple[bytes, int]:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source_path = folder / "source.mp4"
            thumb_path = folder / "thumbnail.jpg"
            source_path.write_bytes(source)
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(source_path), "-frames:v", "1", str(thumb_path)],
                check=True,
                capture_output=True,
            )
            probed = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(source_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            if not thumb_path.is_file():
                raise RuntimeError("Превью не создано")
            duration = int(float(probed.stdout.strip() or "0"))
            return thumb_path.read_bytes(), max(duration, 1)
