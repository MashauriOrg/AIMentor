"""CLI utility to transcribe MP4 files with Whisper.

Usage:
    python transcribe_mp4.py --input path/to/video.mp4 --output transcript.txt

Requires the OPENAI_API_KEY environment variable to be set.
"""

import argparse
import os
from pathlib import Path
from typing import Optional

from openai import OpenAI


def transcribe_mp4(
    input_path: Path,
    output_path: Optional[Path] = None,
    model: str = "whisper-1",
    prompt: Optional[str] = None,
    language: Optional[str] = None,
) -> str:
    """Transcribe an MP4 file using the Whisper API.

    Args:
        input_path: Path to the MP4 video file.
        output_path: Optional path where the transcript will be written.
        model: Whisper model to use.
        prompt: Optional prompt to guide the transcription.
        language: Optional language code (e.g., "en") to hint the model.

    Returns:
        The transcribed text.
    """

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Please export your API key before running the script."
        )

    client = OpenAI(api_key=api_key)

    with input_path.open("rb") as audio_file:
        response = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            prompt=prompt,
            language=language,
        )

    transcript = response.text

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(transcript, encoding="utf-8")

    return transcript


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe an MP4 file with Whisper.")
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the MP4 video file to transcribe.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path for the transcript (text file).",
    )
    parser.add_argument(
        "--model",
        default="whisper-1",
        help="Whisper model to use (default: whisper-1).",
    )
    parser.add_argument(
        "--prompt",
        help="Optional prompt to provide context to the model.",
    )
    parser.add_argument(
        "--language",
        help="Optional language code (e.g., en, es) to guide transcription.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    transcript = transcribe_mp4(
        input_path=args.input,
        output_path=args.output,
        model=args.model,
        prompt=args.prompt,
        language=args.language,
    )
    print(transcript)


if __name__ == "__main__":
    main()
