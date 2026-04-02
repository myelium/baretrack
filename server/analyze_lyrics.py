"""Analyze song lyrics line-by-line for deeper meaning using Claude."""

import json

from anthropic import Anthropic

DEFAULT_ANALYSIS_PROMPT = """\
Decode these lyrics line by line. For each line or couplet, explain \
the deeper meaning, symbolism, metaphors, cultural references, and \
emotional subtext. Help the reader truly understand what the songwriter \
is expressing beyond the surface words.

Consider the historical and social context of when this song was written \
and released. What was happening in the world, in the artist's life, or \
in the cultural zeitgeist at that time? How did those circumstances shape \
the meaning of these lyrics? Weave this context naturally into your \
line-by-line interpretation — don't separate it into its own section, \
but let it enrich each observation where relevant.

Format rules:
- Start your response with exactly one line: "Song: {identified title} by {identified artist} ({year})" \
based on your knowledge of the lyrics. Include the release year if known. \
If you cannot identify the song, use the provided metadata.
- Then a blank line, followed by the analysis.
- Quote each lyric line in double quotes (e.g. "lyric line here"), not italics.
- If the song is NOT in English, immediately after the quoted lyric line, \
add an English translation on the next line in italics (e.g. *English translation here*). \
If the song IS in English, skip this step — do not duplicate the English lyrics.
- Then give the interpretation below.
- Keep interpretations concise but insightful (1-3 sentences each).
- If lines work together as a couplet or verse, group them.
- End with a brief overall reflection on the song's core message and its \
place in the cultural moment it emerged from.
- Use plain text with minimal formatting.
- Do not use headers or bullet points. Write in flowing prose style.
- Do not add any disclaimers or preamble beyond the Song: line."""


def analyze_lyrics(lyrics_text: str, title: str | None = None,
                   artist: str | None = None,
                   custom_prompt: str | None = None) -> dict:
    """
    Use Claude to decode the deeper meaning of song lyrics, line by line.

    Args:
        lyrics_text: The full lyrics as plain text.
        title: Song title for context.
        artist: Artist/channel name for context.
        custom_prompt: Optional custom prompt to override the default.

    Returns:
        Dict with "song_info" (identified title/artist) and "analysis" text.
    """
    context_parts = []
    if title:
        context_parts.append(f'"{title}"')
    if artist:
        context_parts.append(f"by {artist}")
    context_line = f"Metadata: {' '.join(context_parts)}\n\n" if context_parts else ""

    analysis_prompt = custom_prompt or DEFAULT_ANALYSIS_PROMPT

    prompt = (
        f"{context_line}"
        f"Here are the lyrics:\n\n{lyrics_text}\n\n"
        f"{analysis_prompt}"
    )

    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()

    # Parse the "Song: ..." line from the response
    song_info = ""
    analysis = text
    lines = text.split("\n", 2)
    if lines and lines[0].startswith("Song:"):
        song_info = lines[0].replace("Song:", "").strip()
        # Rest is the analysis (skip blank line after Song: line)
        analysis = "\n".join(lines[1:]).lstrip("\n")

    # Extract year from song_info, e.g. "Alone by Heart (1987)"
    import re
    year_match = re.search(r"\((\d{4})\)", song_info)
    year = year_match.group(1) if year_match else None

    return {"song_info": song_info, "analysis": analysis, "year": year}
