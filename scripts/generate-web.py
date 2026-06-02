#!/usr/bin/env python3
"""
generate-web.py — Sinh WEB CORE responsive cho điểm đến Mường Cốc.

Output (chỉ tạo các file dưới, KHÔNG đụng brochure/poster/data/kml/print):
  index.html                       # landing tổng (i18n VN/EN/FR)
  cung/{slug}/index.html           # 19 microsite chi tiết tour (i18n)

Dùng:
  python3 scripts/generate-web.py            # sinh landing + 19 microsite
  python3 scripts/generate-web.py vong-xe-xanh trek-roc-eo   # vài cung (không sinh landing)
  python3 scripts/generate-web.py --landing  # chỉ landing

Cơ chế i18n: mỗi đoạn text render 3 phiên bản <span/div data-lang="vi|en|fr">.
CSS (assets/css/site.css) ẩn/hiện theo <html lang>. JS (assets/js/site.js)
đổi lang + nhớ localStorage. FR tạm = bản EN (TODO dịch FR sau).
"""

import html
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BASE = SCRIPT_DIR.parent
DATA = BASE / "data"
CUNG = BASE / "cung"

# ---- hằng số dùng chung ----
MAPS_URL = "https://www.google.com/maps/d/viewer?mid=1hNSY53YglDigLPa4YQzp13XTxxnTbHM"
FB_URL = "https://www.facebook.com/profile.php?id=61575640444733"
TEL = "+84986103298"
TEL_SHOW = "0986 103 298"
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:'
         'ital,wght@0,500;0,600;0,700;1,500;1,600&family=Be+Vietnam+Pro:'
         'wght@300;400;500;600;700&display=swap" rel="stylesheet">')

# thứ tự ưu tiên cover (scenic → kiến trúc → nội thất) — giống brochure
COVER_PRIORITY = [
    "dam-sen-nguyet-farm", "ho-baiboo", "canh-dong-roc-eo", "thung-canh",
    "doi-hoa-bo-moi", "con-duong-tram", "vuon-sim-co", "dong-huong-tich",
    "chua-phu-coc", "tourism-hub-doi-dung", "dinh-phu-coc", "chua-tien",
    "den-cay-thoi", "den-mau-ai-nang", "hang-ho-den-quan-mai",
    "nha-tho-giao-xu-bac-son", "nha-san-ba-dien", "gio-nui-farmstay",
    "lamia-muong-coc", "bep-ruou-doi-ly", "co-la-muong", "ba-la-homestay",
    "nha-niem-nga", "nha-tho-ho-ong-che", "farm-ca-qua", "ban-moc-muong-coc",
    "doi-duoc-lieu-roc-eo", "homestay-ong-kien",
]
HL_ICONS = ["🌱", "🪕", "🤝", "🍃", "⛩️", "🏔️", "🌊", "🎭", "🛶", "🌾"]
NOTE_ICONS = ["🌧️", "💪", "🏛️", "🍶", "👘", "🚫", "🐝", "📌"]
LOAI_ICON = {"xe-dap": "🚲", "trek": "🥾", "tour": "🌾"}

# 19 cung theo nhóm (thứ tự hiển thị landing) — khớp slugs.md
GROUPS = [
    ("🚲", {"vi": "Cung đạp xe", "en": "Cycling routes", "fr": "Parcours à vélo"},
     ["vong-xe-xanh", "theo-dong-ai-nang", "dau-xua-muong-coc", "hon-muong-ho-baiboo",
      "ve-mien-di-san", "xanh-giua-long", "huong-dong-bo-moi", "nhip-song-bo-moi"]),
    ("🌾", {"vi": "Cung tour", "en": "Tour routes", "fr": "Circuits"},
     ["tour-1n-thien-nhien", "tour-1n-van-hoa-sen", "tour-2n-thien-nhien",
      "tour-2n-van-hoa-sen", "tour-3n-huong-tich", "tour-kn-quang-phu-cau",
      "tour-kn-chua-huong", "tour-kn-cuc-phuong", "tour-kn-mai-chau-pu-luong"]),
    ("🥾", {"vi": "Cung trek", "en": "Trekking routes", "fr": "Treks"},
     ["trek-roc-eo", "trek-xuyen-rung-huong-tich"]),
]
ALL_SLUGS = [s for _, _, lst in GROUPS for s in lst]

