"""Correct Whisper-transcribed lyrics using Claude's knowledge of song lyrics."""

import json

from anthropic import Anthropic


def correct_lyrics(words: list[dict], title: str | None = None,
                   artist: str | None = None) -> dict:
    """
    Use Claude to correct misheard words in Whisper transcription.

    Each word dict has: {"text": str, "start": float, "end": float}

    Claude compares the transcription against its knowledge of the song's
    official lyrics and corrects words that were likely misheard, while
    preserving the exact same number of entries and all timestamps.

    Returns dict with:
        "words": corrected word list (same structure, same length)
        "identified_title": song title Claude identified (or None)
        "identified_artist": artist Claude identified (or None)
    """
    if not words:
        return {"words": words, "identified_title": None, "identified_artist": None}

    # Build the plain text transcription for Claude to review
    texts = [w["text"] for w in words]
    transcript = " ".join(texts)

    # Build context
    context_parts = []
    if title:
        context_parts.append(f'"{title}"')
    if artist:
        context_parts.append(f"by {artist}")
    context_line = f"Metadata: {' '.join(context_parts)}\n" if context_parts else ""

    prompt = (
        f"{context_line}"
        f"The following lyrics were transcribed from audio using speech recognition. "
        f"Some words may be incorrect due to mishearing.\n\n"
        f"Transcription ({len(texts)} words):\n{transcript}\n\n"
        f"Task: Based on your knowledge of this song's actual lyrics, correct any "
        f"misheard words. Your response must have exactly two sections.\n\n"
        f"SECTION 1 — First line only:\n"
        f"SONG: {{song title}} | ARTIST: {{artist/singer name}}\n"
        f"(Based on your identification of the song. If unsure, use the metadata provided.)\n\n"
        f"SECTION 2 — Corrected words:\n"
        f"EXACTLY {len(texts)} lines, one word per line, in the same order as the transcription.\n\n"
        f"Rules:\n"
        f"- The first line must be the SONG/ARTIST identification.\n"
        f"- Then a blank line.\n"
        f"- Then EXACTLY {len(texts)} word lines.\n"
        f"- If you don't know the song or aren't sure about a correction, "
        f"return the original word unchanged.\n"
        f"- Preserve contractions as-is (don't → don't, not do not).\n"
        f"- Keep the same word boundaries — if Whisper heard one word, output one word.\n"
        f"- No commentary, no numbering beyond the format above.\n"
    )

    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    lines = raw.split("\n")

    # Parse SONG/ARTIST from first line
    identified_title = None
    identified_artist = None
    word_lines_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("SONG:"):
            # Parse "SONG: xxx | ARTIST: yyy"
            parts = stripped.split("|")
            for part in parts:
                part = part.strip()
                if part.startswith("SONG:"):
                    identified_title = part[5:].strip()
                elif part.startswith("ARTIST:"):
                    identified_artist = part[7:].strip()
            word_lines_start = i + 1
            break

    # Skip blank lines after the SONG line
    while word_lines_start < len(lines) and not lines[word_lines_start].strip():
        word_lines_start += 1

    corrected_lines = [l.strip() for l in lines[word_lines_start:] if l.strip()]

    # Safety check: if Claude returned wrong number of words, keep original
    if len(corrected_lines) != len(texts):
        return {
            "words": words,
            "identified_title": identified_title,
            "identified_artist": identified_artist,
        }

    # Apply corrections — only change the text, preserve timestamps
    result = []
    for i, w in enumerate(words):
        result.append({
            "text": corrected_lines[i],
            "start": w["start"],
            "end": w["end"],
        })

    return {
        "words": result,
        "identified_title": identified_title,
        "identified_artist": identified_artist,
    }
