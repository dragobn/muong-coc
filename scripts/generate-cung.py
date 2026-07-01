#!/usr/bin/env python3
"""
generate-cung.py — Sinh brochure 8 trang A4 + poster 2 mặt A5
cho mỗi cung tour Mường Cốc từ master-data JSON + Jinja2 template.

v2: Đổ ảnh thật từ images.json vào slot hero, itinerary-head, dest-card.
    Nếu không có ảnh → giữ placeholder .ph

Dùng:
  python3 scripts/generate-cung.py                   # sinh tất cả 19 cung
  python3 scripts/generate-cung.py vong-xe-xanh      # sinh 1 cung
  python3 scripts/generate-cung.py vong-xe-xanh dau-xua-muong-coc  # nhiều cung

Output:
  cung/{slug}/brochure.html
  cung/{slug}/poster.html
"""

import json
import os
import sys
import re
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Jinja2 — thử import, fallback sang string.Template nếu chưa cài
# ---------------------------------------------------------------------------
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_OK = True
except ImportError:
    JINJA2_OK = False
    print("[WARN] Jinja2 chưa cài. Thử: pip install jinja2  hoặc  ~/.claude/skills/.venv/bin/pip install jinja2")
    print("[WARN] Generator sẽ chạy ở chế độ fallback (string replacement đơn giản).")

# ---------------------------------------------------------------------------
# Paths — tất cả tính relative từ thư mục demo-site
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).parent           # demo-site/scripts/
BASE_DIR     = SCRIPT_DIR.parent               # demo-site/
TEMPLATE_DIR = BASE_DIR / "templates"
DATA_DIR     = BASE_DIR / "data"
OUTPUT_DIR   = BASE_DIR / "cung"

# ---------------------------------------------------------------------------
# Đọc images.json — map tên điểm → path ảnh
# ---------------------------------------------------------------------------
_IMAGES_PATH = DATA_DIR / "images.json"
try:
    IMAGE_MAP: dict[str, str] = json.loads(_IMAGES_PATH.read_text(encoding="utf-8"))
except Exception as _e:
    print(f"[WARN] Không đọc được images.json: {_e}")
    IMAGE_MAP = {}

# ---------------------------------------------------------------------------
# Thứ tự ưu tiên chọn cover hero (slug thư mục poi)
# Ưu tiên: cảnh rộng (đầm/hồ/đồng/thung lũng) > kiến trúc > nội thất
# ---------------------------------------------------------------------------
COVER_HERO_PRIORITY = [
    "dam-sen-nguyet-farm",      # đầm sen — phong cảnh đặc trưng nhất MC
    "ho-baiboo",                # hồ Baibóo — mặt nước rộng
    "canh-dong-roc-eo",         # cánh đồng lúa Rộc Éo
    "thung-canh",               # Thung Cánh — thung lũng hoang sơ
    "doi-hoa-bo-moi",           # đồi hoa Bơ Môi
    "con-duong-tram",           # con đường Tràm — đặc trưng di sản
    "vuon-sim-co",              # vườn sim cổ
    "dong-huong-tich",          # động Hương Tích — cảnh rộng
    "chua-phu-coc",             # chùa Phú Cốc — kiến trúc tâm linh
    "tourism-hub-doi-dung",     # Hub Đồi Dùng
    "dinh-phu-coc",             # Đình Phú Cốc
    "chua-tien",                # chùa Tiên
    "den-cay-thoi",             # đền Cây Thợi
    "den-mau-ai-nang",          # đền Mẫu
    "hang-ho-den-quan-mai",     # hang Hổ — cảnh tự nhiên
    "nha-tho-giao-xu-bac-son",  # nhà thờ — kiến trúc Pháp
    "nha-san-ba-dien",          # nhà sàn
    "gio-nui-farmstay",         # Gió Núi farmstay
    "lamia-muong-coc",          # Lamia
    "bep-ruou-doi-ly",          # bếp rượu
    "co-la-muong",              # cỗ lá
    "ba-la-homestay",           # Bà Là homestay
    "nha-niem-nga",             # Nhà Niệm Nga
    "nha-tho-ho-ong-che",       # nhà thờ họ
    "farm-ca-qua",              # farm cá quả
    "ban-moc-muong-coc",        # bản Mộc
    "doi-duoc-lieu-roc-eo",     # đồi dược liệu
    "homestay-ong-kien",        # homestay ông Kiền
]

