#!/usr/bin/env python3
"""
generate-tin-tuc.py — Sinh trang Tin tức/Sự kiện cho web Mường Cốc.

Nguồn: content/tin-tuc/*.md (YAML frontmatter: title, date, image, summary, body markdown).
Output:
  tin-tuc/index.html              # danh sách tin (mới nhất trước)
  tin-tuc/<slug>/index.html       # từng bài

Chỉ dùng thư viện chuẩn Python (chạy được trên Cloudflare Pages không cần cài thêm).
Nội dung tin VN-first (luôn hiển thị ở mọi ngôn ngữ). Khung trang (topbar/footer) đa ngữ như site.
Cách dùng: python3 scripts/generate-tin-tuc.py
"""
import html
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
SRC = BASE / "content" / "tin-tuc"
OUT = BASE / "tin-tuc"

TEL = "+84962029198"
TEL_SHOW = "0962 029 198"
FB_URL = "https://www.facebook.com/profile.php?id=61575640444733"
MAPS_URL = "https://www.google.com/maps/d/viewer?mid=1hNSY53YglDigLPa4YQzp13XTxxnTbHM"
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:'
         'ital,wght@0,500;0,600;0,700;1,500;1,600&family=Be+Vietnam+Pro:'
         'wght@300;400;500;600;700&display=swap" rel="stylesheet">')


def e(s: str) -> str:
    return html.escape(s or "", quote=True)


def slugify(s: str) -> str:
    s = s.lower().strip()
    vn = "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
    en = "aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd"
    s = s.translate(str.maketrans(vn, en))
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "bai-viet"


def parse_md(path: Path) -> dict:
    """Đọc 1 file .md có frontmatter YAML đơn giản (key: value) + body."""
    raw = path.read_text(encoding="utf-8")
    meta, body = {}, raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"').strip("'")
            body = parts[2].strip()
    meta["body"] = body
    meta.setdefault("title", path.stem)
    meta.setdefault("date", "")
    return meta


def asset_url(p: str) -> str:
    """Chuẩn hoá đường dẫn ảnh -> root-relative (chạy đúng ở mọi độ sâu trang)."""
    p = (p or "").strip()
    if not p:
        return ""
    if p.startswith(("http://", "https://", "/")):
        return p
    return "/" + p


