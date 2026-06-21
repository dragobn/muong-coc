#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gom ảnh theo từng chương trình (17 tour/cung) thành album rời để anh trim.
Nguồn ảnh: assets/img/poi/<folder>/ (map qua data/images.json + diem_den mỗi tour).
Output: album-anh/<slug>/ (ảnh copy) + index.html gallery; album-anh/index.html tổng.
"""
import json, os, shutil

ROOT = os.path.join(os.path.dirname(__file__), "..")
POI = os.path.join(ROOT, "assets", "img", "poi")
OUT = os.path.join(ROOT, "album-anh")
IMG = json.load(open(os.path.join(ROOT, "data", "images.json"), encoding="utf-8"))

PROGRAMS = [
    ("Tour 1 – Thiên nhiên 1N", "tour-1n-thien-nhien"),
    ("Tour 2 – Văn hoá sen & Mo Mường 1N", "tour-1n-van-hoa-sen"),
    ("Tour 3 – Thiên nhiên 2N1Đ", "tour-2n-thien-nhien"),
    ("Tour 4 – Sen & Mo Mường 2N1Đ", "tour-2n-van-hoa-sen"),
    ("Tour 5 – Trekking Hương Tích 3N2Đ", "tour-3n-huong-tich"),
    ("Tour 6 – Quảng Phú Cầu 1N", "tour-kn-quang-phu-cau"),
    ("Tour 7 – Chùa Hương 1N", "tour-kn-chua-huong"),
    ("Tour 8 – Cúc Phương 2N1Đ", "tour-kn-cuc-phuong"),
    ("Tour 9 – Mai Châu–Pù Luông 3–4N", "tour-kn-mai-chau-pu-luong"),
    ("Cung C1 – Vòng Xe Xanh", "vong-xe-xanh"),
    ("Cung C2 – Theo Dòng Ái Nàng", "theo-dong-ai-nang"),
    ("Cung C3 – Dấu Xưa Mường Cốc", "dau-xua-muong-coc"),
    ("Cung C4 – Hồn Mường Bên Hồ Baibóo", "hon-muong-ho-baiboo"),
    ("Cung C5 – Về Miền Di Sản", "ve-mien-di-san"),
    ("Cung C6 – Xanh Giữa Lòng Mường Cốc", "xanh-giua-long"),
    ("Cung C7 – Hương Đồng Bơ Môi", "huong-dong-bo-moi"),
    ("Cung C8 – Nhịp Sống Mường Bơ Môi", "nhip-song-bo-moi"),
]
EXT = (".jpg", ".jpeg", ".png", ".webp")

def folder_of(name):
    p = IMG.get(name) or IMG.get((name or "").strip())
    if p and "/poi/" in p:
        return p.split("/poi/")[1].split("/")[0]
    return None

def poi_list(slug):
    d = json.load(open(os.path.join(ROOT, "data", "tours", slug + ".json"), encoding="utf-8"))
    out = []
    for x in (d.get("diem_den") or []):
        f = folder_of(x.get("ten"))
        if f and f not in [o[1] for o in out]:
            out.append((x.get("ten"), f))
    return out

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

cards = []
for ten, slug in PROGRAMS:
    dst = os.path.join(OUT, slug)
    os.makedirs(dst)
    imgs = []  # (filename, caption)
    for poi_ten, fol in poi_list(slug):
        src_dir = os.path.join(POI, fol)
        if not os.path.isdir(src_dir):
            continue
        for fn in sorted(os.listdir(src_dir)):
            if fn.lower().endswith(EXT):
                newname = f"{fol}__{fn}"
                shutil.copy2(os.path.join(src_dir, fn), os.path.join(dst, newname))
                imgs.append((newname, poi_ten))
    # gallery html
    items = "\n".join(
        f'<figure><img src="{fn}" loading="lazy"><figcaption>{cap}</figcaption></figure>'
        for fn, cap in imgs)
    html = f"""<!doctype html><html lang="vi"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Album ảnh — {ten}</title>
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;margin:0;background:#f4f1ea;color:#243}}
header{{background:#2E6B4F;color:#fff;padding:18px 24px}}
header h1{{margin:0;font-size:20px}} header p{{margin:4px 0 0;opacity:.85;font-size:13px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;padding:18px}}
figure{{margin:0;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px #0002}}
figure img{{width:100%;height:170px;object-fit:cover;display:block}}
figcaption{{padding:8px 10px;font-size:12px;color:#456}}
a.back{{color:#fff;text-decoration:none;font-size:13px}}
</style>
<header><a class="back" href="../index.html">← Tất cả chương trình</a>
<h1>{ten}</h1><p>{len(imgs)} ảnh · gom từ các điểm đến trong chương trình · anh trim thêm/bớt tuỳ ý</p></header>
<div class="grid">{items}</div></html>"""
    with open(os.path.join(dst, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    cards.append((ten, slug, len(imgs)))

# index tổng
cards_html = "\n".join(
    f'<a class="card" href="{slug}/index.html"><b>{ten}</b><span>{n} ảnh</span></a>'
    for ten, slug, n in cards)
idx = f"""<!doctype html><html lang="vi"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Album ảnh các tour Mường Cốc</title>
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;margin:0;background:#f4f1ea;color:#243}}
header{{background:#2E6B4F;color:#fff;padding:22px 24px}}
header h1{{margin:0;font-size:22px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;padding:20px}}
.card{{background:#fff;border-radius:12px;padding:18px;text-decoration:none;color:#243;
box-shadow:0 1px 4px #0002;display:flex;justify-content:space-between;align-items:center}}
.card b{{font-size:15px}} .card span{{color:#2E6B4F;font-weight:700;font-size:13px}}
</style>
<header><h1>Album ảnh — 17 chương trình Du lịch cộng đồng Mường Cốc</h1></header>
<div class="grid">{cards_html}</div></html>"""
with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
    f.write(idx)

print("Album dir:", os.path.abspath(OUT))
total = sum(n for _, _, n in cards)
for ten, slug, n in cards:
    print(f"  {n:3} ảnh  {slug}")
print("Tổng ảnh:", total)