# ---------------------------------------------------------------------------
# Dữ liệu tĩnh dùng chung cho tất cả cung
# ---------------------------------------------------------------------------
HIGHLIGHT_ICONS  = ["🌱", "🪕", "🤝", "🍃", "⛩️", "🏔️", "🌊", "🎭", "🛶", "🌾"]
AUDIENCE_ICONS   = ["🌿", "👨‍👩‍👧", "👬", "🎓", "🌱", "🏔️", "🧘", "🎨"]
NOTE_ICONS       = ["🌧️", "💪", "🏛️", "🍶", "👘", "🚫", "🐝", "📌"]

# Icon mặc định cho loại tour (dùng trong poster)
TOUR_ICONS = {
    "xe-dap":    "🚲",
    "trek":      "🥾",
    "tour":      "🗺️",
    "night":     "🌙",
    "default":   "🗺️",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Chuyển tên điểm thành data-slot slug an toàn."""
    text = text.lower()
    text = re.sub(r"[&/\\]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text


def parse_gia(gia_str: str) -> str:
    """
    Trích phần số hoặc chuỗi hiển thị từ field 'gia'.
    VD: "650.000 đ/khách (gồm bữa trưa)" → "650K"
         "Liên hệ..."                      → "Liên hệ"
    """
    if not gia_str:
        return "Liên hệ"
    # Tìm số dạng 650.000 hoặc 650000
    m = re.search(r"(\d[\d.,]+)", gia_str)
    if m:
        raw = m.group(1).replace(".", "").replace(",", "")
        try:
            val = int(raw)
            if val >= 1_000_000:
                return f"{val // 1_000_000}M"
            elif val >= 1_000:
                return f"{val // 1_000}K"
            return str(val)
        except ValueError:
            pass
    return "Liên hệ"


def make_pg_label_cover(data: dict) -> str:
    """Tạo nhãn góc trang bìa, VD: 'CUNG ĐẠP XE A'."""
    loai = data.get("loai", "")
    label_map = {
        "xe-dap":  "CUNG ĐẠP XE",
        "trek":    "CUNG TREKKING",
        "tour":    "TOUR",
        "night":   "TOUR ĐÊM",
    }
    return label_map.get(loai, "CUNG TOUR")


def split_title(ten: str) -> list[str]:
    """
    Tách tên thành dòng 1 (từ đầu) và dòng 2 (phần còn lại in nghiêng).
    Logic: lấy 2 từ đầu làm dòng 1, còn lại là dòng 2.
    Nếu tên chỉ có 1-2 từ thì để nguyên 1 dòng.
    """
    words = ten.split()
    if len(words) <= 2:
        return [ten]
    # Dòng 1: 2 từ đầu; dòng 2: phần còn lại
    return [" ".join(words[:2]), " ".join(words[2:])]


def get_tour_icon(loai: str) -> str:
    return TOUR_ICONS.get(loai, TOUR_ICONS["default"])


def poi_slug_from_path(path: str) -> str:
    """
    Trích slug thư mục POI từ path.
    VD: "assets/img/poi/dam-sen-nguyet-farm/hero.jpg" → "dam-sen-nguyet-farm"
    """
    parts = path.split("/")
    if "poi" in parts:
        idx = parts.index("poi")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return ""


def img_src_for_poi(poi_name: str) -> str | None:
    """
    Tra images.json theo ĐÚNG chuỗi tên điểm.
    Trả về đường dẫn từ thư mục assets/ (relative to demo-site/)
    hoặc None nếu không có ảnh.
    """
    return IMAGE_MAP.get(poi_name)


def pick_cover_hero(data: dict) -> str | None:
    """
    Chọn 1 ảnh cover hero đẹp nhất cho cung này.
    Ưu tiên theo COVER_HERO_PRIORITY (cảnh rộng → kiến trúc → nội thất).

    Trả về path từ demo-site/ (VD: "assets/img/poi/.../hero.jpg")
    hoặc None nếu không có ảnh nào cho cung này.
    """
    # Cover đã gán sẵn (dedup xuyên cung) → ưu tiên
    slug = data.get("slug")
    if slug and slug in COVER_ASSIGN:
        return COVER_ASSIGN[slug]
    # Thu thập tất cả POI có trong cung
    all_poi_names: list[str] = []
    for d in data.get("diem_den", []):
        all_poi_names.append(d.get("ten", ""))
    for s in data.get("lich_trinh", []):
        all_poi_names.append(s.get("diem", ""))

    # Map poi_slug → (path, poi_name) cho những POI có ảnh
    available: dict[str, tuple[str, str]] = {}
    for name in all_poi_names:
        if not name:
            continue
        path = img_src_for_poi(name)
        if path:
            slug = poi_slug_from_path(path)
            if slug and slug not in available:
                available[slug] = (path, name)

    if not available:
        return None

    # Chọn theo thứ tự ưu tiên
    for priority_slug in COVER_HERO_PRIORITY:
        if priority_slug in available:
            return available[priority_slug][0]

    # Fallback: lấy cái đầu tiên
    return next(iter(available.values()))[0]


# ---- Cross-cung cover dedup: mỗi cung 1 cảnh riêng ----
COVER_ASSIGN: dict[str, str] = {}

def _cover_candidates(data: dict) -> dict[str, str]:
    names = [d.get("ten", "") for d in data.get("diem_den", [])] \
          + [s.get("diem", "") for s in data.get("lich_trinh", [])]
    avail: dict[str, str] = {}
    for name in names:
        if not name:
            continue
        path = img_src_for_poi(name)
        if path:
            sl = poi_slug_from_path(path)
            if sl and sl not in avail:
                avail[sl] = path
    return avail

def assign_covers(slugs: list[str]) -> None:
    """Gán cover distinct cho từng cung (greedy theo COVER_HERO_PRIORITY).
    Xử lý xe-đạp + cung A trước để được cảnh đẹp nhất."""
    rank = {"xe-dap": 0, "tour": 1, "trek": 2}
    def _order_key(s: str):
        lo = ""
        f = DATA_DIR / "tours" / f"{s}.json"
        if f.exists():
            try: lo = json.loads(f.read_text(encoding="utf-8")).get("loai", "")
            except Exception: lo = ""
        return (0 if s == "vong-xe-xanh" else 1, rank.get(lo, 3), s)
    slugs = sorted(slugs, key=_order_key)
    used: set[str] = set()
    for slug in slugs:
        f = DATA_DIR / "tours" / f"{slug}.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        avail = _cover_candidates(data)
        if not avail:
            continue
        chosen = None
        for ps in COVER_HERO_PRIORITY:          # scenic chưa dùng
            if ps in avail and ps not in used:
                chosen = ps; break
        if not chosen:                           # bất kỳ chưa dùng
            for ps in avail:
                if ps not in used:
                    chosen = ps; break
        if not chosen:                           # đành tái dùng
            for ps in COVER_HERO_PRIORITY:
                if ps in avail:
                    chosen = ps; break
            chosen = chosen or next(iter(avail))
        COVER_ASSIGN[slug] = avail[chosen]
        used.add(chosen)


def rel_img_path(path: str) -> str:
    """
    Chuyển path tuyệt đối từ demo-site/ sang tương đối từ cung/{slug}/.
    VD: "assets/img/poi/thung-canh/hero.jpg"
        → "../../assets/img/poi/thung-canh/hero.jpg"
    """
    return f"../../{path}"


def build_image_lookup(data: dict) -> dict[str, str]:
    """
    Xây lookup: tên điểm → đường dẫn ảnh tương đối từ cung/{slug}/.
    Chỉ gồm những điểm có ảnh trong IMAGE_MAP.
    """
    lookup: dict[str, str] = {}
    for d in data.get("diem_den", []):
        name = d.get("ten", "")
        path = img_src_for_poi(name)
        if name and path:
            lookup[name] = rel_img_path(path)
    for s in data.get("lich_trinh", []):
        name = s.get("diem", "")
        path = img_src_for_poi(name)
        if name and path and name not in lookup:
            lookup[name] = rel_img_path(path)
    return lookup


def build_context(data: dict) -> dict:
    """Xây dựng context dict đầy đủ cho Jinja2 template từ JSON data."""
    slug       = data["slug"]
    ten        = data["ten"]
    theme      = data.get("theme", "sinhthai")
    tagline    = data.get("tagline", "")
    thoi_luong = data.get("thoi_luong", "1 ngày")
    cu_ly      = data.get("cu_ly", "")
    quy_mo     = data.get("quy_mo", "2 – 12 khách")
    gia        = data.get("gia", "")
    intro      = data.get("intro", "")

    # Xử lý sections có thể rỗng
    highlights        = data.get("highlights", [])
    lich_trinh        = data.get("lich_trinh", [])
    diem_den          = data.get("diem_den", [])
    bao_gom           = data.get("bao_gom", [])
    khong_bao_gom     = data.get("khong_bao_gom", [])
    addon             = data.get("addon", [])
    farmstay_options  = data.get("farmstay_options", [])
    doi_tuong         = data.get("doi_tuong", [])
    luu_y             = data.get("luu_y", [])
    net_zero          = data.get("net_zero", "")
    lien_he           = data.get("lien_he", {
        "don_vi": "Ban Điều Phối Du Lịch Cộng Đồng Mường Cốc",
        "nguoi": "",
        "sdt": "",
        "fanpage": "Du lịch cộng đồng Mường Cốc",
    })

    # Image data
    cover_hero_path = pick_cover_hero(data)
    cover_hero_rel  = rel_img_path(cover_hero_path) if cover_hero_path else None
    image_lookup    = build_image_lookup(data)

    return {
        # Meta
        "slug":             slug,
        "ten":              ten,
        "theme":            theme,
        "tagline":          tagline,
        "thoi_luong":       thoi_luong,
        "cu_ly":            cu_ly,
        "quy_mo":           quy_mo,
        "gia":              gia,
        "gia_display":      parse_gia(gia),
        "intro":            intro,
        # Computed
        "ten_split":        split_title(ten),
        "pg_label_cover":   make_pg_label_cover(data),
        "tour_icon":        get_tour_icon(data.get("loai", "")),
        # Icons arrays
        "highlight_icons":  HIGHLIGHT_ICONS,
        "audience_icons":   AUDIENCE_ICONS,
        "note_icons":       NOTE_ICONS,
        # Data sections
        "highlights":       highlights,
        "lich_trinh":       lich_trinh,
        "diem_den":         diem_den,
        "bao_gom":          bao_gom,
        "khong_bao_gom":    khong_bao_gom,
        "addon":            addon,
        "farmstay_options": farmstay_options,
        "doi_tuong":        doi_tuong,
        "luu_y":            luu_y,
        "net_zero":         net_zero,
        "lien_he":          lien_he,
        # Image context (v2)
        "cover_hero":       cover_hero_rel,   # str | None — đường dẫn tương đối
        "images":           image_lookup,     # dict[tên điểm → rel path]
        # EN bilingual fields (lành tính nếu chưa có trong JSON — Jinja2 check `is defined`)
        "tagline_en":       data.get("tagline_en", ""),
        "intro_en":         data.get("intro_en", ""),
        "highlights_en":    data.get("highlights_en", []),
        "bao_gom_en":       data.get("bao_gom_en", []),
        "khong_bao_gom_en": data.get("khong_bao_gom_en", []),
        "net_zero_en":      data.get("net_zero_en", ""),
        "gia_en":           data.get("gia_en", ""),
    }


# ---------------------------------------------------------------------------
# Kiểm tra field JSON chưa được map
# ---------------------------------------------------------------------------
MAPPED_FIELDS = {
    # Core VN fields
    "slug", "ten", "loai", "theme", "tagline", "thoi_luong", "cu_ly",
    "quy_mo", "gia", "intro", "highlights", "lich_trinh", "diem_den",
    "bao_gom", "khong_bao_gom", "addon", "farmstay_options",
    "doi_tuong", "luu_y", "net_zero", "lien_he",
    # EN bilingual fields (added by bilingual expansion agent)
    "tagline_en", "intro_en", "highlights_en", "bao_gom_en", "khong_bao_gom_en",
    "net_zero_en", "gia_en", "thoi_luong_en",
    # Note: lich_trinh[].mo_ta_en, diem_den[].mo_ta_ngan_en,
    #       addon[].mo_ta_en, doi_tuong[].mo_ta_en, luu_y[].mo_ta_en
    # are nested inside list items — no top-level key to declare here
}

def find_unmapped_fields(data: dict) -> list[str]:
    """Trả về danh sách field có trong JSON nhưng chưa được generator map."""
    return [k for k in data.keys() if k not in MAPPED_FIELDS]


# ---------------------------------------------------------------------------
# Jinja2 render
# ---------------------------------------------------------------------------

def render_jinja2(template_name: str, context: dict) -> str:
    """Render template Jinja2, trả về HTML string."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
        # Cho phép undefined variable trả về chuỗi rỗng thay vì raise
        undefined=__import__("jinja2").Undefined,
    )
    # Custom filters
    env.filters["slugify"] = slugify
    # Tắt autoescaping cho các biến nội dung (đã kiểm soát nguồn data)
    env.autoescape = False

    tmpl = env.get_template(template_name)
    return tmpl.render(**context)


