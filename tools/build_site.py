#!/usr/bin/env python3
"""Build the public Render bundle from the approved local task cards."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


RELEASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = RELEASE_DIR.parent
SOURCE_ROOT = PROJECT_DIR / "单词册、阅读册"
PUBLIC_DIR = RELEASE_DIR / "public"
DEFAULT_URL = "https://reach-higher-1a-1b-word-review.onrender.com"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Helvetica.ttc"),
        Path("/Library/Fonts/Arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size, index=0)
    return ImageFont.load_default()


def make_og_image(path: Path) -> None:
    width, height = 1200, 630
    image = Image.new("RGB", (width, height), "#113654")
    draw = ImageDraw.Draw(image)

    draw.ellipse((835, -210, 1355, 310), fill="#2D759F")
    draw.ellipse((-160, 420, 320, 900), fill="#1E5D84")
    draw.rounded_rectangle((70, 62, 1130, 568), radius=34, fill="#F8FBFD")

    # Book icon.
    draw.rounded_rectangle((858, 145, 1037, 345), radius=20, fill="#DCECF5")
    draw.polygon([(880, 175), (946, 190), (946, 320), (880, 305)], fill="#FFFFFF")
    draw.polygon([(946, 190), (1015, 172), (1015, 305), (946, 320)], fill="#FFFFFF")
    draw.line((946, 190, 946, 320), fill="#2F6F9F", width=5)
    draw.line((895, 216, 932, 224), fill="#D3A540", width=5)
    draw.line((961, 224, 1001, 214), fill="#D3A540", width=5)

    # Speaker icon.
    draw.rounded_rectangle((886, 372, 1007, 468), radius=28, fill="#FFF0CF")
    draw.polygon([(913, 405), (934, 405), (960, 386), (960, 452), (934, 433), (913, 433)], fill="#B0781C")
    draw.arc((946, 397, 986, 442), start=-62, end=62, fill="#B0781C", width=6)

    draw.text((126, 112), "REACH HIGHER", font=font(28, True), fill="#B0781C")
    draw.text((122, 184), "1A · 1B", font=font(74, True), fill="#163A5F")
    draw.text((126, 281), "WORD REVIEW", font=font(58, True), fill="#2F6F9F")
    draw.text((130, 385), "Listen  ·  Learn  ·  Practice", font=font(29), fill="#4E6273")
    draw.rounded_rectangle((128, 472, 526, 522), radius=25, fill="#E8F2F8")
    draw.text((151, 481), "16 STUDENT TASK CARDS", font=font(21, True), fill="#2F6F9F")
    image.save(path, format="PNG", optimize=True)


def meta_block(title: str, description: str, url: str) -> str:
    safe_title = html.escape(title, quote=True)
    safe_description = html.escape(description, quote=True)
    safe_url = html.escape(url, quote=True)
    site_root = url.split("/cards/", 1)[0].rstrip("/")
    image_url = html.escape(f"{site_root}/og-image.png", quote=True)
    return f"""<meta name="description" content="{safe_description}">
