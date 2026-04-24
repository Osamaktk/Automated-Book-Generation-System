import re
from typing import Iterable


def extract_requested_chapter_limit(notes: str, editor_notes: str = "") -> int | None:
    text = f"{notes}\n{editor_notes}".lower()
    patterns = [
        r"do not exceed\s+(\d+)\s+(\d+)\s+chapters",
        r"do not exceed\s+(\d+)\s*[-to]+\s*(\d+)\s+chapters",
        r"(\d+)\s*[-to]+\s*(\d+)\s+chapters",
        r"(\d+)\s+(\d+)\s+chapters",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return max(int(value) for value in match.groups())

    single_value_patterns = [
        r"do not exceed\s+(\d+)\s+chapters?",
        r"no more than\s+(\d+)\s+chapters?",
        r"maximum of\s+(\d+)\s+chapters?",
        r"max(?:imum)?\s+(\d+)\s+chapters?",
        r"only\s+(\d+)\s+chapters?",
        r"just\s+(\d+)\s+chapters?",
        r"(\d+)\s+chapters?\s+only",
    ]
    for pattern in single_value_patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    if "short story" in text or "very short" in text:
        return 3
    return None


def _editor_requests_ending(editor_notes: str) -> bool:
    if not editor_notes:
        return False
    text = editor_notes.lower()
    ending_keywords = [
        "end the chapter",
        "end the story",
        "ending",
        "final chapter",
        "last chapter",
        "conclude",
        "wrap up",
        "finish the story",
    ]
    return any(keyword in text for keyword in ending_keywords)


def build_outline_prompt(title: str, notes: str, editor_notes: str = "") -> str:
    revision_context = f"\n\nEDITOR FEEDBACK:\n{editor_notes}" if editor_notes else ""
    chapter_limit = extract_requested_chapter_limit(notes, editor_notes)
    chapter_instruction = (
        f"2. List of chapters (exactly {chapter_limit}) with:"
        if chapter_limit
        else "2. List of chapters (at least 5) with:"
    )
    limit_guard = (
        f"\nImportant: The notes request a short structure. Do not exceed {chapter_limit} chapters."
        if chapter_limit
        else ""
    )
    return f"""You are a professional book author and editor.
Generate a detailed book outline for the following:

TITLE: {title}
AUTHOR NOTES: {notes}{revision_context}
{limit_guard}

Your outline must include:
1. A brief book description (2-3 sentences)
{chapter_instruction}
   - Chapter number and title
   - A 2-3 sentence description of what happens in that chapter

Format it cleanly and professionally."""


def build_chapter_prompt(
    title: str,
    outline: str,
    chapter_number: int,
    chapter_title: str,
    previous_summaries: Iterable[dict],
    editor_notes: str = "",
) -> str:
    context = ""
    summaries = list(previous_summaries)
    planned_chapter_count = count_outline_chapters(outline)
    if summaries:
        summary_lines = [
            f"Chapter {summary['chapter_number']}: {summary['summary']}"
            for summary in summaries
        ]
        context = "\n\nPREVIOUS CHAPTERS SUMMARY:\n" + "\n".join(summary_lines)

    revision_context = f"\n\nEDITOR FEEDBACK:\n{editor_notes}" if editor_notes else ""
    ending_instruction = ""
    if _editor_requests_ending(editor_notes) or (
        planned_chapter_count and chapter_number >= planned_chapter_count
    ):
        ending_instruction = (
            "\n- This chapter should function as an ending. Resolve the main conflict, "
            "close the most important character arcs, and finish with a satisfying conclusion."
        )
    return f"""You are a professional novelist writing a book called "{title}".

FULL BOOK OUTLINE:
{outline}
{context}
NOW WRITE: Chapter {chapter_number} - {chapter_title}
{revision_context}

Instructions:
- Write a full, engaging chapter (minimum 800 words)
- Stay consistent with characters, plot, and tone from previous chapters
- Use vivid descriptions and natural dialogue
- End in a way that makes the reader want to continue
{ending_instruction}

Write the chapter now:"""


def build_summary_prompt(chapter_number: int, content: str) -> str:
    return f"""Summarize the following chapter in 3-5 sentences.
Focus on: key events, character developments, and important plot points.

Chapter {chapter_number}:
{content[:3000]}

Write only the summary:"""


def extract_chapter_title(outline_content: str, chapter_number: int) -> str:
    fallback_title = f"Chapter {chapter_number}"
    for line in outline_content.splitlines():
        if f"Chapter {chapter_number}" in line or f"**{chapter_number}." in line:
            clean_line = line.replace("**", "").replace("*", "").strip()
            if clean_line:
                return clean_line
    return fallback_title


def count_outline_chapters(outline_content: str) -> int:
    chapter_numbers = set()
    for line in outline_content.splitlines():
        clean_line = line.strip()
        if not clean_line:
            continue

        chapter_match = re.search(r"\bchapter\s+(\d+)\b", clean_line, flags=re.IGNORECASE)
        if chapter_match:
            chapter_numbers.add(int(chapter_match.group(1)))
            continue

        numbered_match = re.match(r"^\**\s*(\d+)\.\s+", clean_line)
        if numbered_match:
            chapter_numbers.add(int(numbered_match.group(1)))

    if not chapter_numbers:
        return 0

    highest = max(chapter_numbers)
    if all(number in chapter_numbers for number in range(1, highest + 1)):
        return highest
    return len(chapter_numbers)
