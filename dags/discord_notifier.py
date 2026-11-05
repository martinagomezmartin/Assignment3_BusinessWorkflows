"""Send Discord webhook notifications for newly processed papers (step 8)."""

import time

import requests

from library_html import humanize_category

# Discord limits: https://discord.com/developers/docs/resources/message#embed-object-embed-limits
MAX_EMBEDS_PER_MESSAGE = 10
MAX_EMBED_CHARS_PER_MESSAGE = 6000
MAX_TITLE_LEN = 256
MAX_FIELD_VALUE_LEN = 1024
SUMMARY_PREVIEW_LEN = 350

CATEGORY_COLORS = {
    "artificial_intelligence": 0x8E44AD,
    "software_engineering": 0x2E86C1,
    "computer_systems": 0x17A589,
    "data_management": 0xD68910,
    "cybersecurity": 0xC0392B,
    "human_computer_interaction": 0xD4AC0D,
    "theoretical_computer_science": 0x566573,
}
DEFAULT_COLOR = 0x5865F2  # Discord blurple


def _truncate(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _paper_embed(paper: dict) -> dict:
    keywords = ", ".join(paper["keywords"]) or "—"
    return {
        "title": _truncate(paper["title"], MAX_TITLE_LEN),
        "description": _truncate(paper["summary"], SUMMARY_PREVIEW_LEN),
        "color": CATEGORY_COLORS.get(paper["category"], DEFAULT_COLOR),
        "fields": [
            {"name": "Category", "value": humanize_category(paper["category"]), "inline": True},
            {"name": "File", "value": _truncate(paper["filename"], MAX_FIELD_VALUE_LEN), "inline": True},
            {"name": "Keywords", "value": _truncate(keywords, MAX_FIELD_VALUE_LEN), "inline": False},
        ],
    }


def _embed_chars(embed: dict) -> int:
    """Characters that count towards Discord's 6000-per-message embed limit."""
    total = len(embed["title"]) + len(embed["description"])
    for field in embed["fields"]:
        total += len(field["name"]) + len(field["value"])
    return total


def build_discord_payloads(papers: list[dict]) -> list[dict]:
    """
    Build the webhook payloads (one per Discord message) announcing the given papers.

    Each paper is a dict with: filename, title, summary, keywords (list[str]), category.
    One embed per paper; papers are split across several messages when needed to stay
    within Discord's per-message limits.
    """
    if not papers:
        return []

    batches: list[list[dict]] = [[]]
    batch_chars = 0
    for paper in papers:
        embed = _paper_embed(paper)
        chars = _embed_chars(embed)
        current = batches[-1]
        if current and (
            len(current) >= MAX_EMBEDS_PER_MESSAGE or batch_chars + chars > MAX_EMBED_CHARS_PER_MESSAGE
        ):
            batches.append([])
            batch_chars = 0
        batches[-1].append(embed)
        batch_chars += chars

    count = len(papers)
    header = f"📚 {count} new paper{'' if count == 1 else 's'} added to the research library"
    payloads = []
    for i, embeds in enumerate(batches):
        payload = {"embeds": embeds}
        if i == 0:
            payload["content"] = header
        payloads.append(payload)
    return payloads


def _post(webhook_url: str, payload: dict) -> None:
    response = requests.post(webhook_url, json=payload, timeout=10)
    if response.status_code == 429:
        # Rate limited: wait the time Discord asks for, then retry once
        retry_after = float(response.json().get("retry_after", 1))
        time.sleep(retry_after)
        response = requests.post(webhook_url, json=payload, timeout=10)
    response.raise_for_status()


def send_discord_notification(webhook_url: str, papers: list[dict]) -> int:
    """
    Post the notification for the given papers to a Discord webhook.

    Raises requests.HTTPError if Discord rejects a message, so the calling Airflow task
    fails and the papers are not marked as reported. Returns the number of messages sent.
    """
    payloads = build_discord_payloads(papers)
    for payload in payloads:
        _post(webhook_url, payload)
    return len(payloads)
