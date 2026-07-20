"""Import GRE lesson text and vocabulary from the saved Z-Library HTML export."""
from __future__ import annotations

import argparse
import json
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HTML = Path.home() / "Desktop" / "读故事记单词 新GRE词汇.html"
OUT_DIR = ROOT / "src" / "data" / "gre" / "content"

TITLE_RE = re.compile(
    r'<p class="x1">\s*<span class="no-style-override5">(\d+)\.\s([^<]+)</span>',
    re.I,
)
P_X3_RE = re.compile(r'<p class="x3">(.*?)</p>', re.S)
P_X2_RE = re.compile(r'<p class="x2">(.*?)</p>', re.S)
P_VOCAB_LINE_RE = re.compile(r'<p class="(x6|x8)">(.*?)</p>', re.S)
X4_RE = re.compile(r'<p class="x4">', re.I)
X5_RE = re.compile(r'<p class="x5">\s*难词注释', re.I)
PHONETIC_RE = re.compile(r"\[([^\]]+)\]")


def strip_tags(fragment: str) -> str:
    text = re.sub(r"<br[^>]*>", "", fragment, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize(text: str) -> str:
    text = text.replace("''", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text


def normalize_zh(text: str) -> str:
    text = normalize(text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[，。；：！？、（）「」])", "", text)
    text = re.sub(r"(?<=[，。；：！？、（）「」])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    return text


def parse_headword(fragment: str) -> tuple[str, str | None]:
    text = strip_tags(fragment)
    phonetic_match = PHONETIC_RE.search(text)
    word = text[: phonetic_match.start()].strip() if phonetic_match else text
    phonetic = phonetic_match.group(1).strip() if phonetic_match else None
    word = re.sub(r"\s+", " ", word).strip()
    return word, phonetic or None


def parse_vocabulary(section: str) -> list[dict]:
    x5 = X5_RE.search(section)
    if not x5:
        return []

    vocab_part = section[x5.end() :]
    entries: list[dict] = []
    current: dict | None = None

    for kind, fragment in P_VOCAB_LINE_RE.findall(vocab_part):
        if kind == "x6":
            word, phonetic = parse_headword(fragment)
            if not word:
                continue
            current = {"word": word, "phonetic": phonetic, "lines": []}
            entries.append(current)
            continue

        if current is None:
            continue

        line = normalize_zh(strip_tags(fragment))
        if line:
            current["lines"].append(line)

    return entries


def parse_lessons(html: str) -> list[dict]:
    matches = list(TITLE_RE.finditer(html))
    if not matches:
        raise ValueError("No lesson titles found in HTML")

    lessons: list[dict] = []
    for i, match in enumerate(matches):
        lesson_id = int(match.group(1))
        title_en = strip_tags(match.group(2))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        section = html[start:end]

        story_en = [normalize(strip_tags(p)) for p in P_X3_RE.findall(section)]
        story_en = [p for p in story_en if p]

        story_zh: list[str] = []
        x4 = X4_RE.search(section)
        if x4:
            zh_part = section[x4.start() :]
            x5 = X5_RE.search(zh_part)
            if x5:
                zh_part = zh_part[: x5.start()]
            story_zh = [normalize_zh(strip_tags(p)) for p in P_X2_RE.findall(zh_part)]
            story_zh = [p for p in story_zh if p and p != "难词注释"]

        vocabulary = parse_vocabulary(section)

        lessons.append(
            {
                "id": lesson_id,
                "title": title_en,
                "storyEn": story_en,
                "storyZh": story_zh,
                "vocabulary": vocabulary,
            }
        )

    return lessons


def resolve_html_path(path: Path | None = None) -> Path:
    if path is not None:
        candidate = path.resolve()
        if candidate.is_file():
            return candidate
        raise FileNotFoundError(f"HTML file not found: {candidate}")

    if DEFAULT_HTML.is_file():
        return DEFAULT_HTML.resolve()

    desktop = Path.home() / "Desktop"
    matches = sorted(desktop.glob("*GRE*.html"))
    if matches:
        return matches[0].resolve()

    raise FileNotFoundError(f"HTML file not found: {DEFAULT_HTML}")


def write_lessons(lessons: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for lesson in lessons:
        payload = {
            "storyEn": lesson["storyEn"],
            "storyZh": lesson["storyZh"],
            "vocabulary": lesson["vocabulary"],
        }
        out = OUT_DIR / f"{lesson['id']:03d}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import GRE stories from HTML export")
    parser.add_argument(
        "--html",
        type=Path,
        default=None,
        help="Path to saved HTML file",
    )
    args = parser.parse_args()

    try:
        html_path = resolve_html_path(args.html)
    except FileNotFoundError as err:
        print(str(err), file=sys.stderr)
        sys.exit(1)

    print(f"Reading {html_path} ...")
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    lessons = parse_lessons(html)

    missing_en = [l["id"] for l in lessons if not l["storyEn"]]
    missing_zh = [l["id"] for l in lessons if not l["storyZh"]]
    missing_vocab = [l["id"] for l in lessons if not l["vocabulary"]]

    write_lessons(lessons)

    vocab_count = sum(len(l["vocabulary"]) for l in lessons)
    print(f"Wrote {len(lessons)} lessons to {OUT_DIR}")
    print(f"  vocabulary entries: {vocab_count}")
    if missing_en:
        print(f"  missing English: {missing_en[:10]}{'...' if len(missing_en) > 10 else ''}")
    if missing_zh:
        print(f"  missing Chinese: {missing_zh[:10]}{'...' if len(missing_zh) > 10 else ''}")
    if missing_vocab:
        print(f"  lessons without vocab: {missing_vocab}")


if __name__ == "__main__":
    main()
