#!/usr/bin/env python3
"""
generate-poi.py — Sinh WEB HỒ SƠ ĐIỂM ĐẾN responsive cho Mường Cốc.

Output (CHỈ tạo dưới đây — KHÔNG đụng landing index.html / cung/ / data/ /
brochure / kml / print):
  poi/index.html              # trang danh sách tất cả điểm đến (i18n)
  poi/{slug}/index.html       # 1 page / điểm đến (i18n VN/EN/FR)

Nguồn nội dung: file .md trong
  ../260601-1809-cung-a-tour-doc/ho-so-diem-den/
  ../260601-1809-cung-a-tour-doc/ho-so-diem-den-dot-2/
(parser 7 mục: thông tin chung / giới thiệu / giá trị / dịch vụ /
trải nghiệm / phục vụ khách / định hướng).

SLUG khớp poi-slug trong data/images.json (qua HOSO_TO_POISLUG) để link
"Xem hồ sơ điểm đến" từ microsite/cẩm nang resolve đúng. Điểm không có
ảnh riêng dùng ảnh mặc định theo loại.

Khung dùng chung: tái dùng assets/css/site.css + assets/js/site.js,
header/footer/FAB GIỐNG landing. CSS riêng cho POI nhúng trong <head>.

Dùng:
  python3 scripts/generate-poi.py            # sinh index + tất cả page
  python3 scripts/generate-poi.py chua-phu-coc gio-nui-farmstay  # vài slug
  python3 scripts/generate-poi.py --index    # chỉ trang danh sách
"""

import html
import json
import re
import sys
import unicodedata
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BASE = SCRIPT_DIR.parent
DATA = BASE / "data"
POI_OUT = BASE / "poi"
HOSO_DIRS = [
    BASE.parent.parent / "260601-1809-cung-a-tour-doc" / "ho-so-diem-den",
    BASE.parent.parent / "260601-1809-cung-a-tour-doc" / "ho-so-diem-den-dot-2",
]
IMG_POI = BASE / "assets" / "img" / "poi"

# ---- hằng số dùng chung (khớp generate-web.py) ----
MAPS_URL = "https://www.google.com/maps/d/viewer?mid=1hNSY53YglDigLPa4YQzp13XTxxnTbHM"
FB_URL = "https://www.facebook.com/profile.php?id=61575640444733"
TEL = "+84986103298"
TEL_SHOW = "0986 103 298"
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:'
         'ital,wght@0,500;0,600;0,700;1,500;1,600&family=Be+Vietnam+Pro:'
         'wght@300;400;500;600;700&display=swap" rel="stylesheet">')

