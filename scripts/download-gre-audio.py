"""Import or download GRE lesson MP3 files into public/audio/.



Remote hosts (hxen / tingclass CDN) are mostly offline. Recommended workflow:



  1. Download the 163-MP3 pack (e.g. jwbl.com Baidu Pan) and extract locally.

  2. Run: python scripts/download-gre-audio.py --source-dir "D:/path/to/mp3"

  3. Or try archived copies: python scripts/download-gre-audio.py --remote --wayback

"""

from __future__ import annotations



import argparse

import json

import re

import shutil

import ssl

import subprocess

import sys

import time

import urllib.error

import urllib.request

from pathlib import Path



ROOT = Path(__file__).resolve().parents[1]

AUDIO_DIR = ROOT / "public" / "audio"

LESSONS_PATH = ROOT / "src" / "data" / "gre" / "lessons.json"

MANIFEST_PATH = AUDIO_DIR / "manifest.json"



USER_AGENT = (

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "

    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

)



TINGCLASS_CDN = "https://online2.tingclass.net/lesson/shi0529/0008/8582/{unit}.mp3"

HXEN_CDN = "http://f1.hxen.com/m2/tingli/gre/cihui/{unit}.mp3"

HXEN_LIST = "http://bbs.hxen.com/englishlistening/gre/humin/"



# Matches: 001.mp3, 胡敏... 001 Title.mp3, Unit001.mp3, lesson-001.mp3

ID_PATTERNS = [

    re.compile(r"(?:^|[^\d])(\d{1,3})(?:[^\d]|$)", re.I),

    re.compile(r"unit\s*(\d{1,3})", re.I),

    re.compile(r"第\s*(\d{1,3})\s*[课篇]", re.I),

]





def ssl_context() -> ssl.SSLContext:

    ctx = ssl.create_default_context()

    ctx.check_hostname = False

    ctx.verify_mode = ssl.CERT_NONE

    return ctx





def fetch(url: str, timeout: int = 20, method: str = "GET") -> bytes | None:

    req = urllib.request.Request(

        url,

        method=method,

        headers={"User-Agent": USER_AGENT, "Referer": "https://www.tingclass.net/"},

    )

    try:

        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp:

            if resp.status != 200:

                return None

            if method == "HEAD":

                return b"ok"

            return resp.read()

    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):

        return None





def is_valid_mp3(path: Path, min_bytes: int = 1000) -> bool:

    return path.is_file() and path.stat().st_size >= min_bytes





def lesson_id_from_name(name: str) -> int | None:

    stem = Path(name).stem

    for pattern in ID_PATTERNS:

        m = pattern.search(stem)

        if m:

            num = int(m.group(1))

            if 1 <= num <= 200:

                return num

    return None





def discover_source_files(source_dir: Path) -> dict[int, Path]:

    found: dict[int, Path] = {}

    for path in sorted(source_dir.rglob("*.mp3")):

        lesson_id = lesson_id_from_name(path.name)

        if lesson_id is None:

            continue

        if lesson_id not in found or len(path.name) < len(found[lesson_id].name):

            found[lesson_id] = path

    return found





def extract_archive(archive: Path, dest: Path) -> bool:

    dest.mkdir(parents=True, exist_ok=True)

    suffix = archive.suffix.lower()



    if suffix == ".zip":

        import zipfile



        with zipfile.ZipFile(archive) as zf:

            zf.extractall(dest)

        return True



    for tool, args in [

        ("7z", ["x", str(archive), f"-o{dest}", "-y"]),

        ("winrar", ["x", "-y", str(archive), str(dest)]),

    ]:

        exe = shutil.which(tool)

        if not exe:

            continue

        try:

            subprocess.run([exe, *args], check=True, capture_output=True)

            return True

        except (subprocess.CalledProcessError, OSError):

            continue



    print(f"Cannot extract {archive}. Install 7-Zip or extract manually.", file=sys.stderr)

    return False





def import_file(lesson_id: int, src: Path) -> bool:

    out = AUDIO_DIR / f"{lesson_id:03d}.mp3"

    if is_valid_mp3(out):

        return True

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src, out)

    return is_valid_mp3(out)





def remote_candidates(lesson_id: int) -> list[str]:

    urls = [TINGCLASS_CDN.format(unit=lesson_id), HXEN_CDN.format(unit=lesson_id)]

    for ts in ("2020", "2019", "2018"):

        urls.append(f"https://web.archive.org/web/{ts}/{HXEN_CDN.format(unit=lesson_id)}")

        urls.append(

            f"https://web.archive.org/web/{ts}/{TINGCLASS_CDN.format(unit=lesson_id)}"

        )

    return urls





def download_remote(lesson_id: int, use_wayback: bool) -> tuple[bool, str | None]:

    candidates = remote_candidates(lesson_id) if use_wayback else [

        TINGCLASS_CDN.format(unit=lesson_id),

        HXEN_CDN.format(unit=lesson_id),

    ]

    for url in candidates:

        data = fetch(url, timeout=25 if "archive.org" in url else 12)

        if data and len(data) > 1000 and data[:3] in (b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):

            out = AUDIO_DIR / f"{lesson_id:03d}.mp3"

            AUDIO_DIR.mkdir(parents=True, exist_ok=True)

            out.write_bytes(data)

            return True, url

    return False, None





