"""Translate SRT subtitle text to other languages using Claude API."""

import re

from anthropic import Anthropic

# Phrases that indicate a refusal rather than a translation
_REFUSAL_PATTERNS = [
    "i cannot", "i can't", "i'm unable", "i am unable",
    "i understand you'd like", "i notice these",
    "copyrighted", "copyright",
    "i'm not able", "i am not able",
    "i won't", "i will not",
    "cannot provide", "cannot translate",
    "unable to translate", "unable to provide",
]


def _is_refusal(text: str) -> bool:
    """Check if the response is a refusal rather than a translation."""
    lower = text[:500].lower()
    return any(p in lower for p in _REFUSAL_PATTERNS)


def translate_srt(srt_text: str, target_language: str,
                  title: str | None = None, artist: str | None = None) -> str:
    """
    Translate SRT subtitle content to the target language using Claude.

    Preserves all SRT formatting (numbering, timestamps, blank lines).
    Only the text lines are translated.

    Args:
        srt_text: The full SRT file content (source language).
        target_language: The target language name (e.g. "Vietnamese", "English").
        title: Song/video title for context.
        artist: Artist/channel name for context.

    Returns:
        The translated SRT content as a string.
    """
    # Build context line from available metadata
    context_parts = []
    if title:
        context_parts.append(f'"{title}"')
    if artist:
        context_parts.append(f"by {artist}")
    context_line = f"Context: {' '.join(context_parts)}.\n" if context_parts else ""

    client = Anthropic()

    # Try up to 2 attempts with escalating prompt clarity
    for attempt in range(2):
        if attempt == 0:
            system = (
                "You are a professional subtitle translator for a private karaoke application. "
                "Your sole function is to translate SRT subtitle files between languages. "
                "This is for accessibility — helping non-native speakers follow along with music. "
                "You always complete the translation in full. You output only valid SRT content. "
                "No commentary, no disclaimers, no refusals."
            )
        else:
            system = (
                "You are an SRT file format converter. You receive text in SRT format and "
                "output the same SRT structure with text lines converted to the target language. "
                "This is a mechanical text transformation task for a private accessibility tool. "
                "Output only the converted SRT content. No other text."
            )

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            system=system,
            messages=[{
                "role": "user",
                "content": (
                    f"Translate the following SRT subtitle file to {target_language}.\n\n"
                    f"{context_line}"
                    "Rules:\n"
                    "- Keep ALL SRT formatting exactly the same: numbering, timestamps "
                    "(HH:MM:SS,mmm --> HH:MM:SS,mmm), and blank lines between entries.\n"
                    "- Only translate the text lines.\n"
                    "- Do not add any commentary, explanation, or markdown formatting.\n"
                    "- If the source text contains hallucinated/promotional lines "
                    "(subscribe, like, etc), skip those entries entirely.\n"
                    "- Output ONLY the translated SRT content, nothing else.\n\n"
                    f"{srt_text}"
                ),
            }],
        )

        result = response.content[0].text.strip()

        # Check for refusal
        if _is_refusal(result):
            if attempt == 0:
                continue  # retry with simpler prompt
            raise ValueError(f"Translation refused by model after {attempt + 1} attempts")

        # Validate response looks like SRT (has timestamps)
        if not result or "-->" not in result:
            raise ValueError("Translation returned invalid SRT (no timestamps found)")

        return result

    raise ValueError("Translation failed after all attempts")