<link rel="canonical" href="{safe_url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="zh_CN">
<meta property="og:title" content="{safe_title}">
<meta property="og:description" content="{safe_description}">
<meta property="og:image" content="{image_url}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="{safe_url}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{safe_title}">
<meta name="twitter:description" content="{safe_description}">
<meta name="twitter:image" content="{image_url}">"""


def card_details(source: Path, level: str) -> tuple[int, str, str]:
    match = re.search(r"Unit (\d+) Weeks (1-2|3-4)", source.name)
    if not match:
        raise ValueError(f"Unrecognized task-card filename: {source.name}")
    unit = int(match.group(1))
    weeks_slug = match.group(2)
    weeks_display = weeks_slug.replace("-", "–")
    return unit, weeks_slug, weeks_display


def build_card(source: Path, level: str, base_url: str) -> dict[str, object]:
    unit, weeks_slug, weeks_display = card_details(source, level)
    slug = f"{level.lower()}-unit-{unit}-weeks-{weeks_slug}.html"
    card_url = f"{base_url}/cards/{slug}"
    title = f"Reach Higher {level} · Unit {unit} · Weeks {weeks_display} 单词任务卡"
    description = "听力任务 + 全部 Key Words 与 Challenge Words 四种互动复习。"
    text = source.read_text(encoding="utf-8")

    # Render publishes MP3 only; WAV masters remain in the local final archive.
    text = re.sub(r'<source src="[^\"]+\.wav" type="audio/wav">', "", text)
    text = text.replace("../../../音频/", f"../audio/{level.lower()}/")

    title_end = re.search(r"</title>", text)
    if not title_end:
        raise ValueError(f"Missing </title>: {source}")
    insertion = "\n" + meta_block(title, description, card_url)
    text = text[: title_end.end()] + insertion + text[title_end.end() :]

    home_style = (
        ".home-link{display:inline-flex;align-items:center;gap:7px;color:#fff;"
        "text-decoration:none;font-weight:800;padding:8px 12px;border:1px solid #ffffff66;"
        "border-radius:999px;background:#ffffff12}.home-link:hover{background:#ffffff22}"
        "html,body{overflow-x:hidden}.layout,.panel,.audio-card,.hero{min-width:0;max-width:100%}"
        ".hero h1,.hero .lede{overflow-wrap:anywhere}@media(max-width:580px){.hero h1{font-size:27px}}"
    )
    text = text.replace("</style>", home_style + "\n</style>", 1)
    text = text.replace(
        '<body><main class="wrap">',
        '<body><main class="wrap"><a class="home-link" href="../index.html">← 全部任务卡</a>',
        1,
    )

    output = PUBLIC_DIR / "cards" / slug
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")

    original_refs = re.findall(r'(?:src="|"audio":\s*")([^\"]+\.mp3)', source.read_text(encoding="utf-8"))
    for ref in sorted(set(original_refs)):
        marker = "../../../音频/"
        if marker not in ref:
            raise ValueError(f"Unexpected audio path {ref} in {source}")
        suffix = ref.split(marker, 1)[1]
        audio_source = SOURCE_ROOT / level / "音频" / suffix
        if not audio_source.exists():
            raise FileNotFoundError(audio_source)
        audio_output = PUBLIC_DIR / "audio" / level.lower() / suffix
        audio_output.parent.mkdir(parents=True, exist_ok=True)
        if not audio_output.exists():
            shutil.copy2(audio_source, audio_output)

    data_match = re.search(r'<script type="application/json" id="wordData">(.*?)</script>', text, re.S)
    if not data_match:
        raise ValueError(f"Missing wordData: {source}")
    words = json.loads(data_match.group(1))
    return {
        "level": level,
        "unit": unit,
        "weeks": weeks_display,
        "slug": slug,
        "href": f"cards/{slug}",
        "word_count": len(words),
    }


def build_index(cards: list[dict[str, object]], base_url: str) -> None:
    groups = []
    for level in ("1A", "1B"):
        items = [card for card in cards if card["level"] == level]
        buttons = "\n".join(
            f'''<a class="task" href="{card['href']}">
  <span class="unit">Unit {card['unit']}</span>
  <strong>Weeks {card['weeks']}</strong>
  <span>{card['word_count']} words · 开始学习 →</span>
</a>'''
            for card in items
        )
        groups.append(
            f'''<section class="level-section">
  <div class="section-head"><div><p class="kicker">Reach Higher</p><h2>{level}</h2></div><span>8 张任务卡</span></div>
  <div class="task-grid">{buttons}</div>
</section>'''
        )

    title = "Reach Higher 1A · 1B 单词任务卡"
    description = "学生在线单词任务卡：听力任务、单词发音和四种互动复习模式。"
    document = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
{meta_block(title, description, base_url + '/')}
<style>
:root{{--navy:#163a5f;--blue:#2f6f9f;--blue2:#e8f2f8;--gold:#b98428;--ink:#172331;--muted:#657587;--line:#d7e2e9;--paper:#fff;--bg:#edf3f7;font-family:"Hiragino Sans GB",Aptos,"Segoe UI",system-ui,sans-serif}}
*{{box-sizing:border-box}}body{{margin:0;color:var(--ink);background:linear-gradient(180deg,#143b60 0,#2d6d99 360px,var(--bg) 360px);min-height:100vh}}.wrap{{max-width:1060px;margin:auto;padding:34px 18px 70px}}.hero{{color:white;padding:20px 4px 38px;display:grid;grid-template-columns:1fr auto;gap:24px;align-items:center}}.eyebrow{{font-size:13px;font-weight:900;letter-spacing:.14em;color:#f2d18c}}h1{{font-size:clamp(34px,6vw,64px);line-height:1;margin:10px 0 14px}}.hero p{{font-size:17px;line-height:1.7;color:#e6eef4;max-width:680px;margin:0}}.hero-badge{{width:132px;height:132px;border-radius:28px;background:#ffffff19;border:1px solid #ffffff45;display:grid;place-items:center;font-size:56px}}.level-section{{background:#fffffffa;border:1px solid var(--line);box-shadow:0 18px 48px #102a3e1f;border-radius:20px;padding:22px;margin-bottom:18px}}.section-head{{display:flex;justify-content:space-between;align-items:end;gap:16px;margin-bottom:17px}}.kicker{{margin:0;color:var(--gold);font-size:12px;letter-spacing:.13em;font-weight:900;text-transform:uppercase}}h2{{font-size:38px;color:var(--navy);margin:2px 0 0}}.section-head>span{{font-size:13px;color:var(--muted);padding:6px 10px;background:var(--blue2);border-radius:999px}}.task-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:11px}}.task{{display:flex;min-height:136px;flex-direction:column;justify-content:center;text-decoration:none;border:1px solid var(--line);border-radius:14px;padding:17px;background:linear-gradient(180deg,#fff,#f9fbfc);transition:.15s transform,.15s border-color,.15s box-shadow}}.task:hover{{transform:translateY(-2px);border-color:var(--blue);box-shadow:0 10px 24px #1b4a6b17}}.task .unit{{font-size:12px;font-weight:900;color:var(--blue);letter-spacing:.08em;text-transform:uppercase}}.task strong{{font-size:19px;color:var(--navy);margin:8px 0 13px}}.task span:last-child{{font-size:13px;color:var(--muted)}}.note{{margin:28px 4px 0;color:#587083;font-size:13px;line-height:1.6;text-align:center}}@media(max-width:780px){{.task-grid{{grid-template-columns:1fr 1fr}}.hero-badge{{display:none}}}}@media(max-width:480px){{.task-grid{{grid-template-columns:1fr}}.wrap{{padding:20px 12px 48px}}.level-section{{padding:16px}}}}
</style>
</head>
<body><main class="wrap">
<header class="hero"><div><div class="eyebrow">VOCABULARY TASK CARDS</div><h1>Reach Higher<br>1A · 1B</h1><p>选择 Unit 和 Weeks，完成听力任务，再用 Word Card、Choose Meaning、Fill the Blank 和 Missed Words 复习全部单词。</p></div><div class="hero-badge" aria-hidden="true">🔊</div></header>
{''.join(groups)}
<p class="note">建议使用 Chrome、Safari 或微信内置浏览器打开；学习进度保存在当前设备的浏览器中。</p>
</main></body></html>'''
    (PUBLIC_DIR / "index.html").write_text(document, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL.rstrip("/"))
    args = parser.parse_args()
    base_url = args.url.rstrip("/")

    if PUBLIC_DIR.exists():
        shutil.rmtree(PUBLIC_DIR)
    PUBLIC_DIR.mkdir(parents=True)

    cards: list[dict[str, object]] = []
    for level in ("1A", "1B"):
        source_dir = SOURCE_ROOT / level / "单词册" / "任务卡"
        for source in sorted(source_dir.rglob("*.html")):
            cards.append(build_card(source, level, base_url))

    cards.sort(key=lambda item: (item["level"], item["unit"], item["weeks"]))
    build_index(cards, base_url)
    make_og_image(PUBLIC_DIR / "og-image.png")
    (PUBLIC_DIR / "404.html").write_text(
        '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        '<title>Task card not found</title><style>body{font-family:system-ui;text-align:center;padding:15vh 20px;color:#163a5f}a{color:#2f6f9f}</style>'
        '<h1>没有找到这张任务卡</h1><p><a href="/">返回全部任务卡</a></p>',
        encoding="utf-8",
    )

    audio_files = list((PUBLIC_DIR / "audio").rglob("*.mp3"))
    total_audio_bytes = sum(path.stat().st_size for path in audio_files)
    report = {
        "site_url": base_url,
        "cards": len(cards),
        "audio_files": len(audio_files),
        "audio_mb": round(total_audio_bytes / 1024 / 1024, 2),
        "levels": {level: sum(1 for card in cards if card["level"] == level) for level in ("1A", "1B")},
    }
    (RELEASE_DIR / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