IMAGE_MAP = json.loads((DATA / "images.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def e(s):
    return html.escape(str(s or ""))


def poi_slug(path):
    parts = (path or "").split("/")
    return parts[parts.index("poi") + 1] if "poi" in parts else ""


def img_for(name):
    """Tra images.json theo đúng tên điểm → path ảnh (relative demo-site)."""
    return IMAGE_MAP.get(name)


def load(slug):
    return json.loads((DATA / f"{slug}.json").read_text(encoding="utf-8"))


def t3(vi, en):
    """3 span data-lang. FR tạm = EN."""
    en = en or vi
    return (f'<span data-lang="vi">{e(vi)}</span>'
            f'<span data-lang="en">{e(en)}</span>'
            f'<span data-lang="fr">{e(en)}</span>')


def block3(vi, en, tag="div"):
    """3 block data-lang cho đoạn dài (chứa HTML con)."""
    en = en or vi
    return (f'<{tag} data-lang="vi">{vi}</{tag}>'
            f'<{tag} data-lang="en">{en}</{tag}>'
            f'<{tag} data-lang="fr">{en}</{tag}>')


# ---- gán cover distinct cho 19 cung (greedy) ----
def assign_covers():
    rank = {"xe-dap": 0, "tour": 1, "trek": 2}

    def okey(s):
        try:
            lo = load(s).get("loai", "")
        except Exception:
            lo = ""
        return (0 if s == "vong-xe-xanh" else 1, rank.get(lo, 3), s)

    used, cover = set(), {}
    for s in sorted(ALL_SLUGS, key=okey):
        d = load(s)
        names = [x.get("ten", "") for x in d.get("diem_den", [])] + \
                [x.get("diem", "") for x in d.get("lich_trinh", [])]
        avail = {}
        for n in names:
            p = img_for(n)
            if p:
                sl = poi_slug(p)
                if sl and sl not in avail:
                    avail[sl] = p
        ch = next((p for p in COVER_PRIORITY if p in avail and p not in used), None)
        if not ch:
            ch = next((p for p in avail if p not in used), None)
        if not ch:
            ch = next((p for p in COVER_PRIORITY if p in avail), None) or \
                 (next(iter(avail)) if avail else None)
        cover[s] = avail.get(ch) if ch else None
        if ch:
            used.add(ch)
    return cover


COVERS = assign_covers()


# ---------------------------------------------------------------------------
# Khung dùng chung: header (topbar), FAB, footer
# ---------------------------------------------------------------------------
def topbar(prefix, with_home):
    """prefix = đường dẫn tới gốc site ('' cho landing, '../../' cho microsite)."""
    home = (f'<a class="home-link" href="{prefix or "./"}">'
            f'{t3("← Trang chủ", "← Home")}</a>') if with_home else ""
    brand_href = prefix or "./"
    return f'''<nav class="topbar">
  <a class="brand" href="{brand_href}">
    <span class="logo-sm"><img src="{prefix}assets/img/logo-muong-coc.png" alt="Logo Mường Cốc"></span>
    <span class="brand-tx">{t3("Du lịch cộng đồng Mường Cốc", "Muong Coc Community Tourism")}</span>
  </a>
  {home}
  <div class="lang-switch" role="group" aria-label="Ngôn ngữ / Language">
    <button type="button" data-set-lang="vi" aria-pressed="true">VI</button>
    <button type="button" data-set-lang="en" aria-pressed="false">EN</button>
    <button type="button" data-set-lang="fr" aria-pressed="false">FR</button>
  </div>
</nav>'''


def fab():
    return f'''<div class="fab">
  <a class="fb" href="{FB_URL}" target="_blank" rel="noopener" aria-label="Fanpage Du lịch cộng đồng Mường Cốc">
    <span aria-hidden="true">f</span>
    <span class="tip">{t3("Fanpage Du lịch cộng đồng Mường Cốc", "Facebook Fanpage")}</span>
  </a>
  <a class="call" href="tel:{TEL}" aria-label="Gọi hotline {TEL_SHOW}">
    <span aria-hidden="true">📞</span>
    <span class="tip">{t3("Gọi hotline " + TEL_SHOW, "Call " + TEL_SHOW)}</span>
  </a>
</div>'''


def footer(prefix):
    return f'''<footer>
  <div class="deco"><span></span><i></i><span></span></div>
  <div class="closing">{t3("Chạm Vào Bình Yên", "Touch the Stillness")}</div>
  <div class="ft-contact">
    <span>📞 {t3("Hotline", "Hotline")}: <a href="tel:{TEL}">{TEL_SHOW}</a></span>
    <span>🌐 Fanpage: <a href="{FB_URL}" target="_blank" rel="noopener">Du lịch cộng đồng Mường Cốc</a></span>
    <span>🗺️ <a href="{MAPS_URL}" target="_blank" rel="noopener">{t3("Bản đồ du lịch", "Tourism map")}</a></span>
  </div>
  <div class="ft-line">{t3("Ban Điều Phối Du Lịch Cộng Đồng Mường Cốc", "Muong Coc Community Tourism Board")}<br>
    Tourism Hub Đồi Dùng · {t3("Xã Mỹ Đức · Hà Nội", "My Duc Commune · Hanoi")}</div>
</footer>'''


def head(title, desc, prefix, og_img, theme=""):
    return f'''<!DOCTYPE html>
<html lang="vi"{(' class="theme-' + theme + '"') if theme else ""}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{prefix}{og_img}">
{FONTS}
<link rel="stylesheet" href="{prefix}assets/css/site.css">
</head>
<body>
<div class="wrap">'''


def tail(prefix):
    return (f'{footer(prefix)}\n</div>\n{fab()}\n'
            f'<script src="{prefix}assets/js/site.js"></script>\n</body>\n</html>')


# ---------------------------------------------------------------------------
# LANDING (index.html)
# ---------------------------------------------------------------------------
def render_landing():
    parts = [head(
        "Du lịch cộng đồng Mường Cốc — Chạm Vào Bình Yên",
        "Du lịch cộng đồng Mường Cốc, xã Mỹ Đức, Hà Nội — bản Mường, du lịch xanh 5 KHÔNG. "
        "Cung đạp xe, tour văn hoá, trek rừng nguyên sinh.",
        "", "assets/img/thung-canh.jpg")]
    parts.append(topbar("", with_home=False))

    # HERO
    parts.append(f'''  <header class="hero">
    <div class="hero-bg"><img src="assets/img/thung-canh.jpg" alt="Thung lũng Mường Cốc"></div>
    <div class="hero-top"><span class="logo-circle"><img src="assets/img/logo-muong-coc.png" alt="Logo Mường Cốc"></span></div>
    <div class="hero-body">
      <div class="hero-pre">{t3("Du lịch cộng đồng · Xã Mỹ Đức · Hà Nội", "Community Tourism · My Duc · Hanoi")}</div>
      <h1>{t3("Du lịch cộng đồng", "Community Tourism")}<br>Mường Cốc<em>{t3("Chạm Vào Bình Yên", "Touch the Stillness")}</em></h1>
      <div class="hero-tag">{t3("Bản Mường — Bóng Núi — Hơi Thở Đất", "Muong Village — Mountain Shade — Breath of the Earth")}</div>
      <div class="hero-loc">🌿 {t3("DU LỊCH XANH · CAM KẾT 5 KHÔNG", "GREEN TOURISM · 5-NO PLEDGE")}</div>
    </div>
    <div class="scroll-cue">↓</div>
  </header>''')

    # INTRO
    intro_vi = ('<p><span class="drop">M</span>ường Cốc nằm tại xã Mỹ Đức, Hà Nội — một bản Mường còn '
                'giữ nguyên nếp sống thường ngày giữa bóng núi, chùa cổ, vườn sim và những thung lũng '
                'chưa một mảnh bê tông. Mỗi trải nghiệm đều bước ra từ đời sống thật của bản.</p>'
                '<p>Mường Cốc theo đuổi du lịch xanh với cam kết <b>5 KHÔNG</b> — bạn đến để lắng nghe, '
                'chứ không chỉ để xem.</p>')
    intro_en = ('<p><span class="drop">M</span>uong Coc lies in My Duc Commune, Hanoi — a Muong village '
                'still living its everyday rhythm among mountain shade, old pagodas, rose-myrtle gardens '
                'and valleys untouched by concrete. Every experience grows from real village life.</p>'
                '<p>Muong Coc pursues green tourism with a <b>5-NO pledge</b> — you come to listen, '
                'not merely to watch.</p>')
    five = [("01 · Không rác nhựa", "01 · No plastic waste"),
            ("02 · Không bê tông hoá", "02 · No concrete sprawl"),
            ("03 · Không dàn dựng", "03 · No staged shows"),
            ("04 · Không dấu chân nặng", "04 · No heavy footprint"),
            ("05 · Không quên trồng cây", "05 · Always plant a tree")]
    five_html = "".join(f'<span>{t3(v, en)}</span>' for v, en in five)
    parts.append(f'''  <section class="intro alt">
    <div class="kick">{t3("Về Mường Cốc", "About Muong Coc")}</div>
    {block3(intro_vi, intro_en)}
    <div class="five-no">{five_html}</div>
  </section>''')

    # CÁC CUNG
    parts.append(f'''  <section>
    <div class="kick">{t3("19 hành trình trải nghiệm", "19 signature journeys")}</div>
    <h2 class="sec">{t3("Các cung ", "Experience ")}<em>{t3("trải nghiệm", "routes")}</em></h2>''')
    for icon, label, slugs in GROUPS:
        parts.append(f'''    <div class="grp"><span class="gi">{icon}</span>'''
                     f'''<span class="gt">{t3(label["vi"], label["en"])}</span>'''
                     f'''<span class="gc">{len(slugs)} {t3("cung", "routes")}</span></div>
    <div class="cung-list">''')
        for slug in slugs:
            d = load(slug)
            cov = COVERS.get(slug)
            thumb = cov if cov else "assets/img/thung-canh.jpg"
            ten = d.get("ten", slug)
            ten_en = d.get("ten_en", ten)
            meta_vi = " · ".join(x for x in [d.get("thoi_luong", ""), d.get("gia", "")] if x)
            meta_en = " · ".join(x for x in [d.get("thoi_luong_en", d.get("thoi_luong", "")),
                                             d.get("gia_en", d.get("gia", ""))] if x)
            parts.append(
                f'''      <a class="cung" href="cung/{slug}/">'''
                f'''<img class="thumb" src="{thumb}" alt="{e(ten)}" loading="lazy">'''
                f'''<div class="body"><div class="nm">{t3(ten, ten_en)}</div>'''
                f'''<div class="st">{t3(meta_vi, meta_en)}</div></div>'''
                f'''<span class="arrow">→</span></a>''')
        parts.append("    </div>")
    parts.append("  </section>")

    # HỒ SƠ ĐIỂM ĐẾN (link tạm /poi/ — main bổ sung danh sách sau)
    parts.append(f'''  <section class="poi alt">
    <div class="kick">{t3("Khám phá sâu hơn", "Dig deeper")}</div>
    <h2 class="sec">{t3("Hồ sơ ", "Destination ")}<em>{t3("điểm đến", "profiles")}</em></h2>
    <div class="poi-list">
      <a class="poi-card" href="poi/"><span class="ic">⛩️</span><span><span class="nm">{t3("Tất cả điểm đến", "All destinations")}</span><span class="ds">{t3("Hồ sơ điểm đến Mường Cốc", "Muong Coc destination profiles")}</span></span><span class="arrow">→</span></a>
    </div>
  </section>''')

    # MAP CTA
    parts.append(f'''  <section>
    <div class="kick center">{t3("Định hướng hành trình", "Plan your route")}</div>
    <h2 class="sec" style="text-align:center;">{t3("Bản đồ ", "Tourism ")}<em>{t3("du lịch", "map")}</em></h2>
    <a class="btn" href="{MAPS_URL}" target="_blank" rel="noopener"><span class="ic">🗺️</span><span>{t3("Bản đồ du lịch Mường Cốc", "Muong Coc tourism map")}<small>{t3("Google My Maps · tất cả điểm đến", "Google My Maps · all destinations")}</small></span></a>
  </section>''')

    parts.append(tail(""))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# MICROSITE cung/{slug}/index.html
# ---------------------------------------------------------------------------
def render_cung(slug):
    d = load(slug)
    theme = d.get("theme", "")
    prefix = "../../"
    ten = d.get("ten", slug)
    ten_en = d.get("ten_en", ten)
    cover = COVERS.get(slug) or "assets/img/thung-canh.jpg"
    icon = LOAI_ICON.get(d.get("loai", ""), "🗺️")

    parts = [head(
        f"{ten} — Du lịch cộng đồng Mường Cốc",
        (d.get("intro", "") or "")[:155],
        prefix, cover, theme)]
    parts.append(topbar(prefix, with_home=True))

    # HERO + chips
    chips = []
    for vi_key, en_key in [("thoi_luong", "thoi_luong_en"), ("cu_ly", "cu_ly_en"),
                           ("gia", "gia_en"), ("quy_mo", "quy_mo")]:
        v = d.get(vi_key)
        if v:
            chips.append(f'<span>{t3(v, d.get(en_key, v))}</span>')
    chips_html = "".join(chips)
    parts.append(f'''  <header class="hero compact">
    <div class="hero-bg"><img src="{prefix}{cover}" alt="{e(ten)}"></div>
    <div class="hero-body" style="padding-top:30px;">
      <div class="hero-pre">{icon} {t3("Cung trải nghiệm Mường Cốc", "Muong Coc experience route")}</div>
      <h1 style="font-size:2.3rem;">{t3(ten, ten_en)}</h1>
      <div class="hero-tag">{t3(d.get("tagline", ""), d.get("tagline_en", d.get("tagline", "")))}</div>
      <div class="hero-chips">{chips_html}</div>
    </div>
  </header>''')

    # INTRO
    if d.get("intro"):
        parts.append(f'''  <section class="intro alt">
    <div class="kick">{t3("Giới thiệu", "Overview")}</div>
    {block3("<p>" + e(d.get("intro")) + "</p>", "<p>" + e(d.get("intro_en", d.get("intro"))) + "</p>", tag="div")}
  </section>''')

    # HIGHLIGHTS (lý do)
    hls = d.get("highlights", [])
    if hls:
        hls_en = d.get("highlights_en", hls)
        rows = []
        for i, h in enumerate(hls):
            hen = hls_en[i] if i < len(hls_en) else h
            ic = HL_ICONS[i % len(HL_ICONS)]
            rows.append(f'<div class="hl"><span class="hi">{ic}</span><span class="ht">{t3(h, hen)}</span></div>')
        parts.append(f'''  <section>
    <div class="kick">{t3("Vì sao nên đi", "Why go")}</div>
    <h2 class="sec">{len(hls)} {t3("lý do", "reasons")}</h2>
    <div class="hl-list">{"".join(rows)}</div>
  </section>''')

    # LỊCH TRÌNH (timeline) + nút hồ sơ điểm đến
    lt = d.get("lich_trinh", [])
    if lt:
        items = []
        for s in lt:
            diem = s.get("diem", "")
            diem_en = s.get("diem_en", diem)
            mo = s.get("mo_ta", "")
            mo_en = s.get("mo_ta_en", mo)
            gio = s.get("gio_hoac_buoi", "")
            note = ""
            if s.get("luu_y"):
                note = f'<div class="tl-note">⚑ {t3(s.get("luu_y"), s.get("luu_y_en", s.get("luu_y")))}</div>'
            # link hồ sơ điểm đến nếu điểm có ảnh (suy ra poi-slug)
            poi_btn = ""
            ps = poi_slug(img_for(diem) or "")
            if ps:
                poi_btn = (f'<a class="poi-link" href="{prefix}poi/{ps}/">'
                           f'{t3("Xem hồ sơ điểm đến →", "View destination profile →")}</a>')
            items.append(f'''      <div class="tl-item">
        <div class="tl-time">{e(gio)}</div>
        <div class="tl-name">{t3(diem, diem_en)}</div>
        <div class="tl-desc">{block3(e(mo), e(mo_en), tag="span")}</div>
        {note}{poi_btn}
      </div>''')
        parts.append(f'''  <section class="alt">
    <div class="kick">{t3("Lịch trình", "Itinerary")}</div>
    <h2 class="sec">{t3("Hành trình ", "The ")}<em>{t3("trong ngày", "journey")}</em></h2>
    <div class="timeline">
{"".join(items)}
    </div>
  </section>''')

    # ĐIỂM ĐẾN NỔI BẬT
    dds = d.get("diem_den", [])
    if dds:
        cards = []
        for dd in dds:
            nm = dd.get("ten", "")
            nm_en = dd.get("ten_en", nm)
            loai_vi = dd.get("loai", "")
            loai_en = dd.get("loai_en", loai_vi)
            desc = dd.get("mo_ta_ngan", "")
            desc_en = dd.get("mo_ta_ngan_en", desc)
            ps = poi_slug(img_for(nm) or "")
            img = img_for(nm)
            img_html = f'<img src="{prefix}{img}" alt="{e(nm)}" loading="lazy">' if img else ""
            link = (f'<a class="poi-link" href="{prefix}poi/{ps}/">'
                    f'{t3("Xem hồ sơ điểm đến →", "View destination profile →")}</a>') if ps else ""
            tag = f'<div class="dtag">{t3(loai_vi, loai_en)}</div>' if loai_vi else ""
            cards.append(f'''      <div class="dest">{img_html}
        <div class="dbody">{tag}
          <div class="dname">{t3(nm, nm_en)}</div>
          <div class="ddesc">{block3(e(desc), e(desc_en), tag="span")}</div>
          {link}
        </div>
      </div>''')
        parts.append(f'''  <section>
    <div class="kick">{t3("Điểm đến nổi bật", "Featured stops")}</div>
    <h2 class="sec">{t3("Những điểm ", "Places you'll ")}<em>{t3("bạn sẽ qua", "discover")}</em></h2>
    <div class="dest-grid">
{"".join(cards)}
    </div>
  </section>''')

    # BAO GỒM / KHÔNG BAO GỒM
    bg = d.get("bao_gom", [])
    kbg = d.get("khong_bao_gom", [])
    if bg or kbg:
        bg_en = d.get("bao_gom_en", bg)
        kbg_en = d.get("khong_bao_gom_en", kbg)
        bg_li = "".join(f'<li>{t3(x, bg_en[i] if i < len(bg_en) else x)}</li>' for i, x in enumerate(bg))
        kbg_li = "".join(f'<li>{t3(x, kbg_en[i] if i < len(kbg_en) else x)}</li>' for i, x in enumerate(kbg))
        parts.append(f'''  <section class="alt">
    <div class="kick">{t3("Chi phí", "What's included")}</div>
    <h2 class="sec">{t3("Bao gồm ", "Included ")}<em>{t3("& không", "& not")}</em></h2>
    <div class="incl-grid">
      <div class="incl-box"><h3>{t3("Đã bao gồm", "Included")}</h3><ul>{bg_li}</ul></div>
      <div class="incl-box no"><h3>{t3("Không bao gồm", "Not included")}</h3><ul>{kbg_li}</ul></div>
    </div>
  </section>''')

    # ADDON
    addons = d.get("addon", [])
    if addons:
        rows = []
        for a in addons:
            rows.append(f'''<div class="chip-card">
        <div class="ct">{t3(a.get("ten", ""), a.get("ten_en", a.get("ten", "")))}</div>
        <div class="cd">{t3(a.get("mo_ta", ""), a.get("mo_ta_en", a.get("mo_ta", "")))}</div>
      </div>''')
        parts.append(f'''  <section>
    <div class="kick">{t3("Trải nghiệm thêm", "Add-ons")}</div>
    <h2 class="sec">{t3("Tuỳ chọn ", "Optional ")}<em>{t3("nâng cấp", "extras")}</em></h2>
    <div class="chip-cards">{"".join(rows)}</div>
  </section>''')

    # ĐỐI TƯỢNG + LƯU Ý
    dts = d.get("doi_tuong", [])
    lys = d.get("luu_y", [])
    if dts or lys:
        dt_html = ""
        if dts:
            tags = "".join(f'<span>{t3(x.get("nhom", ""), x.get("nhom_en", x.get("nhom", "")))}</span>' for x in dts)
            dt_html = (f'<div class="kick" style="margin-top:6px;">{t3("Phù hợp với", "Best for")}</div>'
                       f'<div class="tag-list">{tags}</div>')
        ly_html = ""
        if lys:
            notes = []
            for i, ly in enumerate(lys):
                ic = NOTE_ICONS[i % len(NOTE_ICONS)]
                notes.append(f'''<div class="note"><span class="ni">{ic}</span><div class="nt">
          <b>{t3(ly.get("tieu_de", ""), ly.get("tieu_de_en", ly.get("tieu_de", "")))}</b>
          <span>{t3(ly.get("mo_ta", ""), ly.get("mo_ta_en", ly.get("mo_ta", "")))}</span>
        </div></div>''')
            ly_html = (f'<div class="kick" style="margin-top:22px;">{t3("Lưu ý", "Good to know")}</div>'
                       f'<div class="note-list">{"".join(notes)}</div>')
        parts.append(f'''  <section class="alt">
    <h2 class="sec">{t3("Đối tượng ", "Who & ")}<em>{t3("& lưu ý", "notes")}</em></h2>
    {dt_html}{ly_html}
  </section>''')

    # NET ZERO
    if d.get("net_zero"):
        parts.append(f'''  <section>
    <div class="netzero"><span class="ni">🌳</span><div class="nt">
      <b>{t3("Cam kết Net Zero", "Net-Zero pledge")}</b>
      <span>{t3(d.get("net_zero"), d.get("net_zero_en", d.get("net_zero")))}</span>
    </div></div>
  </section>''')

    # CTA: bản đồ + brochure
    brochure_pdf = CUNG / slug / "brochure.pdf"
    brochure_btn = ""
    if brochure_pdf.exists():
        brochure_btn = (f'<a class="btn ghost" href="../brochure.pdf"><span class="ic">📄</span>'
                        f'<span>{t3("Tải brochure PDF", "Download brochure PDF")}'
                        f'<small>{t3("Chương trình chi tiết 8 trang", "8-page full programme")}</small></span></a>')
    parts.append(f'''  <section class="alt">
    <div class="kick center">{t3("Bắt đầu hành trình", "Start your journey")}</div>
    <h2 class="sec" style="text-align:center;">{t3("Đặt cung ", "Book this ")}<em>{t3("này", "route")}</em></h2>
    <div class="cta-stack">
      <a class="btn" href="{MAPS_URL}" target="_blank" rel="noopener"><span class="ic">🗺️</span><span>{t3("Mở bản đồ tuyến", "Open route map")}<small>{t3("Google My Maps", "Google My Maps")}</small></span></a>
      {brochure_btn}
      <a class="btn ghost" href="tel:{TEL}"><span class="ic">📞</span><span>{t3("Gọi đặt cung", "Call to book")}<small>{TEL_SHOW}</small></span></a>
    </div>
  </section>''')

    parts.append(tail(prefix))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
def write_cung(slug):
    out = CUNG / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_cung(slug), encoding="utf-8")
    print(f"[OK] {out.relative_to(BASE)}")


def write_landing():
    out = BASE / "index.html"
    out.write_text(render_landing(), encoding="utf-8")
    print(f"[OK] {out.relative_to(BASE)}")


def main(argv):
    if argv and argv[0] == "--landing":
        write_landing()
        return
    if argv:
        for s in argv:
            if (DATA / f"{s}.json").exists():
                write_cung(s)
            else:
                print(f"[SKIP] không có data/{s}.json")
        return
    # mặc định: landing + tất cả
    write_landing()
    for s in ALL_SLUGS:
        write_cung(s)
    print(f"\nXong: index.html + {len(ALL_SLUGS)} microsite.")


if __name__ == "__main__":
    main(sys.argv[1:])