IMAGE_MAP = json.loads((DATA / "images.json").read_text(encoding="utf-8"))
COORDS = json.loads((DATA / "master-poi-coords.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------------------
# MAP: filename hoso (không prefix hoso-NN-) -> poi-slug ảnh trong images.json
# Quyết định slug page = poi-slug ảnh nếu map được (để cung/cẩm nang resolve),
# ngược lại = slug suy ra từ tên file. Curated tay cho chuẩn xác.
# ---------------------------------------------------------------------------
HOSO_TO_POISLUG = {
    "chua-phu-coc": "chua-phu-coc",
    "den-cay-thoi": "den-cay-thoi",
    "chua-dinh-long-dinh-long-tu": "chua-dinh-long",
    "den-mau-thuong-thien-den-ai-nang": "den-mau-ai-nang",
    "dinh-phu-coc": "dinh-phu-coc",
    "hang-ho": "hang-ho-den-quan-mai",
    "den-quan-mai": "hang-ho-den-quan-mai",      # cùng cụm -> alias xử lý riêng
    "chua-tien": "chua-tien",
    "nha-tho-giao-xu-bac-son": "nha-tho-giao-xu-bac-son",
    "ho-baiboo": "ho-baiboo",
    "thung-canh": "thung-canh",
    "con-duong-tram": "con-duong-tram",
    "doi-hoa-muong-thon-bo-moi-dap-dong-lang": "doi-hoa-bo-moi",
    "tourism-hub-nha-van-hoa-thon-doi-dung": "tourism-hub-doi-dung",
    "gio-nui-farmstay": "gio-nui-farmstay",
    "lamia-muong-coc": "lamia-muong-coc",
    "ban-moc-muong-coc": "ban-moc-muong-coc",
    "farm-ca-qua-muong-coc": "farm-ca-qua",
    "vuon-sim-co-va-ruou-sim": "vuon-sim-co",
    "doi-duoc-lieu-roc-eo": "doi-duoc-lieu-roc-eo",
    "tram-chill-thung-canh-farmstay": "thung-canh",  # dùng chung ảnh thung-canh
    "ba-la-homestay": "ba-la-homestay",
    "trai-nghiem-nha-san-nha-ba-dien": "nha-san-ba-dien",
    "nha-niem-nga-mat-ong-an-phu-va-tra-sen": "nha-niem-nga",
    "nha-ong-lap-ruou-tam-lap-va-gao-que-doi-ly": "bep-ruou-doi-ly",
    "nha-tho-ho-ong-che-diem-tham-quan-nha-tho-ho": "nha-tho-ho-ong-che",
    "dam-sen-nguyet-farm": "dam-sen-nguyet-farm",
    "homestay-doi-nui-am-thuc-va-trai-nghiem-xe-dap": "homestay-ong-kien",
    "trai-nghiem-xe-dap-dap-doi-lang-bo-moi": "canh-dong-roc-eo",
    "dan-duong-trekking-dong-huong-tich-nha-anh-thuong": "dong-huong-tich",
}

# Điểm liên kết ngoài / dịch vụ KHÔNG có hồ sơ khảo sát riêng nhưng vẫn là
# resolve target của link "Xem hồ sơ điểm đến" từ cung/cẩm nang. Sinh stub page
# nhẹ (hero + mô tả ngắn + bản đồ) để link không 404.
STUBS = {
    "co-la-muong": {
        "ten": "Bữa trưa Cỗ Lá Mường",
        "loai": "am-thuc",
        "vi": "Mâm cỗ lá truyền thống của người Mường — món bày trên lá chuối, "
              "ăn cùng cộng đồng tại Tourism Hub Đồi Dùng. Trải nghiệm ẩm thực "
              "bản địa đặc trưng trong nhiều cung tour Mường Cốc.",
        "en": "A traditional Muong 'leaf feast' served on banana leaves and shared "
              "with the community at Doi Dung Tourism Hub — a signature local-food "
              "experience on many Muong Coc routes.",
        "external": False,
    },
    "chua-huong": {
        "ten": "Chùa Hương (Hương Sơn)", "loai": "tam-linh",
        "vi": "Quần thể danh thắng Hương Sơn, Mỹ Đức — một trong những điểm hành "
              "hương nổi tiếng nhất Hà Nội, kết nối trong các cung tour liên vùng "
              "của Mường Cốc.",
        "en": "The Huong Son (Perfume Pagoda) complex in My Duc — one of Hanoi's "
              "most famous pilgrimage sites, linked in Muong Coc's regional routes.",
        "external": True,
    },
    "dong-huong-tich": {
        "ten": "Động Hương Tích", "loai": "canh-quan",
        "vi": "Động đá vôi kỳ vĩ trong quần thể Hương Sơn — đích đến của cung trek "
              "xuyên rừng từ bản Mường Cốc theo lối mòn người địa phương.",
        "en": "The grand limestone cave in the Huong Son complex — destination of "
              "the forest trek from Muong Coc along local trails.",
        "external": True,
    },
    "suoi-yen": {
        "ten": "Suối Yến", "loai": "ho-nuoc",
        "vi": "Dòng suối thơ mộng dẫn vào quần thể Hương Sơn, đi thuyền giữa núi "
              "non — chặng kết nối trong cung tour tâm linh & sông nước.",
        "en": "The poetic Yen Stream leading into Huong Son, a boat ride amid "
              "karst mountains — part of the spiritual & waterway route.",
        "external": True,
    },
    "quang-phu-cau": {
        "ten": "Làng hương Quảng Phú Cầu", "loai": "van-hoa",
        "vi": "Làng nghề làm hương truyền thống ở Ứng Hoà, Hà Nội — điểm check-in "
              "rực rỡ sắc đỏ, kết nối trên cung tour liên vùng Mường Cốc.",
        "en": "A traditional incense-making village in Ung Hoa, Hanoi — a vivid red "
              "photo spot linked on Muong Coc's regional route.",
        "external": True,
    },
    "cuc-phuong": {
        "ten": "Vườn Quốc gia Cúc Phương", "loai": "canh-quan",
        "vi": "Vườn quốc gia đầu tiên của Việt Nam (Ninh Bình) — rừng nguyên sinh, "
              "đa dạng sinh học, điểm đến liên vùng từ Mường Cốc.",
        "en": "Vietnam's first national park (Ninh Binh) — primary forest and rich "
              "biodiversity, a regional destination from Muong Coc.",
        "external": True,
    },
    "mai-chau": {
        "ten": "Mai Châu", "loai": "van-hoa",
        "vi": "Thung lũng bản Thái ở Hoà Bình — ruộng lúa, nhà sàn, dệt thổ cẩm, "
              "điểm đến liên vùng trên cung tour dài ngày của Mường Cốc.",
        "en": "A Thai-village valley in Hoa Binh — rice paddies, stilt houses and "
              "brocade weaving, a regional stop on Muong Coc's multi-day route.",
        "external": True,
    },
    "pu-luong": {
        "ten": "Pù Luông", "loai": "canh-quan",
        "vi": "Khu bảo tồn thiên nhiên Pù Luông (Thanh Hoá) — ruộng bậc thang, "
              "rừng nhiệt đới, điểm đến liên vùng trên cung tour dài ngày Mường Cốc.",
        "en": "Pu Luong Nature Reserve (Thanh Hoa) — terraced fields and tropical "
              "forest, a regional stop on Muong Coc's multi-day route.",
        "external": True,
    },
}

# slug page riêng (không trùng poi-slug ảnh, dùng ảnh mặc định theo loại):
# tất cả hoso còn lại -> slug suy từ tên file (slugify), hero = ảnh default.

# loại -> (icon, theme skin site.css, ảnh hero mặc định khi không map ảnh)
LOAI_PROFILE = {
    "tam-linh":   ("⛩️", "disan", "assets/img/poi/chua-phu-coc/hero.jpg"),
    "di-tich":    ("🏛️", "disan", "assets/img/poi/dinh-phu-coc/hero.jpg"),
    "canh-quan":  ("🏔️", "sinhthai", "assets/img/poi/thung-canh/hero.jpg"),
    "ho-nuoc":    ("🌊", "honuoc", "assets/img/poi/ho-baiboo/hero.jpg"),
    "farmstay":   ("🌾", "nongnghiep", "assets/img/poi/gio-nui-farmstay/hero.jpg"),
    "homestay":   ("🏡", "nongnghiep", "assets/img/poi/ba-la-homestay/hero.jpg"),
    "nong-nghiep":("🌱", "nongnghiep", "assets/img/poi/canh-dong-roc-eo/hero.jpg"),
    "am-thuc":    ("🍲", "ketnoi", "assets/img/poi/co-la-muong/hero.jpg"),
    "trai-nghiem":("🛶", "sinhthai", "assets/img/poi/ho-baiboo/hero.jpg"),
    "van-hoa":    ("🪕", "disan", "assets/img/poi/tourism-hub-doi-dung/hero.jpg"),
}
DEFAULT_LOAI = ("📍", "sinhthai", "assets/img/thung-canh.jpg")

# Suy loại từ TIÊU ĐỀ (ưu tiên — chính xác hơn quét toàn văn vì "gia đình",
# "tập quán" trong body gây nhiễu). Chỉ fallback raw cho vài keyword an toàn.
def guess_loai(title, raw):
    t = title.lower()
    if "farmstay" in t:
        return "farmstay"
    if "homestay" in t or "nhà sàn" in t or "nhà cổ" in t or "nhà vườn" in t:
        return "homestay"
    if "nhà thờ" in t or "giáo xứ" in t:
        return "tam-linh"
    if "chùa" in t or "miếu" in t or ("đền" in t and "đình" not in t):
        return "tam-linh"
    if "đền" in t:
        return "tam-linh"
    if "đình" in t:
        return "di-tich"
    if any(k in t for k in ["hồ ", "đầm", "bè tre", "hồ câu", "suối"]):
        return "ho-nuoc"
    if any(k in t for k in ["hang", "động", "thung", "đồi hoa", "con đường",
                            "vườn sim", "vườn hoa", "kèn hồng"]):
        return "canh-quan"
    if any(k in t for k in ["dược liệu", "trà sen", "mật ong", "rượu", "bếp",
                            "ẩm thực", "cỗ lá", "nhà hàng", "đặc sản", "sản vật"]):
        return "am-thuc"
    if any(k in t for k in ["vườn", "trang trại", "nông nghiệp", "mò trai",
                            "nông trại", "cá quả", "dưa chuột", "lợn", "gà",
                            "vịt", "ốc", "mò trai", "chăn trâu"]):
        return "nong-nghiep"
    if any(k in t for k in ["xe đạp", "trekking", "trải nghiệm", "dẫn đường",
                            "bè", "điểm dừng"]):
        return "trai-nghiem"
    if any(k in t for k in ["tourism hub", "nhà văn hoá", "nhà văn hóa",
                            "văn hoá", "văn hóa", "chợ", "event", "sang", "mộc mường"]):
        return "van-hoa"
    return "canh-quan"

# nhóm hiển thị trên trang index (gộp loại)
GROUP_OF = {
    "tam-linh": "ditich", "di-tich": "ditich", "van-hoa": "ditich",
    "canh-quan": "thiennhien", "ho-nuoc": "thiennhien",
    "farmstay": "luutru", "homestay": "luutru",
    "nong-nghiep": "trainghiem", "trai-nghiem": "trainghiem", "am-thuc": "trainghiem",
}
GROUP_META = [
    ("ditich", "⛩️", {"vi": "Di tích · Văn hoá · Tâm linh", "en": "Heritage · Culture · Spiritual"}),
    ("thiennhien", "🏔️", {"vi": "Thiên nhiên · Cảnh quan", "en": "Nature · Landscape"}),
    ("luutru", "🏡", {"vi": "Lưu trú · Farmstay · Homestay", "en": "Stays · Farmstay · Homestay"}),
    ("trainghiem", "🌾", {"vi": "Trải nghiệm · Nông nghiệp · Ẩm thực", "en": "Experiences · Farm · Food"}),
]
LOAI_LABEL = {
    "tam-linh": {"vi": "Di tích tâm linh", "en": "Spiritual heritage"},
    "di-tich": {"vi": "Di tích lịch sử", "en": "Historic site"},
    "van-hoa": {"vi": "Không gian văn hoá", "en": "Cultural space"},
    "canh-quan": {"vi": "Cảnh quan thiên nhiên", "en": "Natural landscape"},
    "ho-nuoc": {"vi": "Hồ nước · sông", "en": "Lake & water"},
    "farmstay": {"vi": "Farmstay", "en": "Farmstay"},
    "homestay": {"vi": "Homestay · lưu trú", "en": "Homestay & lodging"},
    "nong-nghiep": {"vi": "Trải nghiệm nông nghiệp", "en": "Farm experience"},
    "trai-nghiem": {"vi": "Điểm trải nghiệm", "en": "Experience spot"},
    "am-thuc": {"vi": "Ẩm thực · đặc sản", "en": "Food & specialty"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def e(s):
    return html.escape(str(s or ""))


def slugify(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return re.sub(r"-+", "-", s)


def t3(vi, en=None):
    en = en or vi
    return (f'<span data-lang="vi">{e(vi)}</span>'
            f'<span data-lang="en">{e(en)}</span>'
            f'<span data-lang="fr">{e(en)}</span>')


def block3(vi, en=None, tag="div"):
    en = en or vi
    return (f'<{tag} data-lang="vi">{vi}</{tag}>'
            f'<{tag} data-lang="en">{en}</{tag}>'
            f'<{tag} data-lang="fr">{en}</{tag}>')


def img_for_name(name):
    return IMAGE_MAP.get(name)


def coords_for(name):
    """Tìm lat/lon: khớp tên chính xác hoặc chứa tên."""
    if name in COORDS and COORDS[name].get("lat"):
        return COORDS[name]["lat"], COORDS[name]["lon"]
    for k, v in COORDS.items():
        if v.get("lat") and name and (name in k or k in name):
            return v["lat"], v["lon"]
    return None, None


# ---------------------------------------------------------------------------
# PARSER hồ sơ .md (2 biến thể: dot-1 plain / dot-2 markdown)
# ---------------------------------------------------------------------------
SEC_PAT = re.compile(r"^\s*#*\s*(\d)\.\s*(.+?)\s*$")


def clean_md(line):
    line = line.replace("**", "").replace("☑", "").replace("☐", "")
    return line.strip()


def parse_hoso(path):
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    # tiêu đề: dòng IN HOA đầu tiên không phải "HỒ SƠ..." / phụ đề
    title = ""
    for ln in lines[:12]:
        s = clean_md(ln)
        if not s or s.startswith("(") or s.startswith("Điểm đến"):
            continue
        if "HỒ SƠ GIỚI THIỆU" in s.upper() or "XÂY DỰNG SẢN PHẨM" in s.upper():
            continue
        if s.isupper() or s == s.upper():
            title = s
            break
    if not title:
        title = path.stem

    # tách section theo "N. TÊN"
    secs = {}
    cur = None
    buf = []
    for ln in lines:
        m = SEC_PAT.match(ln)
        if m and m.group(1) in "1234567" and len(clean_md(ln)) < 60:
            if cur:
                secs[cur] = buf
            cur = int(m.group(1))
            buf = []
        elif cur:
            buf.append(ln)
    if cur:
        secs[cur] = buf

    def get_kv(sec_lines, key):
        for i, ln in enumerate(sec_lines):
            s = clean_md(ln)
            if s.lower().startswith(key.lower()):
                val = s.split(":", 1)[1].strip() if ":" in s else ""
                if not val:  # giá trị ở dòng kế
                    for j in range(i + 1, min(i + 3, len(sec_lines))):
                        nx = clean_md(sec_lines[j])
                        if nx and not nx.lower().startswith(("ông", "bà")):
                            val = nx
                            break
                        if nx:
                            val = nx
                            break
                return val
        return ""

    def paragraphs(sec_lines):
        out, cur_p = [], []
        for ln in sec_lines:
            s = clean_md(ln)
            if s == "---":
                continue
            if not s:
                if cur_p:
                    out.append(" ".join(cur_p))
                    cur_p = []
            else:
                cur_p.append(s)
        if cur_p:
            out.append(" ".join(cur_p))
        return out

    def bullets(sec_lines):
        out = []
        for ln in sec_lines:
            s = clean_md(ln)
            if s.startswith(("-", "•", "·")):
                out.append(s.lstrip("-•· ").strip())
        return out

    def table_rows(sec_lines):
        rows = []
        for ln in sec_lines:
            s = ln.strip()
            if s.startswith("|") and "|" in s[1:]:
                cells = [c.strip() for c in s.strip("|").split("|")]
                if all(set(c) <= set("-: ") for c in cells):
                    continue  # separator
                if len(cells) >= 2 and cells[0].lower() not in ("dịch vụ",):
                    rows.append((cells[0], cells[1]))
        return rows

    info = secs.get(1, [])
    data = {
        "title": title,
        "ten": get_kv(info, "Tên điểm đến") or title.title(),
        "dia_chi": get_kv(info, "Địa chỉ"),
        "mo_cua": get_kv(info, "Thời gian mở cửa"),
        "chu_ho": get_kv(info, "Chủ hộ") or get_kv(info, "Người đại diện"),
        "loai_list": [b for b in bullets(info)] or _checked_lines(info),
        "suc_chua": [b for b in bullets(info) if "khách" in b.lower()],
        "intro": paragraphs(secs.get(2, [])),
        "values": parse_values(secs.get(3, [])),
        "services": table_rows(secs.get(4, [])) or bullets(secs.get(4, [])),
        "experiences": bullets(secs.get(5, [])),
        "visitor": parse_visitor(secs.get(6, [])),
        "future": " ".join(paragraphs(secs.get(7, []))[:2]),
        "raw": raw,
    }
    return data


def _checked_lines(sec_lines):
    out = []
    for ln in sec_lines:
        if "☑" in ln:
            out.append(clean_md(ln))
    return out


def parse_values(sec_lines):
    """Mục 3: nhóm 'Giá trị X' -> list bullet."""
    groups = []
    cur = None
    for ln in sec_lines:
        s = clean_md(ln)
        if not s or s == "---":
            continue
        if s.startswith(("-", "•", "·")):
            if cur:
                cur[1].append(s.lstrip("-•· ").strip())
        elif s.lower().startswith("giá trị") or (len(s) < 40 and not s[0].islower()):
            cur = (s, [])
            groups.append(cur)
    return [g for g in groups if g[1]]


def parse_visitor(sec_lines):
    """Mục 6: ngôn ngữ / tiện ích / lưu ý."""
    res = {"lang": [], "amenities": [], "notes": []}
    cur = None
    for ln in sec_lines:
        s = clean_md(ln)
        if not s or s == "---":
            continue
        low = s.lower()
        if low.startswith("ngôn ngữ"):
            cur = "lang"; continue
        if low.startswith("tiện ích"):
            cur = "amenities"; continue
        if low.startswith("lưu ý"):
            cur = "notes"; continue
        item = s.lstrip("-•· ").strip()
        if "☑" in ln or s.startswith(("-", "•", "·")) or cur:
            if cur and item:
                res[cur].append(item)
    return res


# ---------------------------------------------------------------------------
# Khung dùng chung (GIỐNG generate-web.py, prefix tương ứng cấp thư mục)
# ---------------------------------------------------------------------------
def head(title, desc, prefix, og_img, theme=""):
    poi_css = POI_INLINE_CSS
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
<style>{poi_css}</style>
</head>
<body>
<div class="wrap">'''


def topbar(prefix, with_home=True):
    home = (f'<a class="home-link" href="{prefix or "./"}">'
            f'{t3("← Trang chủ", "← Home")}</a>') if with_home else ""
    return f'''<nav class="topbar">
  <a class="brand" href="{prefix or "./"}">
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


def tail(prefix):
    return (f'{footer(prefix)}\n</div>\n{fab()}\n'
            f'<script src="{prefix}assets/js/site.js"></script>\n</body>\n</html>')


# ---------------------------------------------------------------------------
# CSS riêng POI (bổ sung nhẹ trên site.css)
# ---------------------------------------------------------------------------
POI_INLINE_CSS = """
.poi-infobar{display:grid;grid-template-columns:1fr 1fr;gap:0;background:#fff;border-radius:14px;
  overflow:hidden;box-shadow:var(--shadow-sm);margin-top:4px;border:1px solid rgba(201,145,47,.14);}
.poi-infobar .cell{padding:13px 15px;border-top:3px solid var(--accent);border-right:1px solid rgba(201,145,47,.12);}
.poi-infobar .cell:nth-child(2n){border-right:none;}
.poi-infobar .cell .l{font-size:.6rem;letter-spacing:.14em;text-transform:uppercase;color:var(--amber);font-weight:700;}
.poi-infobar .cell .v{font-family:var(--serif);font-weight:600;font-size:1.02rem;color:var(--accent-dark);line-height:1.2;margin-top:3px;}
@media(min-width:560px){.poi-infobar{grid-template-columns:repeat(4,1fr);}.poi-infobar .cell:nth-child(2n){border-right:1px solid rgba(201,145,47,.12);}.poi-infobar .cell:last-child{border-right:none;}}
.val-grid{display:grid;gap:13px;margin-top:4px;}
@media(min-width:560px){.val-grid{grid-template-columns:1fr 1fr;}}
.val-box{background:#fff;border-radius:13px;padding:15px 17px;box-shadow:var(--shadow-sm);}
.val-box h3{font-family:var(--serif);font-weight:600;font-size:1.12rem;color:var(--amber);
  border-bottom:1px solid rgba(201,145,47,.3);padding-bottom:7px;margin-bottom:9px;}
.val-box ul{list-style:none;display:flex;flex-direction:column;gap:6px;}
.val-box li{font-size:.9rem;color:#3a3633;padding-left:16px;position:relative;line-height:1.45;}
.val-box li::before{content:"–";position:absolute;left:0;color:var(--accent);font-weight:700;}
.svc-table{width:100%;border-collapse:collapse;margin-top:4px;background:#fff;border-radius:13px;overflow:hidden;box-shadow:var(--shadow-sm);}
.svc-table td{padding:11px 15px;border-bottom:1px solid rgba(201,145,47,.13);vertical-align:top;font-size:.9rem;color:#3a3633;}
.svc-table tr:last-child td{border-bottom:none;}
.svc-table td.k{font-family:var(--serif);font-weight:600;color:var(--accent-dark);width:42%;}
.svc-list{list-style:none;display:flex;flex-direction:column;gap:8px;margin-top:4px;}
.svc-list li{background:#fff;border-radius:11px;padding:11px 15px;box-shadow:var(--shadow-sm);font-size:.9rem;color:#3a3633;border-left:3px solid var(--accent);}
.exp-list{list-style:none;display:flex;flex-direction:column;gap:9px;margin-top:4px;}
.exp-list li{display:flex;gap:11px;background:#fff;border-radius:12px;padding:12px 15px;box-shadow:var(--shadow-sm);font-size:.92rem;color:#3a3633;line-height:1.45;}
.exp-list li::before{content:"✦";color:var(--amber);font-weight:700;flex-shrink:0;}
.amen-list{display:flex;flex-wrap:wrap;gap:8px;margin-top:4px;}
.amen-list span{background:#fff;border:1px solid rgba(10,106,47,.18);border-radius:999px;padding:7px 13px;font-size:.8rem;font-weight:600;color:var(--accent-dark);}
.gallery{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:4px;}
.gallery img{width:100%;height:150px;object-fit:cover;border-radius:13px;box-shadow:var(--shadow-sm);}
.gallery img:first-child{grid-column:1 / -1;height:200px;}
.cung-ref{display:flex;flex-direction:column;gap:10px;margin-top:4px;}
.cung-ref a{display:flex;align-items:center;gap:12px;background:#fff;border-radius:13px;padding:12px 15px;
  box-shadow:var(--shadow-sm);text-decoration:none;color:var(--ink);border:1px solid rgba(201,145,47,.12);}
.cung-ref a .ci{font-size:1.4rem;flex-shrink:0;}
.cung-ref a .cn{font-weight:600;font-size:.95rem;color:var(--accent-dark);flex:1;}
.cung-ref a .arrow{color:var(--amber);font-size:1.1rem;}
.poi-future{background:linear-gradient(135deg,var(--accent),var(--accent-dark));color:#fff;border-radius:15px;
  padding:18px 20px;margin-top:4px;}
.poi-future b{display:block;font-family:var(--serif);font-size:1.1rem;margin-bottom:6px;}
.poi-future p{font-size:.9rem;opacity:.93;line-height:1.55;}
.poi-index-list{display:grid;gap:12px;margin-top:4px;}
@media(min-width:560px){.poi-index-list{grid-template-columns:1fr 1fr;}}
.poi-index-card{display:flex;align-items:center;gap:13px;background:#fff;border-radius:14px;padding:11px;
  box-shadow:var(--shadow-sm);text-decoration:none;color:var(--ink);border:1px solid rgba(201,145,47,.12);}
.poi-index-card .thumb{flex-shrink:0;width:66px;height:66px;border-radius:11px;object-fit:cover;background:var(--cream-2);}
.poi-index-card .nm{font-weight:600;font-size:.96rem;line-height:1.2;color:var(--ink);}
.poi-index-card .ty{font-size:.7rem;color:var(--muted);margin-top:3px;}
.poi-index-card .arrow{margin-left:auto;color:var(--amber);font-size:1.1rem;flex-shrink:0;}
"""


# ---------------------------------------------------------------------------
# RENDER 1 POI page
# ---------------------------------------------------------------------------
def render_poi(slug, d, poislug, loai, cung_refs):
    prefix = "../../"
    icon, theme, default_img = LOAI_PROFILE.get(loai, DEFAULT_LOAI)

    # ảnh hero + gallery
    if poislug and (IMG_POI / poislug / "hero.jpg").exists():
        imgdir = f"assets/img/poi/{poislug}"
        hero = f"{imgdir}/hero.jpg"
        gallery = [f"{imgdir}/{f}" for f in ("02.jpg", "03.jpg")
                   if (IMG_POI / poislug / f).exists()]
    else:
        hero = default_img
        gallery = []

    ten = d["ten"]
    title = f"{ten} — Hồ sơ điểm đến Mường Cốc"
    desc = (d["intro"][0] if d["intro"] else ten)[:155]
    loai_lab = LOAI_LABEL.get(loai, {"vi": "Điểm đến", "en": "Destination"})

    parts = [head(title, desc, prefix, hero, theme)]
    parts.append(topbar(prefix, with_home=True))

    # HERO
    parts.append(f'''  <header class="hero compact">
    <div class="hero-bg"><img src="{prefix}{hero}" alt="{e(ten)}"></div>
    <div class="hero-body" style="padding-top:34px;">
      <div class="hero-pre">{icon} {t3("Hồ sơ điểm đến", "Destination profile")}</div>
      <h1 style="font-size:2.3rem;">{e(ten)}</h1>
      <div class="hero-tag">{t3(loai_lab["vi"], loai_lab["en"])}</div>
      <div class="hero-loc">📍 {t3("Xã Mỹ Đức · Hà Nội", "My Duc Commune · Hanoi")}</div>
    </div>
  </header>''')

    # GIỚI THIỆU
    if d["intro"]:
        ps = "".join(f"<p>{e(p)}</p>" for p in d["intro"])
        first = d["intro"][0]
        rest = "".join(f"<p>{e(p)}</p>" for p in d["intro"][1:])
        drop = (f'<p><span class="drop">{e(first[0])}</span>{e(first[1:])}</p>{rest}'
                if first else ps)
        parts.append(f'''  <section class="intro alt">
    <div class="kick">{t3("Giới thiệu", "Overview")}</div>
    {block3(drop, ps, tag="div")}
  </section>''')

    # INFOBAR
    cells = []
    if d["loai_list"]:
        cells.append(("Loại hình", loai_lab["vi"], loai_lab["en"]))
    if d["mo_cua"]:
        cells.append(("Giờ mở cửa", d["mo_cua"], d["mo_cua"]))
    if d["suc_chua"]:
        sc = " · ".join(d["suc_chua"])[:42]
        cells.append(("Sức chứa", sc, sc))
    if d["dia_chi"]:
        cells.append(("Vị trí", d["dia_chi"], d["dia_chi"]))
    if cells:
        cell_html = "".join(
            f'<div class="cell"><div class="l">{t3(l, l)}</div>'
            f'<div class="v">{t3(vi, en)}</div></div>'
            for l, vi, en in cells[:4])
        parts.append(f'''  <section>
    <div class="kick">{t3("Thông tin nhanh", "Quick facts")}</div>
    <div class="poi-infobar">{cell_html}</div>
  </section>''')

    # GIÁ TRỊ NỔI BẬT
    if d["values"]:
        boxes = []
        for name, items in d["values"]:
            li = "".join(f"<li>{t3(x)}</li>" for x in items)
            boxes.append(f'<div class="val-box"><h3>{t3(name)}</h3><ul>{li}</ul></div>')
        parts.append(f'''  <section class="alt">
    <div class="kick">{t3("Giá trị nổi bật", "Highlights")}</div>
    <h2 class="sec">{t3("Vì sao ", "Why ")}<em>{t3("đáng ghé", "visit")}</em></h2>
    <div class="val-grid">{"".join(boxes)}</div>
  </section>''')

    # DỊCH VỤ
    if d["services"]:
        if isinstance(d["services"][0], tuple):
            rows = "".join(
                f'<tr><td class="k">{t3(k)}</td><td>{t3(v)}</td></tr>'
                for k, v in d["services"])
            svc = f'<table class="svc-table">{rows}</table>'
        else:
            svc = '<ul class="svc-list">' + "".join(
                f"<li>{t3(x)}</li>" for x in d["services"]) + "</ul>"
        parts.append(f'''  <section>
    <div class="kick">{t3("Dịch vụ", "Services")}</div>
    <h2 class="sec">{t3("Dịch vụ ", "What's ")}<em>{t3("cung cấp", "offered")}</em></h2>
    {svc}
  </section>''')

    # TRẢI NGHIỆM GỢI Ý
    if d["experiences"]:
        li = "".join(f"<li><span>{t3(x)}</span></li>" for x in d["experiences"])
        parts.append(f'''  <section class="alt">
    <div class="kick">{t3("Trải nghiệm gợi ý", "Suggested experiences")}</div>
    <h2 class="sec">{t3("Bạn có thể ", "Things ")}<em>{t3("làm gì", "to do")}</em></h2>
    <ul class="exp-list">{li}</ul>
  </section>''')

    # ẢNH PHỤ
    if gallery:
        imgs = f'<img src="{prefix}{hero}" alt="{e(ten)}" loading="lazy">' + "".join(
            f'<img src="{prefix}{g}" alt="{e(ten)}" loading="lazy">' for g in gallery)
        parts.append(f'''  <section>
    <div class="kick">{t3("Hình ảnh", "Gallery")}</div>
    <div class="gallery">{imgs}</div>
  </section>''')

    # THÔNG TIN PHỤC VỤ KHÁCH (tiện ích + lưu ý)
    vis = d["visitor"]
    if vis["amenities"] or vis["notes"]:
        blocks = []
        if vis["amenities"]:
            am = "".join(f"<span>{t3(x)}</span>" for x in vis["amenities"])
            blocks.append(f'<div class="kick" style="margin-top:4px;">{t3("Tiện ích", "Amenities")}</div>'
                          f'<div class="amen-list">{am}</div>')
        if vis["notes"]:
            notes = "".join(
                f'<div class="note"><span class="ni">📌</span><div class="nt"><span>{t3(x)}</span></div></div>'
                for x in vis["notes"])
            blocks.append(f'<div class="kick" style="margin-top:20px;">{t3("Lưu ý khi tham quan", "Good to know")}</div>'
                          f'<div class="note-list">{notes}</div>')
        parts.append(f'''  <section class="alt">
    <h2 class="sec">{t3("Phục vụ ", "Visitor ")}<em>{t3("khách", "info")}</em></h2>
    {"".join(blocks)}
  </section>''')

    # CUNG TOUR GHÉ ĐIỂM NÀY
    if cung_refs:
        refs = "".join(
            f'<a href="{prefix}cung/{cs}/"><span class="ci">{ci}</span>'
            f'<span class="cn">{t3(cn)}</span><span class="arrow">→</span></a>'
            for cs, cn, ci in cung_refs)
        parts.append(f'''  <section>
    <div class="kick">{t3("Cung tour ghé điểm này", "Routes that stop here")}</div>
    <h2 class="sec">{t3("Có trong ", "Part of ")}<em>{t3("hành trình", "journeys")}</em></h2>
    <div class="cung-ref">{refs}</div>
  </section>''')

    # ĐỊNH HƯỚNG PHÁT TRIỂN
    if d["future"]:
        parts.append(f'''  <section class="alt">
    <div class="poi-future"><b>{t3("Định hướng phát triển", "Looking ahead")}</b>
      <p>{t3(d["future"])}</p></div>
  </section>''')

    # CTA: bản đồ + trang chủ
    lat, lon = coords_for(ten) if ten else (None, None)
    if not (lat and lon):
        lat, lon = coords_for(d["title"])
    if lat and lon:
        map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        map_sub = t3("Mở vị trí trên Google Maps", "Open in Google Maps")
    else:
        map_url = MAPS_URL
        map_sub = t3("Bản đồ du lịch Mường Cốc", "Muong Coc tourism map")
    parts.append(f'''  <section>
    <div class="kick center">{t3("Định hướng", "Find your way")}</div>
    <div class="cta-stack">
      <a class="btn" href="{map_url}" target="_blank" rel="noopener"><span class="ic">🗺️</span><span>{t3("Mở bản đồ", "Open map")}<small>{map_sub}</small></span></a>
      <a class="btn ghost" href="{prefix}"><span class="ic">←</span><span>{t3("Trang chủ", "Home")}<small>{t3("Du lịch cộng đồng Mường Cốc", "Muong Coc Community Tourism")}</small></span></a>
    </div>
  </section>''')

    parts.append(tail(prefix))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# RENDER stub page (điểm ngoài / dịch vụ — link resolve, không 404)
# ---------------------------------------------------------------------------
def render_stub(slug, s, cung_refs):
    prefix = "../../"
    loai = s["loai"]
    icon, theme, default_img = LOAI_PROFILE.get(loai, DEFAULT_LOAI)
    hero = (f"assets/img/poi/{slug}/hero.jpg"
            if (IMG_POI / slug / "hero.jpg").exists() else default_img)
    ten = s["ten"]
    loai_lab = LOAI_LABEL.get(loai, {"vi": "Điểm đến", "en": "Destination"})
    badge = (t3("Điểm liên kết ngoài vùng", "Regional partner destination")
             if s.get("external") else t3("Trải nghiệm Mường Cốc", "Muong Coc experience"))

    parts = [head(f"{ten} — Hồ sơ điểm đến Mường Cốc", s["vi"][:155], prefix, hero, theme)]
    parts.append(topbar(prefix, with_home=True))
    parts.append(f'''  <header class="hero compact">
    <div class="hero-bg"><img src="{prefix}{hero}" alt="{e(ten)}"></div>
    <div class="hero-body" style="padding-top:34px;">
      <div class="hero-pre">{icon} {badge}</div>
      <h1 style="font-size:2.3rem;">{e(ten)}</h1>
      <div class="hero-tag">{t3(loai_lab["vi"], loai_lab["en"])}</div>
    </div>
  </header>''')
    parts.append(f'''  <section class="intro alt">
    <div class="kick">{t3("Giới thiệu", "Overview")}</div>
    {block3("<p>" + e(s["vi"]) + "</p>", "<p>" + e(s["en"]) + "</p>", tag="div")}
  </section>''')

    if cung_refs:
        refs = "".join(
            f'<a href="{prefix}cung/{cs}/"><span class="ci">{ci}</span>'
            f'<span class="cn">{t3(cn)}</span><span class="arrow">→</span></a>'
            for cs, cn, ci in cung_refs)
        parts.append(f'''  <section>
    <div class="kick">{t3("Cung tour ghé điểm này", "Routes that stop here")}</div>
    <div class="cung-ref">{refs}</div>
  </section>''')

    lat, lon = coords_for(ten)
    if lat and lon:
        map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        map_sub = t3("Mở vị trí trên Google Maps", "Open in Google Maps")
    else:
        map_url, map_sub = MAPS_URL, t3("Bản đồ du lịch Mường Cốc", "Muong Coc tourism map")
    parts.append(f'''  <section class="alt">
    <div class="cta-stack">
      <a class="btn" href="{map_url}" target="_blank" rel="noopener"><span class="ic">🗺️</span><span>{t3("Mở bản đồ", "Open map")}<small>{map_sub}</small></span></a>
      <a class="btn ghost" href="{prefix}"><span class="ic">←</span><span>{t3("Trang chủ", "Home")}<small>{t3("Du lịch cộng đồng Mường Cốc", "Muong Coc Community Tourism")}</small></span></a>
    </div>
  </section>''')
    parts.append(tail(prefix))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# RENDER poi/index.html (danh sách)
# ---------------------------------------------------------------------------
def render_index(items):
    """items: list of dict(slug, ten, loai, poislug, group)."""
    prefix = "../"
    parts = [head("Hồ sơ điểm đến — Du lịch cộng đồng Mường Cốc",
                  "Toàn bộ hồ sơ điểm đến Mường Cốc: di tích, cảnh quan, lưu trú, trải nghiệm bản Mường.",
                  prefix, "assets/img/poi/dinh-phu-coc/hero.jpg", "")]
    parts.append(topbar(prefix, with_home=True))
    parts.append(f'''  <header class="hero compact">
    <div class="hero-bg"><img src="{prefix}assets/img/poi/dinh-phu-coc/hero.jpg" alt="Điểm đến Mường Cốc"></div>
    <div class="hero-body" style="padding-top:34px;">
      <div class="hero-pre">⛩️ {t3("Khám phá sâu hơn", "Dig deeper")}</div>
      <h1 style="font-size:2.3rem;">{t3("Hồ sơ điểm đến", "Destination profiles")}</h1>
      <div class="hero-tag">{t3("Mỗi điểm một câu chuyện bản Mường", "Each place, a Muong story")}</div>
    </div>
  </header>''')

    by_group = {}
    for it in items:
        by_group.setdefault(it["group"], []).append(it)
    for gkey, gi, glabel in GROUP_META:
        lst = by_group.get(gkey, [])
        if not lst:
            continue
        cards = []
        for it in sorted(lst, key=lambda x: x["ten"]):
            ps = it["poislug"]
            thumb = (f"{prefix}assets/img/poi/{ps}/hero.jpg"
                     if ps and (IMG_POI / ps / "hero.jpg").exists()
                     else f"{prefix}" + LOAI_PROFILE.get(it["loai"], DEFAULT_LOAI)[2])
            lab = LOAI_LABEL.get(it["loai"], {"vi": "Điểm đến", "en": "Destination"})
            cards.append(
                f'<a class="poi-index-card" href="{it["slug"]}/">'
                f'<img class="thumb" src="{thumb}" alt="{e(it["ten"])}" loading="lazy">'
                f'<span><span class="nm">{e(it["ten"])}</span>'
                f'<span class="ty">{t3(lab["vi"], lab["en"])}</span></span>'
                f'<span class="arrow">→</span></a>')
        parts.append(f'''  <section>
    <div class="grp"><span class="gi">{gi}</span><span class="gt">{t3(glabel["vi"], glabel["en"])}</span><span class="gc">{len(lst)}</span></div>
    <div class="poi-index-list">{"".join(cards)}</div>
  </section>''')

    parts.append(f'''  <section class="alt">
    <a class="btn" href="{MAPS_URL}" target="_blank" rel="noopener"><span class="ic">🗺️</span><span>{t3("Bản đồ du lịch Mường Cốc", "Muong Coc tourism map")}<small>{t3("Google My Maps · tất cả điểm đến", "Google My Maps · all stops")}</small></span></a>
  </section>''')
    parts.append(tail(prefix))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CUNG refs: quét data/*.json tìm cung có ghé điểm (theo poislug ảnh)
# ---------------------------------------------------------------------------
CUNG_ICON = {"xe-dap": "🚲", "trek": "🥾", "tour": "🌾"}


def build_cung_index():
    """poislug -> list (cung-slug, ten, icon)."""
    idx = {}
    tour_files = [p for p in DATA.glob("*.json")
                  if p.name not in ("images.json", "master-poi-coords.json")]
    for p in tour_files:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "ten" not in d:
            continue
        cslug = p.stem
        icon = CUNG_ICON.get(d.get("loai", ""), "🗺️")
        names = [x.get("ten", "") for x in d.get("diem_den", [])] + \
                [x.get("diem", "") for x in d.get("lich_trinh", [])]
        seen = set()
        for n in names:
            path = img_for_name(n)
            if not path:
                continue
            ps = path.split("/")[3] if "poi/" in path else ""
            if ps and ps not in seen:
                seen.add(ps)
                idx.setdefault(ps, [])
                if cslug not in [c[0] for c in idx[ps]]:
                    idx[ps].append((cslug, d.get("ten", cslug), icon))
    return idx


# ---------------------------------------------------------------------------
# Build all
# ---------------------------------------------------------------------------
def collect_hoso():
    """-> list of (slug, poislug, data, loai)."""
    out = []
    used_slugs = {}
    for hd in HOSO_DIRS:
        for md in sorted(hd.glob("hoso-*.md")):
            d = parse_hoso(md)
            base = re.sub(r"^hoso-\d+-", "", md.stem)
            poislug = HOSO_TO_POISLUG.get(base)
            loai = guess_loai(d["title"], d["raw"])
            # slug page: ưu tiên poislug ảnh (để cung resolve), else base
            slug = poislug or base
            # tránh trùng slug (vd hang-ho + den-quan-mai cùng poislug)
            if slug in used_slugs:
                slug = base  # giữ slug riêng theo tên file
            used_slugs[slug] = md.name
            out.append((slug, poislug, d, loai, base, md.name))
    return out


def main(argv):
    POI_OUT.mkdir(parents=True, exist_ok=True)
    cung_idx = build_cung_index()
    hoso = collect_hoso()

    index_only = argv and argv[0] == "--index"
    want = set(a for a in argv if not a.startswith("--"))

    hoso_slugs = {slug for slug, *_ in hoso}

    index_items = []
    generated = []
    for slug, poislug, d, loai, base, fname in hoso:
        index_items.append({"slug": slug, "ten": d["ten"], "loai": loai,
                            "poislug": poislug, "group": GROUP_OF.get(loai, "thiennhien")})
        if index_only:
            continue
        if want and slug not in want:
            continue
        cung_refs = cung_idx.get(poislug, []) if poislug else []
        out = POI_OUT / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_poi(slug, d, poislug, loai, cung_refs), encoding="utf-8")
        generated.append((slug, poislug, fname))
        print(f"[OK] poi/{slug}/index.html  <- {fname}"
              + (f"  (img: {poislug})" if poislug else "  (img: default)"))

    # STUB pages: điểm ngoài / dịch vụ không có hồ sơ riêng nhưng là resolve target
    for slug, s in STUBS.items():
        if slug in hoso_slugs:
            continue  # đã có page từ hồ sơ thật
        index_items.append({"slug": slug, "ten": s["ten"], "loai": s["loai"],
                            "poislug": slug, "group": GROUP_OF.get(s["loai"], "thiennhien")})
        if index_only or (want and slug not in want):
            continue
        cung_refs = cung_idx.get(slug, [])
        out = POI_OUT / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_stub(slug, s, cung_refs), encoding="utf-8")
        generated.append((slug, slug, "STUB"))
        print(f"[OK] poi/{slug}/index.html  <- STUB (điểm ngoài/dịch vụ)")

    # index page (luôn sinh)
    (POI_OUT / "index.html").write_text(render_index(index_items), encoding="utf-8")
    print(f"[OK] poi/index.html  ({len(index_items)} điểm)")

    if not index_only:
        with_img = sum(1 for _, ps, _ in generated if ps)
        print(f"\nXong: {len(generated)} page + index. "
              f"{with_img} page có ảnh riêng, {len(generated)-with_img} dùng ảnh mặc định.")


if __name__ == "__main__":
    main(sys.argv[1:])