def md_inline(t: str) -> str:
    t = e(t)
    # ảnh chèn trong bài: ![mô tả](đường-dẫn)
    t = re.sub(r"!\[(.*?)\]\(([^)]+)\)",
               lambda m: f'<img src="{asset_url(m.group(2))}" alt="{m.group(1)}" loading="lazy" style="max-width:100%;border-radius:10px;margin:10px 0">', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[(.+?)\]\((https?://[^)]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    return t


def md_to_html(body: str) -> str:
    """Markdown tối giản: ## h2, ### h3, - list, đoạn văn, **đậm**, [link](url)."""
    out, buf_list = [], []

    def flush_list():
        if buf_list:
            out.append("<ul>" + "".join(f"<li>{md_inline(x)}</li>" for x in buf_list) + "</ul>")
            buf_list.clear()

    for block in re.split(r"\n\s*\n", body.strip()):
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        if all(l.lstrip().startswith(("- ", "* ")) for l in lines):
            for l in lines:
                buf_list.append(l.lstrip()[2:])
            continue
        flush_list()
        if block.startswith("### "):
            out.append(f"<h3>{md_inline(block[4:])}</h3>")
        elif block.startswith("## "):
            out.append(f"<h2>{md_inline(block[3:])}</h2>")
        else:
            out.append("<p>" + "<br>".join(md_inline(l) for l in lines) + "</p>")
    flush_list()
    return "\n".join(out)


def chrome_head(title: str, desc: str, prefix: str, og_img: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:image" content="{asset_url(og_img)}">
{FONTS}
<link rel="stylesheet" href="{prefix}assets/css/site.css">
</head>
<body>
<div class="wrap">
<nav class="topbar">
  <a class="brand" href="{prefix}">
    <span class="logo-sm"><img src="{prefix}assets/img/logo-muong-coc.png" alt="Logo Mường Cốc"></span>
    <span class="brand-tx">Du lịch cộng đồng Mường Cốc</span>
  </a>
  <div class="lang-switch" role="group" aria-label="Ngôn ngữ">
    <button type="button" data-set-lang="vi" aria-pressed="true">VI</button>
    <button type="button" data-set-lang="en" aria-pressed="false">EN</button>
    <button type="button" data-set-lang="fr" aria-pressed="false">FR</button>
  </div>
</nav>
<nav class="quicknav" aria-label="Điều hướng nhanh">
  <a href="{prefix}">Trang chủ</a>
  <a href="{prefix}tin-tuc/">Tin tức</a>
  <a href="{prefix}gioi-thieu/">Giới thiệu</a>
  <a href="{prefix}#dat-tour" class="cta">Đặt tour</a>
</nav>"""


def chrome_foot(prefix: str) -> str:
    return f"""<footer>
  <div class="deco"><span></span><i></i><span></span></div>
  <div class="closing">Chạm Vào Bình Yên</div>
  <div class="ft-contact">
    <span>📞 Hotline: <a href="tel:{TEL}">{TEL_SHOW}</a></span>
    <span>🌐 Fanpage: <a href="{FB_URL}" target="_blank" rel="noopener">Du lịch cộng đồng Mường Cốc</a></span>
    <span>🗺️ <a href="{MAPS_URL}" target="_blank" rel="noopener">Bản đồ du lịch</a></span>
  </div>
  <div class="ft-line">Ban Điều Phối Du Lịch Cộng Đồng Mường Cốc<br>Tourism Hub Đồi Dùng · Xã Mỹ Đức · Hà Nội</div>
</footer>
</div>
<script src="{prefix}assets/js/site.js"></script>
</body>
</html>"""


def fmt_date(d: str) -> str:
    try:
        return datetime.strptime(d[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return d


def main():
    OUT.mkdir(exist_ok=True)
    posts = []
    for f in sorted(SRC.glob("*.md")):
        m = parse_md(f)
        m["slug"] = slugify(m.get("title", f.stem))
        posts.append(m)
    posts.sort(key=lambda x: x.get("date", ""), reverse=True)

    # Trang từng bài
    for p in posts:
        d = OUT / p["slug"]
        d.mkdir(exist_ok=True)
        img = p.get("image", "")
        hero = f'<img class="news-hero" src="{asset_url(img)}" alt="{e(p["title"])}">' if img else ""
        page = (chrome_head(f'{p["title"]} — Tin tức Mường Cốc', p.get("summary", ""), "../../", img or "assets/img/thung-canh.jpg")
                + f'<main class="news-article"><p class="news-date">{fmt_date(p.get("date",""))}</p>'
                + f'<h1>{e(p["title"])}</h1>{hero}<div class="news-body">{md_to_html(p["body"])}</div>'
                + '<p><a href="../">← Quay lại Tin tức</a></p></main>'
                + chrome_foot("../../"))
        (d / "index.html").write_text(page, encoding="utf-8")
        print(f"[OK] tin-tuc/{p['slug']}/index.html")

    # Trang danh sách
    cards = []
    for p in posts:
        img = p.get("image", "")
        thumb = f'<img src="{asset_url(img)}" alt="{e(p["title"])}">' if img else ""
        cards.append(f'<a class="news-card" href="{p["slug"]}/">{thumb}'
                     f'<div class="news-card-tx"><span class="news-date">{fmt_date(p.get("date",""))}</span>'
                     f'<h3>{e(p["title"])}</h3><p>{e(p.get("summary",""))}</p></div></a>')
    listing = (chrome_head("Tin tức & Sự kiện — Du lịch cộng đồng Mường Cốc",
                           "Tin tức, sự kiện, hoạt động mới nhất của điểm đến Du lịch cộng đồng Mường Cốc.",
                           "../", "assets/img/thung-canh.jpg")
               + '<header class="hero hero-news"><h1>Tin tức & Sự kiện</h1>'
               + '<p>Hoạt động, sự kiện và thông báo mới nhất của Mường Cốc</p></header>'
               + '<main class="news-grid">' + ("\n".join(cards) if cards else "<p>Chưa có bài viết.</p>") + '</main>'
               + chrome_foot("../"))
    (OUT / "index.html").write_text(listing, encoding="utf-8")
    print(f"[OK] tin-tuc/index.html  ({len(posts)} bài)")


if __name__ == "__main__":
    main()