def scrape_hxen_pages(max_pages: int = 7) -> dict[int, str]:

    found: dict[int, str] = {}

    for i in range(1, max_pages + 1):

        suffix = "" if i == 1 else f"index_{i}.html"

        page_url = HXEN_LIST + suffix

        html_bytes = fetch(page_url)

        if not html_bytes:

            continue

        html = html_bytes.decode("gb2312", errors="ignore")

        links = re.findall(r'href="(/englishlistening/gre/humin/[^"]+\.html)"', html)

        for link in links:

            page = fetch("http://bbs.hxen.com" + link)

            if not page:

                continue

            text = page.decode("gb2312", errors="ignore")

            mp3s = re.findall(r"(http://[^\"'\s]+\.mp3)", text, flags=re.I)

            unit_match = re.search(r"Unit(\d+)", text, flags=re.I)

            if mp3s and unit_match:

                found[int(unit_match.group(1))] = mp3s[0]

    return found





def write_manifest(

    lesson_ids: list[int],

    downloaded: list[int],

    missing: list[int],

    sources: dict[str, str],

    mode: str,

) -> None:

    manifest = {

        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),

        "mode": mode,

        "total": len(lesson_ids),

        "downloaded": sorted(downloaded),

        "missing": sorted(missing),

        "sources": sources,

        "downloadedCount": len(downloaded),

        "missingCount": len(missing),

    }

    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")





def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(description="Import GRE lesson MP3 files into public/audio/")

    parser.add_argument("--source-dir", type=Path, help="Folder with extracted MP3 files")

    parser.add_argument("--archive", type=Path, help="ZIP/RAR archive to extract first")

    parser.add_argument("--extract-to", type=Path, help="Temp folder for archive extraction")

    parser.add_argument("--remote", action="store_true", help="Try remote / Wayback download")

    parser.add_argument("--wayback", action="store_true", help="Include archive.org when using --remote")

    parser.add_argument("--from", dest="from_id", type=int, default=1, help="Start lesson id")

    parser.add_argument("--to", dest="to_id", type=int, default=200, help="End lesson id")

    return parser.parse_args()





def main() -> None:

    args = parse_args()

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)



    lessons = json.loads(LESSONS_PATH.read_text(encoding="utf-8"))

    all_ids = [l["id"] for l in lessons]

    lesson_ids = [i for i in all_ids if args.from_id <= i <= args.to_id]



    source_dir = args.source_dir

    mode = "local"



    if args.archive:

        extract_dir = args.extract_to or (ROOT / ".tmp-gre-audio")

        if extract_dir.exists():

            shutil.rmtree(extract_dir)

        if not extract_archive(args.archive.resolve(), extract_dir):

            sys.exit(1)

        source_dir = extract_dir

        mode = "archive"



    downloaded: list[int] = []

    missing: list[int] = []

    sources: dict[str, str] = {}



    if source_dir:

        source_dir = source_dir.resolve()

        if not source_dir.is_dir():

            print(f"Source directory not found: {source_dir}", file=sys.stderr)

            sys.exit(1)



        mapping = discover_source_files(source_dir)

        print(f"Found {len(mapping)} MP3 files in {source_dir}")



        for lesson_id in lesson_ids:

            out = AUDIO_DIR / f"{lesson_id:03d}.mp3"

            if is_valid_mp3(out):

                downloaded.append(lesson_id)

                continue

            src = mapping.get(lesson_id)

            if src and import_file(lesson_id, src):

                downloaded.append(lesson_id)

                sources[f"{lesson_id:03d}"] = str(src)

                print(f"[COPY] {lesson_id:03d} <- {src.name}")

            else:

                missing.append(lesson_id)

                print(f"[MISS] {lesson_id:03d} (no matching source file)")



    elif args.remote:

        mode = "remote-wayback" if args.wayback else "remote"

        print("Trying remote sources (most legacy hosts are offline)...")

        scraped = scrape_hxen_pages()

        print(f"Scraped {len(scraped)} hxen page links")



        for lesson_id in lesson_ids:

            out = AUDIO_DIR / f"{lesson_id:03d}.mp3"

            if is_valid_mp3(out):

                downloaded.append(lesson_id)

                continue



            ok = False

            url_used: str | None = None



            hxen_url = scraped.get(lesson_id)

            if hxen_url:

                data = fetch(hxen_url, timeout=20)

                if data and len(data) > 1000:

                    out.write_bytes(data)

                    ok = True

                    url_used = hxen_url



            if not ok:

                ok, url_used = download_remote(lesson_id, use_wayback=args.wayback)



            if ok:

                downloaded.append(lesson_id)

                if url_used:

                    sources[f"{lesson_id:03d}"] = url_used

                print(f"[GET]  {lesson_id:03d} <- {url_used}")

            else:

                missing.append(lesson_id)

                print(f"[MISS] {lesson_id:03d}")

            time.sleep(0.1)



    else:

        print("Scanning existing public/audio/ ...")

        for lesson_id in lesson_ids:

            out = AUDIO_DIR / f"{lesson_id:03d}.mp3"

            if is_valid_mp3(out):

                downloaded.append(lesson_id)

            else:

                missing.append(lesson_id)



    write_manifest(lesson_ids, downloaded, missing, sources, mode)



    print(f"\nDone: {len(downloaded)}/{len(lesson_ids)} files in {AUDIO_DIR}")

    print(f"Manifest: {MANIFEST_PATH}")



    if missing:

        print("\nMissing audio files. Options:")

        print("  1. Download pack from http://www.jwbl.com/html/17/7493.html (Baidu Pan, 163 MP3)")

        print("  2. Extract book CD / RAR, then run:")

        print('     python scripts/download-gre-audio.py --source-dir "PATH/TO/MP3"')

        print("  3. Or: python scripts/download-gre-audio.py --archive file.rar --extract-to .tmp-gre-audio")





if __name__ == "__main__":

    main()


