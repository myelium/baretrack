"""Generate ASS subtitle file with karaoke-style word highlighting."""

import math
from pathlib import Path

from .transcribe import Segment, Word

# ASS header with karaoke styling
ASS_HEADER = """\
[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,Arial,60,&H0000FFFF,&H00808080,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,60,60,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# Max words per subtitle line
WORDS_PER_LINE = 6


def _ass_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp H:MM:SS.cc"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _centiseconds(seconds: float) -> int:
    return max(1, int(round(seconds * 100)))


def _build_line(words: list[Word], line_start: float, line_end: float) -> str:
    """
    Build one ASS Dialogue line using actual word timestamps for \\k durations.
    """
    # Use each word's actual duration directly from its timestamps
    k_durations = []
    for i, w in enumerate(words):
        if i < len(words) - 1:
            # Duration until next word starts
            d = max(0.01, words[i + 1].start - w.start)
        else:
            # Last word: use its own end time
            d = max(0.01, w.end - w.start)
        k_durations.append(d)

    text_parts = [
        f"{{\\k{_centiseconds(d)}}}{w.text} "
        for w, d in zip(words, k_durations)
    ]
    text = "".join(text_parts).rstrip()

    return (
        f"Dialogue: 0,{_ass_time(line_start)},{_ass_time(line_end)},"
        f"Karaoke,,0,0,0,,{text}"
    )


def build_ass(segments: list[Segment], output_path: Path) -> Path:
    """
    Build an ASS subtitle file from Whisper segments.

    Long segments are split into sub-lines of WORDS_PER_LINE words.
    Each sub-line uses the actual word timestamps for display timing.
    """
    lines = []

    for seg in segments:
        words = seg.words
        n_lines = math.ceil(len(words) / WORDS_PER_LINE)

        for i in range(n_lines):
            chunk = words[i * WORDS_PER_LINE : (i + 1) * WORDS_PER_LINE]
            line_start = chunk[0].start
            # End at the next chunk's start (or segment end for last chunk)
            if i < n_lines - 1:
                next_chunk_start = words[(i + 1) * WORDS_PER_LINE].start
                line_end = next_chunk_start
            else:
                line_end = seg.end
            lines.append(_build_line(chunk, line_start, line_end))

    output_path.write_text(ASS_HEADER + "\n".join(lines) + "\n")
    return output_path


def _srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    whole = int(s)
    ms = int(round((s - whole) * 1000))
    return f"{h:02d}:{m:02d}:{whole:02d},{ms:03d}"


def build_srt(segments: list[Segment], output_path: Path) -> Path:
    """
    Build a standard SRT subtitle file from Whisper segments.

    Groups words into lines of WORDS_PER_LINE, using actual word timestamps.
    """
    entries = []
    idx = 1

    for seg in segments:
        words = seg.words
        n_lines = math.ceil(len(words) / WORDS_PER_LINE)

        for i in range(n_lines):
            chunk = words[i * WORDS_PER_LINE : (i + 1) * WORDS_PER_LINE]
            line_start = chunk[0].start
            if i < n_lines - 1:
                line_end = words[(i + 1) * WORDS_PER_LINE].start
            else:
                line_end = seg.end
            text = " ".join(w.text for w in chunk)
            entries.append(
                f"{idx}\n{_srt_time(line_start)} --> {_srt_time(line_end)}\n{text}"
            )
            idx += 1

    output_path.write_text("\n\n".join(entries) + "\n")
    return output_path