# ---------------------------------------------------------------------------
# Fallback: template đơn giản dùng str.replace (không cần Jinja2)
# WARN: chỉ xử lý các biến đơn giản, không có vòng lặp
# ---------------------------------------------------------------------------

def render_fallback(template_path: Path, context: dict) -> str:
    """
    Fallback khi Jinja2 chưa cài: thay thế {{variable}} đơn giản.
    Không xử lý vòng lặp {% for %} → chỉ dùng cho smoke test.
    """
    text = template_path.read_text(encoding="utf-8")
    # Thay thế các biến đơn giản {{ key }}
    for k, v in context.items():
        if isinstance(v, (str, int, float)):
            text = text.replace("{{ " + k + " }}", str(v))
            text = text.replace("{{" + k + "}}", str(v))
    # Xoá các khối {% ... %} còn sót
    text = re.sub(r"\{%.*?%\}", "", text, flags=re.DOTALL)
    # Xoá các {{ ... }} còn sót
    text = re.sub(r"\{\{.*?\}\}", "<!-- unmapped -->", text, flags=re.DOTALL)
    return text


# ---------------------------------------------------------------------------
# Generate một cung
# ---------------------------------------------------------------------------

def generate_cung(slug: str) -> bool:
    """
    Đọc data/{slug}.json → sinh cung/{slug}/brochure.html + poster.html.
    Trả về True nếu thành công.
    """
    json_path = DATA_DIR / "tours" / f"{slug}.json"
    if not json_path.exists():
        print(f"  [ERROR] Không tìm thấy: {json_path}")
        return False

    # Đọc và parse JSON
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  [ERROR] JSON không hợp lệ ({json_path}): {e}")
        return False

    # Kiểm tra field chưa map
    unmapped = find_unmapped_fields(data)
    if unmapped:
        print(f"  [INFO] Field JSON chưa map: {unmapped}")

    # Build context
    ctx = build_context(data)

    # Log image stats
    total_poi = len(data.get("diem_den", [])) + len(data.get("lich_trinh", []))
    img_count = len(ctx["images"])
    cover = ctx["cover_hero"] or "placeholder"
    print(f"  [IMG] cover_hero={cover}")
    print(f"  [IMG] image slots: {img_count} có ảnh / {total_poi} POI tổng")

    # Tạo output dir
    out_dir = OUTPUT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # Render
    for tmpl_name, out_name in [
        ("brochure.html.j2", "brochure.html"),
        ("poster.html.j2",   "poster.html"),
    ]:
        out_path = out_dir / out_name
        try:
            if JINJA2_OK:
                html = render_jinja2(tmpl_name, ctx)
            else:
                html = render_fallback(TEMPLATE_DIR / tmpl_name, ctx)
            out_path.write_text(html, encoding="utf-8")
            print(f"  [OK] {out_path.relative_to(BASE_DIR)}")
        except Exception as e:
            print(f"  [ERROR] Render {tmpl_name}: {e}")
            traceback.print_exc()
            return False

    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    # Xác định danh sách slug cần sinh
    if len(sys.argv) > 1:
        slugs = sys.argv[1:]
    else:
        # Sinh tất cả JSON trong data/tours/ (mỗi file = 1 cung/tour)
        slugs = sorted(p.stem for p in (DATA_DIR / "tours").glob("*.json"))
        if not slugs:
            print(f"[ERROR] Không tìm thấy file JSON nào trong {DATA_DIR}")
            sys.exit(1)

    print(f"[generate-cung] Jinja2={'OK' if JINJA2_OK else 'FALLBACK'}")
    print(f"[generate-cung] Template dir : {TEMPLATE_DIR}")
    print(f"[generate-cung] Output dir   : {OUTPUT_DIR}")
    print(f"[generate-cung] IMAGE_MAP    : {len(IMAGE_MAP)} entries")
    print(f"[generate-cung] Sẽ sinh {len(slugs)} cung: {', '.join(slugs)}\n")

    assign_covers(slugs)   # gán cover distinct trước khi sinh
    print(f"[generate-cung] Cover dedup: {len(COVER_ASSIGN)} cung gán cảnh riêng")

    ok_count = 0
    fail_slugs = []
    for slug in slugs:
        print(f"→ {slug}")
        if generate_cung(slug):
            ok_count += 1
        else:
            fail_slugs.append(slug)
        print()

    print(f"[generate-cung] Kết quả: {ok_count}/{len(slugs)} cung thành công.")
    if fail_slugs:
        print(f"[generate-cung] Lỗi tại: {', '.join(fail_slugs)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
