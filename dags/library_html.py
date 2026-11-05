"""Render the static HTML research library (step 7)."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def humanize_category(category: str) -> str:
    """'artificial_intelligence' -> 'Artificial Intelligence'."""
    return category.replace("_", " ").strip().title()


def build_library_html(papers: list[dict]) -> str:
    """
    Build the full HTML page for the library.

    Each paper is a dict with: filename, title, summary, keywords (list[str]), category.
    """
    # Copy so the caller's dicts are not modified
    papers = sorted((dict(p) for p in papers), key=lambda p: p["title"].lower())

    for paper in papers:
        paper["category_label"] = humanize_category(paper["category"])
        # Lowercased with .lower() to match the JS toLowerCase() used by the search box
        paper["search_text"] = " ".join(
            [paper["title"], paper["summary"], paper["filename"], paper["category_label"], *paper["keywords"]]
        ).lower()

    categories = sorted(
        {(p["category"], p["category_label"]) for p in papers},
        key=lambda c: c[1],
    )

    return _env.get_template("library.html.j2").render(papers=papers, categories=categories)


def write_library_html(papers: list[dict], output_dir: Path) -> Path:
    """Write index.html into output_dir (created if missing) and return its path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "index.html"
    output_path.write_text(build_library_html(papers), encoding="utf-8")
    return output_path
