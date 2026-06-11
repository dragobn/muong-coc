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
đổi lang + nhớ localStorage. FR dùng field _fr trong data/*.json (fallback EN
nếu thiếu); UI string cố định dịch trực tiếp qua t3(vi, en, fr).
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
MAP_MIDS: dict = json.loads((DATA / "map-mids.json").read_text(encoding="utf-8"))
MAPS_URL = f"https://www.google.com/maps/d/viewer?mid={MAP_MIDS['_tong']}"  # landing + footer


def maps_url_for(slug: str) -> str:
    """Trả URL Google My Maps cho slug; fallback sang _tong nếu không có."""
    mid = MAP_MIDS.get(slug) or MAP_MIDS["_tong"]
    return f"https://www.google.com/maps/d/viewer?mid={mid}"
FB_URL = "https://www.facebook.com/profile.php?id=61575640444733"
TEL = "+84962029198"
TEL_SHOW = "0962 029 198"
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
HL_ICONS = ["🌱", "🪕", "🤝", "🍃", "🪷", "🏔️", "🌊", "🎭", "🛶", "🌾"]
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
    return json.loads((DATA / "tours" / f"{slug}.json").read_text(encoding="utf-8"))


def t3(vi, en, fr=None):
    """3 span data-lang. FR dùng bản dịch riêng, fallback EN nếu thiếu."""
    en = en or vi
    fr = fr or en
    return (f'<span data-lang="vi">{e(vi)}</span>'
            f'<span data-lang="en">{e(en)}</span>'
            f'<span data-lang="fr">{e(fr)}</span>')


def block3(vi, en, fr=None, tag="div"):
    """3 block data-lang cho đoạn dài (chứa HTML con). FR fallback EN."""
    en = en or vi
    fr = fr or en
    return (f'<{tag} data-lang="vi">{vi}</{tag}>'
            f'<{tag} data-lang="en">{en}</{tag}>'
            f'<{tag} data-lang="fr">{fr}</{tag}>')


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
            f'{t3("← Trang chủ", "← Home", "← Accueil")}</a>') if with_home else ""
    brand_href = prefix or "./"
    return f'''<nav class="topbar">
  <a class="brand" href="{brand_href}">
    <span class="logo-sm"><img src="{prefix}assets/img/logo-muong-coc.png" alt="Logo Mường Cốc"></span>
    <span class="brand-tx">{t3("Du lịch cộng đồng Mường Cốc", "Muong Coc Community Tourism", "Tourisme communautaire de Mường Cốc")}</span>
  </a>
  {home}
  <div class="lang-switch" role="group" aria-label="Ngôn ngữ / Language">
    <button type="button" data-set-lang="vi" aria-pressed="true">VI</button>
    <button type="button" data-set-lang="en" aria-pressed="false">EN</button>
    <button type="button" data-set-lang="fr" aria-pressed="false">FR</button>
  </div>
</nav>'''


def fab():
    # Icon điện thoại = SVG trắng (fill currentColor=#fff) cho nổi trên nền xanh
    phone_svg = ('<svg class="ico" viewBox="0 0 24 24" width="24" height="24" '
                 'fill="currentColor" aria-hidden="true">'
                 '<path d="M6.62 10.79a15.53 15.53 0 0 0 6.59 6.59l2.2-2.2a1.02 1.02 0 0 1 '
                 '1.05-.25c1.16.38 2.41.59 3.7.59a1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 '
                 '3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.29.21 2.54.59 3.7a1.02 1.02 0 0 1-.25 '
                 '1.05l-2.2 2.04z"/></svg>')
    return f'''<div class="fab">
  <a class="fb" href="{FB_URL}" target="_blank" rel="noopener" aria-label="Fanpage Du lịch cộng đồng Mường Cốc">
    <span aria-hidden="true">f</span>
    <span class="tip">{t3("Fanpage Du lịch cộng đồng Mường Cốc", "Facebook Fanpage", "Page Facebook")}</span>
  </a>
  <a class="call" href="tel:{TEL}" aria-label="Gọi hotline {TEL_SHOW}">
    {phone_svg}
    <span class="tip">{t3("Gọi hotline " + TEL_SHOW, "Call " + TEL_SHOW, "Appeler " + TEL_SHOW)}</span>
  </a>
</div>'''


def footer(prefix):
    return f'''<footer>
  <div class="deco"><span></span><i></i><span></span></div>
  <div class="closing">{t3("Chạm Vào Bình Yên", "Touch the Stillness", "Toucher la Quiétude")}</div>
  <div class="ft-contact">
    <span>📞 {t3("Hotline", "Hotline", "Hotline")}: <a href="tel:{TEL}">{TEL_SHOW}</a></span>
    <span>🌐 Fanpage: <a href="{FB_URL}" target="_blank" rel="noopener">Du lịch cộng đồng Mường Cốc</a></span>
    <span>🗺️ <a href="{MAPS_URL}" target="_blank" rel="noopener">{t3("Bản đồ du lịch", "Tourism map", "Carte touristique")}</a></span>
  </div>
  <div class="ft-line">{t3("Ban Điều Phối Du Lịch Cộng Đồng Mường Cốc", "Muong Coc Community Tourism Board", "Comité de coordination du tourisme communautaire de Mường Cốc")}<br>
    Tourism Hub Đồi Dùng · {t3("Xã Mỹ Đức · Hà Nội", "My Duc Commune · Hanoi", "Commune de Mỹ Đức · Hanoï")}</div>
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

    # NAVIGATOR NHANH (sticky dưới header) — anchor cuộn mượt
    parts.append(f'''  <nav class="quicknav" aria-label="{e('Điều hướng nhanh / Quick navigation')}">
    <a href="gioi-thieu/">{t3("Giới thiệu", "Overview", "Aperçu")}</a>
    <a href="#cung-xe-dap">{t3("Cung đạp xe", "Cycling", "Vélo")}</a>
    <a href="#cung-tour">{t3("Cung tour", "Tours", "Circuits")}</a>
    <a href="#ho-so-diem-den">{t3("Hồ sơ điểm đến", "Destinations", "Destinations")}</a>
    <a href="tin-tuc/">{t3("Tin tức", "News", "Actualités")}</a>
    <a href="#dat-tour" class="cta">{t3("Đặt tour", "Book", "Réserver")}</a>
  </nav>''')

    # HERO
    parts.append(f'''  <header class="hero">
    <div class="hero-bg"><img src="assets/img/thung-canh.jpg" alt="Thung lũng Mường Cốc"></div>
    <div class="hero-top"><span class="logo-circle"><img src="assets/img/logo-muong-coc.png" alt="Logo Mường Cốc"></span></div>
    <div class="hero-body">
      <div class="hero-pre">{t3("Du lịch cộng đồng · Xã Mỹ Đức · Hà Nội", "Community Tourism · My Duc · Hanoi", "Tourisme communautaire · Commune de Mỹ Đức · Hanoï")}</div>
      <h1>{t3("Du lịch cộng đồng", "Community Tourism", "Tourisme communautaire")}<br>Mường Cốc<em>{t3("Chạm Vào Bình Yên", "Touch the Stillness", "Toucher la Quiétude")}</em></h1>
      <div class="hero-tag">{t3("Bản Mường — Bóng Núi — Hơi Thở Đất", "Muong Village — Mountain Shade — Breath of the Earth", "Village Mường — Ombre des Montagnes — Souffle de la Terre")}</div>
      <div class="hero-loc">🌿 {t3("DU LỊCH XANH · CAM KẾT 5 KHÔNG", "GREEN TOURISM · 5-NO PLEDGE", "TOURISME VERT · ENGAGEMENT DES 5 NON")}</div>
    </div>
    <div class="scroll-cue">↓</div>
  </header>''')

    # INTRO
    intro_vi = ('<p><span class="drop">M</span>ường Cốc nằm tại xã Mỹ Đức, Hà Nội — một bản Mường còn '
                'giữ nguyên nếp sống thường ngày giữa bóng núi, chùa cổ, vườn sim và những thung lũng '
                'chưa một mảnh bê tông. Mỗi trải nghiệm đều bước ra từ đời sống thật của bản.</p>'
                '<p>Mường Cốc theo đuổi du lịch xanh, hướng đến <b>net-zero</b>, với cam kết <b>5 KHÔNG</b> '
                '— bạn đến để lắng nghe, chứ không chỉ để xem.</p>')
    intro_en = ('<p><span class="drop">M</span>uong Coc lies in My Duc Commune, Hanoi — a Muong village '
                'still living its everyday rhythm among mountain shade, old pagodas, rose-myrtle gardens '
                'and valleys untouched by concrete. Every experience grows from real village life.</p>'
                '<p>Muong Coc pursues green tourism toward <b>net-zero</b>, with a <b>5-NO pledge</b> '
                '— you come to listen, not merely to watch.</p>')
    intro_fr = ('<p><span class="drop">M</span>ường Cốc se niche dans la commune de Mỹ Đức, à Hanoï — un '
                'village Mường qui garde encore son rythme quotidien parmi l\'ombre des montagnes, les '
                'pagodes anciennes, les jardins de myrte et des vallées que le béton n\'a jamais touchées. '
                'Chaque expérience naît de la vie réelle du village.</p>'
                '<p>Mường Cốc poursuit un tourisme vert vers le <b>net-zero</b>, avec un <b>engagement '
                'des 5 NON</b> — vous venez pour écouter, et non simplement pour regarder.</p>')
    five = [("01 · Không rác nhựa", "01 · No plastic waste", "01 · Aucun déchet plastique"),
            ("02 · Không bê tông hoá", "02 · No concrete sprawl", "02 · Aucune bétonisation"),
            ("03 · Không dàn dựng", "03 · No staged shows", "03 · Aucune mise en scène"),
            ("04 · Không dấu chân nặng", "04 · No heavy footprint", "04 · Aucune empreinte lourde"),
            ("05 · Không quên trồng cây", "05 · Always plant a tree", "05 · Toujours planter un arbre")]
    five_html = "".join(f'<span>{t3(v, en, fr)}</span>' for v, en, fr in five)
    parts.append(f'''  <section class="intro alt">
    <div class="kick">{t3("Về Mường Cốc", "About Muong Coc", "À propos de Mường Cốc")}</div>
    {block3(intro_vi, intro_en, intro_fr)}
    <div class="five-no">{five_html}</div>
    <a href="gioi-thieu/" style="display:flex;align-items:center;gap:14px;margin-top:20px;background:linear-gradient(135deg,var(--green),var(--green-dark));color:#fff;text-decoration:none;padding:16px 20px;border-radius:14px;box-shadow:var(--shadow);">
      <span style="font-size:1.7rem;line-height:1;">🌿</span>
      <span style="flex:1;line-height:1.25;min-width:0;">
        <b style="font-family:var(--serif);font-size:1.18rem;display:block;">{t3("Giới thiệu tổng quan", "Overview", "Aperçu général")}</b>
        <small style="opacity:.92;font-size:.82rem;">{t3("Vùng đất · văn hoá · ẩm thực · trải nghiệm · lời mời", "Land · culture · cuisine · experiences · invitation", "Terre · culture · gastronomie · expériences · invitation")}</small>
      </span>
      <span style="font-size:1.4rem;flex-shrink:0;">→</span>
    </a>
  </section>''')

    # CÁC CUNG — mỗi nhóm là <details> collapsible (nhóm xe đạp mở mặc định)
    GROUP_ANCHORS = ["cung-xe-dap", "cung-tour", "cung-trek"]
    parts.append(f'''  <section id="cac-cung">
    <div class="kick">{t3("19 hành trình trải nghiệm", "19 signature journeys", "19 itinéraires d'expérience")}</div>
    <h2 class="sec">{t3("Các cung ", "Experience ", "Itinéraires ")}<em>{t3("trải nghiệm", "routes", "d'expérience")}</em></h2>''')
    for gi, (icon, label, slugs) in enumerate(GROUPS):
        anchor = GROUP_ANCHORS[gi] if gi < len(GROUP_ANCHORS) else f"cung-grp-{gi}"
        open_attr = " open" if gi == 0 else ""  # nhóm xe đạp mở sẵn
        parts.append(f'''    <details class="grp-acc" id="{anchor}"{open_attr}>
      <summary class="grp">
        <span class="gi">{icon}</span>'''
                     f'''<span class="gt">{t3(label["vi"], label["en"], label.get("fr"))}</span>'''
                     f'''<span class="gc">{len(slugs)} {t3("cung", "routes", "itinéraires")}</span>'''
                     f'''<span class="gchev" aria-hidden="true">⌄</span>
      </summary>
      <div class="cung-list">''')
        for slug in slugs:
            d = load(slug)
            cov = COVERS.get(slug)
            thumb = cov if cov else "assets/img/thung-canh.jpg"
            ten = d.get("ten", slug)
            ten_en = d.get("ten_en", ten)
            ten_fr = d.get("ten_fr", ten_en)
            meta_vi = " · ".join(x for x in [d.get("thoi_luong", ""), d.get("gia", "")] if x)
            meta_en = " · ".join(x for x in [d.get("thoi_luong_en", d.get("thoi_luong", "")),
                                             d.get("gia_en", d.get("gia", ""))] if x)
            meta_fr = " · ".join(x for x in [d.get("thoi_luong_fr", d.get("thoi_luong_en", d.get("thoi_luong", ""))),
                                             d.get("gia_fr", d.get("gia_en", d.get("gia", "")))] if x)
            parts.append(
                f'''      <a class="cung" href="cung/{slug}/">'''
                f'''<img class="thumb" src="{thumb}" alt="{e(ten)}" loading="lazy">'''
                f'''<div class="body"><div class="nm">{t3(ten, ten_en, ten_fr)}</div>'''
                f'''<div class="st">{t3(meta_vi, meta_en, meta_fr)}</div></div>'''
                f'''<span class="arrow">→</span></a>''')
        parts.append("      </div>\n    </details>")
    parts.append("  </section>")

    # HỒ SƠ ĐIỂM ĐẾN (link tạm /poi/ — main bổ sung danh sách sau)
    parts.append(f'''  <section class="poi alt" id="ho-so-diem-den">
    <div class="kick">{t3("Khám phá sâu hơn", "Dig deeper", "Explorer en profondeur")}</div>
    <h2 class="sec">{t3("Hồ sơ ", "Destination ", "Fiches des ")}<em>{t3("điểm đến", "profiles", "destinations")}</em></h2>
    <div class="poi-list">
      <a class="poi-card" href="poi/"><span class="ic">🪷</span><span><span class="nm">{t3("Tất cả điểm đến", "All destinations", "Toutes les destinations")}</span><span class="ds">{t3("Hồ sơ điểm đến Mường Cốc", "Muong Coc destination profiles", "Fiches des destinations de Mường Cốc")}</span></span><span class="arrow">→</span></a>
    </div>
  </section>''')

    # MAP CTA
    parts.append(f'''  <section>
    <div class="kick center">{t3("Định hướng hành trình", "Plan your route", "Planifier votre itinéraire")}</div>
    <h2 class="sec" style="text-align:center;">{t3("Bản đồ ", "Tourism ", "Carte ")}<em>{t3("du lịch", "map", "touristique")}</em></h2>
    <a class="btn" href="{MAPS_URL}" target="_blank" rel="noopener"><span class="ic">🗺️</span><span>{t3("Bản đồ du lịch Mường Cốc", "Muong Coc tourism map", "Carte touristique de Mường Cốc")}<small>{t3("Google My Maps · tất cả điểm đến", "Google My Maps · all destinations", "Google My Maps · toutes les destinations")}</small></span></a>
  </section>''')

    # ĐẶT TOUR (khối liên hệ đặt tour)
    parts.append(f'''  <section class="alt book" id="dat-tour">
    <div class="kick center">{t3("Sẵn sàng lên đường", "Ready to go", "Prêt à partir")}</div>
    <h2 class="sec" style="text-align:center;">{t3("Đặt ", "Book your ", "Réserver votre ")}<em>{t3("tour", "tour", "circuit")}</em></h2>
    <p class="book-lead">{t3("Liên hệ Ban Điều Phối để chọn cung phù hợp, hỏi lịch khởi hành và báo giá theo nhóm.", "Contact the Coordination Board to pick a route, check departure dates and get a group quote.", "Contactez le Comité de coordination pour choisir un itinéraire, vérifier les dates de départ et obtenir un devis de groupe.")}</p>
    <div class="cta-stack">
      <a class="btn" href="tel:{TEL}"><span class="ic">📞</span><span>{t3("Gọi đặt tour", "Call to book", "Appeler pour réserver")}<small>{TEL_SHOW}</small></span></a>
      <a class="btn ghost" href="{FB_URL}" target="_blank" rel="noopener"><span class="ic">💬</span><span>{t3("Nhắn tin Fanpage", "Message on Fanpage", "Message sur la page")}<small>{t3("Du lịch cộng đồng Mường Cốc", "Muong Coc Community Tourism", "Tourisme communautaire de Mường Cốc")}</small></span></a>
    </div>
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
    ten_fr = d.get("ten_fr", ten_en)
    cover = COVERS.get(slug) or "assets/img/thung-canh.jpg"
    icon = LOAI_ICON.get(d.get("loai", ""), "🗺️")

    parts = [head(
        f"{ten} — Du lịch cộng đồng Mường Cốc",
        (d.get("intro", "") or "")[:155],
        prefix, cover, theme)]
    parts.append(topbar(prefix, with_home=True))

    # HERO + chips
    chips = []
    for vi_key, en_key, fr_key in [("thoi_luong", "thoi_luong_en", "thoi_luong_fr"),
                                   ("cu_ly", "cu_ly_en", "cu_ly_fr"),
                                   ("gia", "gia_en", "gia_fr"), ("quy_mo", "quy_mo", "quy_mo")]:
        v = d.get(vi_key)
        if v:
            ven = d.get(en_key, v)
            chips.append(f'<span>{t3(v, ven, d.get(fr_key, ven))}</span>')
    chips_html = "".join(chips)
    tag_en = d.get("tagline_en", d.get("tagline", ""))
    parts.append(f'''  <header class="hero compact">
    <div class="hero-bg"><img src="{prefix}{cover}" alt="{e(ten)}"></div>
    <div class="hero-body" style="padding-top:30px;">
      <div class="hero-pre">{icon} {t3("Cung trải nghiệm Mường Cốc", "Muong Coc experience route", "Itinéraire d'expérience de Mường Cốc")}</div>
      <h1 style="font-size:2.3rem;">{t3(ten, ten_en, ten_fr)}</h1>
      <div class="hero-tag">{t3(d.get("tagline", ""), tag_en, d.get("tagline_fr", tag_en))}</div>
      <div class="hero-chips">{chips_html}</div>
    </div>
  </header>''')

    # INTRO
    if d.get("intro"):
        intro_en = d.get("intro_en", d.get("intro"))
        intro_fr = d.get("intro_fr", intro_en)
        parts.append(f'''  <section class="intro alt">
    <div class="kick">{t3("Giới thiệu", "Overview", "Présentation")}</div>
    {block3("<p>" + e(d.get("intro")) + "</p>", "<p>" + e(intro_en) + "</p>", "<p>" + e(intro_fr) + "</p>", tag="div")}
  </section>''')

    # HIGHLIGHTS (lý do)
    hls = d.get("highlights", [])
    if hls:
        hls_en = d.get("highlights_en", hls)
        hls_fr = d.get("highlights_fr", hls_en)
        rows = []
        for i, h in enumerate(hls):
            hen = hls_en[i] if i < len(hls_en) else h
            hfr = hls_fr[i] if i < len(hls_fr) else hen
            ic = HL_ICONS[i % len(HL_ICONS)]
            rows.append(f'<div class="hl"><span class="hi">{ic}</span><span class="ht">{t3(h, hen, hfr)}</span></div>')
        parts.append(f'''  <section>
    <div class="kick">{t3("Vì sao nên đi", "Why go", "Pourquoi y aller")}</div>
    <h2 class="sec">{len(hls)} {t3("lý do", "reasons", "raisons")}</h2>
    <div class="hl-list">{"".join(rows)}</div>
  </section>''')

    # LỊCH TRÌNH (timeline) + nút hồ sơ điểm đến
    lt = d.get("lich_trinh", [])
    if lt:
        items = []
        for s in lt:
            diem = s.get("diem", "")
            diem_en = s.get("diem_en", diem)
            diem_fr = s.get("diem_fr", diem_en)
            mo = s.get("mo_ta", "")
            mo_en = s.get("mo_ta_en", mo)
            mo_fr = s.get("mo_ta_fr", mo_en)
            gio = s.get("gio_hoac_buoi", "")
            note = ""
            if s.get("luu_y"):
                ly_en = s.get("luu_y_en", s.get("luu_y"))
                note = f'<div class="tl-note">⚑ {t3(s.get("luu_y"), ly_en, s.get("luu_y_fr", ly_en))}</div>'
            # link hồ sơ điểm đến nếu điểm có ảnh (suy ra poi-slug)
            poi_btn = ""
            ps = poi_slug(img_for(diem) or "")
            if ps:
                poi_btn = (f'<a class="poi-link" href="{prefix}poi/{ps}/">'
                           f'{t3("Xem hồ sơ điểm đến →", "View destination profile →", "Voir la fiche de la destination →")}</a>')
            items.append(f'''      <div class="tl-item">
        <div class="tl-time">{e(gio)}</div>
        <div class="tl-name">{t3(diem, diem_en, diem_fr)}</div>
        <div class="tl-desc">{block3(e(mo), e(mo_en), e(mo_fr), tag="span")}</div>
        {note}{poi_btn}
      </div>''')
        parts.append(f'''  <section class="alt">
    <div class="kick">{t3("Lịch trình", "Itinerary", "Programme")}</div>
    <h2 class="sec">{t3("Hành trình ", "The ", "Le ")}<em>{t3("trong ngày", "journey", "parcours")}</em></h2>
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
            nm_fr = dd.get("ten_fr", nm_en)
            loai_vi = dd.get("loai", "")
            loai_en = dd.get("loai_en", loai_vi)
            loai_fr = dd.get("loai_fr", loai_en)
            desc = dd.get("mo_ta_ngan", "")
            desc_en = dd.get("mo_ta_ngan_en", desc)
            desc_fr = dd.get("mo_ta_ngan_fr", desc_en)
            ps = poi_slug(img_for(nm) or "")
            img = img_for(nm)
            img_html = f'<img src="{prefix}{img}" alt="{e(nm)}" loading="lazy">' if img else ""
            link = (f'<a class="poi-link" href="{prefix}poi/{ps}/">'
                    f'{t3("Xem hồ sơ điểm đến →", "View destination profile →", "Voir la fiche de la destination →")}</a>') if ps else ""
            tag = f'<div class="dtag">{t3(loai_vi, loai_en, loai_fr)}</div>' if loai_vi else ""
            cards.append(f'''      <div class="dest">{img_html}
        <div class="dbody">{tag}
          <div class="dname">{t3(nm, nm_en, nm_fr)}</div>
          <div class="ddesc">{block3(e(desc), e(desc_en), e(desc_fr), tag="span")}</div>
          {link}
        </div>
      </div>''')
        parts.append(f'''  <section>
    <div class="kick">{t3("Điểm đến nổi bật", "Featured stops", "Étapes marquantes")}</div>
    <h2 class="sec">{t3("Những điểm ", "Places you'll ", "Les lieux ")}<em>{t3("bạn sẽ qua", "discover", "à découvrir")}</em></h2>
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
        bg_fr = d.get("bao_gom_fr", bg_en)
        kbg_fr = d.get("khong_bao_gom_fr", kbg_en)
        bg_li = "".join(f'<li>{t3(x, bg_en[i] if i < len(bg_en) else x, bg_fr[i] if i < len(bg_fr) else (bg_en[i] if i < len(bg_en) else x))}</li>' for i, x in enumerate(bg))
        kbg_li = "".join(f'<li>{t3(x, kbg_en[i] if i < len(kbg_en) else x, kbg_fr[i] if i < len(kbg_fr) else (kbg_en[i] if i < len(kbg_en) else x))}</li>' for i, x in enumerate(kbg))
        parts.append(f'''  <section class="alt">
    <div class="kick">{t3("Chi phí", "What's included", "Tarifs")}</div>
    <h2 class="sec">{t3("Bao gồm ", "Included ", "Inclus ")}<em>{t3("& không", "& not", "& non inclus")}</em></h2>
    <div class="incl-grid">
      <div class="incl-box"><h3>{t3("Đã bao gồm", "Included", "Inclus")}</h3><ul>{bg_li}</ul></div>
      <div class="incl-box no"><h3>{t3("Không bao gồm", "Not included", "Non inclus")}</h3><ul>{kbg_li}</ul></div>
    </div>
  </section>''')

    # ADDON
    addons = d.get("addon", [])
    if addons:
        rows = []
        for a in addons:
            a_ten_en = a.get("ten_en", a.get("ten", ""))
            a_mo_en = a.get("mo_ta_en", a.get("mo_ta", ""))
            rows.append(f'''<div class="chip-card">
        <div class="ct">{t3(a.get("ten", ""), a_ten_en, a.get("ten_fr", a_ten_en))}</div>
        <div class="cd">{t3(a.get("mo_ta", ""), a_mo_en, a.get("mo_ta_fr", a_mo_en))}</div>
      </div>''')
        parts.append(f'''  <section>
    <div class="kick">{t3("Trải nghiệm thêm", "Add-ons", "Expériences en option")}</div>
    <h2 class="sec">{t3("Tuỳ chọn ", "Optional ", "Suppléments ")}<em>{t3("nâng cấp", "extras", "facultatifs")}</em></h2>
    <div class="chip-cards">{"".join(rows)}</div>
  </section>''')

    # ĐỐI TƯỢNG + LƯU Ý
    dts = d.get("doi_tuong", [])
    lys = d.get("luu_y", [])
    if dts or lys:
        dt_html = ""
        if dts:
            def _dt_tag(x):
                nhom_en = x.get("nhom_en", x.get("nhom", ""))
                return f'<span>{t3(x.get("nhom", ""), nhom_en, x.get("nhom_fr", nhom_en))}</span>'
            tags = "".join(_dt_tag(x) for x in dts)
            dt_html = (f'<div class="kick" style="margin-top:6px;">{t3("Phù hợp với", "Best for", "Idéal pour")}</div>'
                       f'<div class="tag-list">{tags}</div>')
        ly_html = ""
        if lys:
            notes = []
            for i, ly in enumerate(lys):
                ic = NOTE_ICONS[i % len(NOTE_ICONS)]
                td_en = ly.get("tieu_de_en", ly.get("tieu_de", ""))
                mo_en = ly.get("mo_ta_en", ly.get("mo_ta", ""))
                notes.append(f'''<div class="note"><span class="ni">{ic}</span><div class="nt">
          <b>{t3(ly.get("tieu_de", ""), td_en, ly.get("tieu_de_fr", td_en))}</b>
          <span>{t3(ly.get("mo_ta", ""), mo_en, ly.get("mo_ta_fr", mo_en))}</span>
        </div></div>''')
            ly_html = (f'<div class="kick" style="margin-top:22px;">{t3("Lưu ý", "Good to know", "Bon à savoir")}</div>'
                       f'<div class="note-list">{"".join(notes)}</div>')
        parts.append(f'''  <section class="alt">
    <h2 class="sec">{t3("Đối tượng ", "Who & ", "Public & ")}<em>{t3("& lưu ý", "notes", "remarques")}</em></h2>
    {dt_html}{ly_html}
  </section>''')

    # NET ZERO
    if d.get("net_zero"):
        nz_en = d.get("net_zero_en", d.get("net_zero"))
        parts.append(f'''  <section>
    <div class="netzero"><span class="ni">🌳</span><div class="nt">
      <b>{t3("Cam kết Net Zero", "Net-Zero pledge", "Engagement Net Zéro")}</b>
      <span>{t3(d.get("net_zero"), nz_en, d.get("net_zero_fr", nz_en))}</span>
    </div></div>
  </section>''')

    # CTA: bản đồ + brochure
    cung_map_url = maps_url_for(slug)
    brochure_pdf = CUNG / slug / "brochure.pdf"
    brochure_btn = ""
    if brochure_pdf.exists():
        brochure_btn = (f'<a class="btn ghost" href="../brochure.pdf"><span class="ic">📄</span>'
                        f'<span>{t3("Tải brochure PDF", "Download brochure PDF", "Télécharger la brochure PDF")}'
                        f'<small>{t3("Chương trình chi tiết 8 trang", "8-page full programme", "Programme détaillé de 8 pages")}</small></span></a>')
    parts.append(f'''  <section class="alt">
    <div class="kick center">{t3("Bắt đầu hành trình", "Start your journey", "Commencez votre voyage")}</div>
    <h2 class="sec" style="text-align:center;">{t3("Đặt cung ", "Book this ", "Réserver cet ")}<em>{t3("này", "route", "itinéraire")}</em></h2>
    <div class="cta-stack">
      <a class="btn" href="{cung_map_url}" target="_blank" rel="noopener"><span class="ic">🗺️</span><span>{t3("Mở bản đồ tuyến", "Open route map", "Ouvrir la carte de l'itinéraire")}<small>{t3("Google My Maps", "Google My Maps", "Google My Maps")}</small></span></a>
      {brochure_btn}
      <a class="btn ghost" href="tel:{TEL}"><span class="ic">📞</span><span>{t3("Gọi đặt cung", "Call to book", "Appeler pour réserver")}<small>{TEL_SHOW}</small></span></a>
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
            if (DATA / "tours" / f"{s}.json").exists():
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
