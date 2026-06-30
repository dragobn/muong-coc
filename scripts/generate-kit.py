#!/usr/bin/env python3
"""
generate-kit.py — Sinh trang Destination Kit (/kit/index.html).
Trang tổng quan "at a glance" cho khách quét QR: 2 trải nghiệm cốt lõi +
lưới toàn bộ tour (nhóm) + cẩm nang. Tái dùng dữ liệu & cover từ generate-web.py.
"""
import importlib.util
from pathlib import Path

SCRIPTS = Path(__file__).parent
BASE = SCRIPTS.parent
spec = importlib.util.spec_from_file_location("gweb", SCRIPTS / "generate-web.py")
gw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gw)  # định nghĩa GROUPS, COVERS, load, t3, head, topbar, tail...

t3, e, load = gw.t3, gw.e, gw.load
PFX = "../"  # /kit/ -> gốc site

KIT_CSS = """
.kit-hero{position:relative;min-height:62vh;display:flex;flex-direction:column;justify-content:flex-end;
  padding:40px 22px 30px;color:#fff;background-size:cover;background-position:center}
.kit-hero::after{content:"";position:absolute;inset:0;background:linear-gradient(to top,rgba(8,30,16,.86),rgba(8,30,16,.15) 60%,rgba(8,30,16,.35));z-index:0}
.kit-hero>*{position:relative;z-index:1}
.kit-hero .kick{letter-spacing:.16em;text-transform:uppercase;font-size:.72rem;opacity:.92}
.kit-hero h1{font-family:var(--serif,'Cormorant Garamond',serif);font-size:2.5rem;line-height:1.1;margin:8px 0 6px}
.kit-hero p{margin:0;max-width:600px;opacity:.95}
.kit-sec{max-width:1000px;margin:0 auto;padding:30px 20px 6px}
.kit-sec h2{font-family:var(--serif,serif);color:var(--green-dark);font-size:1.55rem;margin:0 0 4px}
.kit-sec .lead{color:#4a443d;line-height:1.7;margin:6px 0 0}
.kit-five{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 0}
.kit-five span{background:#eef5ee;color:var(--green-dark);border-radius:999px;padding:6px 13px;font-size:.84rem}
.kit-exp{display:grid;grid-template-columns:1fr;gap:14px;max-width:1000px;margin:14px auto 0;padding:0 20px}
@media(min-width:680px){.kit-exp{grid-template-columns:1fr 1fr}}
.kit-exp a{position:relative;display:block;border-radius:16px;overflow:hidden;min-height:200px;text-decoration:none;color:#fff;box-shadow:var(--shadow)}
.kit-exp a img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.kit-exp a .ov{position:absolute;inset:0;background:linear-gradient(to top,rgba(8,30,16,.9),rgba(8,30,16,.05) 70%)}
.kit-exp a .tx{position:absolute;left:0;right:0;bottom:0;padding:16px 18px;z-index:1}
.kit-exp .badge{display:inline-block;background:var(--amber);color:#fff;font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:4px 10px;border-radius:999px;margin-bottom:8px}
.kit-exp h3{margin:0 0 4px;font-size:1.2rem;font-family:var(--serif,serif)}
.kit-exp p{margin:0;font-size:.9rem;opacity:.95}
.kit-grp{max-width:1000px;margin:0 auto;padding:18px 20px 0}
.kit-grp h2{font-size:1.25rem;color:var(--green-dark);margin:0 0 12px;display:flex;align-items:center;gap:8px}
.kit-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:14px}
.kit-card{display:flex;flex-direction:column;border:1px solid #e6e0d4;border-radius:14px;overflow:hidden;background:#fff;text-decoration:none;color:inherit;transition:box-shadow .2s,transform .2s}
.kit-card:hover{box-shadow:0 8px 22px rgba(0,0,0,.09);transform:translateY(-2px)}
.kit-card img{width:100%;height:115px;object-fit:cover;background:#eee}
.kit-card .cd{padding:10px 12px 13px}
.kit-card h4{margin:0 0 5px;font-size:.98rem;line-height:1.25}
.kit-card .meta{font-size:.8rem;color:var(--muted);display:flex;flex-wrap:wrap;gap:3px 10px}
.kit-card .meta b{color:var(--amber);font-weight:600}
.kit-camnang{max-width:1000px;margin:24px auto 0;padding:0 20px}
.kit-camnang a{display:flex;align-items:center;gap:14px;background:linear-gradient(135deg,var(--green),var(--green-dark));color:#fff;text-decoration:none;padding:16px 20px;border-radius:16px;box-shadow:var(--shadow)}
.kit-camnang b{font-family:var(--serif,serif);font-size:1.15rem;display:block}
.kit-camnang small{opacity:.9;font-size:.82rem}
"""


def tour_card(slug):
    d = load(slug)
    cover = gw.COVERS.get(slug) or "assets/img/thung-canh.jpg"
    name = t3(d.get("ten", ""), d.get("ten_en"), d.get("ten_fr"))
    tl = t3(d.get("thoi_luong", ""), d.get("thoi_luong_en"), d.get("thoi_luong_fr"))
    gia = d.get("gia", "")
    meta = f'<span>{tl}</span>' + (f'<span><b>{e(gia)}</b></span>' if gia else "")
    return (f'<a class="kit-card" href="{PFX}cung/{slug}/">'
            f'<img loading="lazy" src="{PFX}{e(cover)}" alt="{e(d.get("ten",""))}">'
            f'<div class="cd"><h4>{name}</h4><div class="meta">{meta}</div></div></a>')


def render():
    parts = [gw.head(
        "Cẩm nang điểm đến — Du lịch cộng đồng Mường Cốc",
        "Bộ cẩm nang điểm đến Mường Cốc: trải nghiệm cốt lõi, các cung tour và cẩm nang du lịch.",
        PFX, "assets/img/thung-canh.jpg")]
    parts.append(f"<style>{KIT_CSS}</style>")
    parts.append(gw.topbar(PFX, with_home=True))

    # HERO
    parts.append(f'''<header class="kit-hero" style="background-image:url('{PFX}assets/img/thung-canh.jpg')">
  <div class="kick">{t3("Cẩm nang điểm đến", "Destination Kit", "Kit de destination")}</div>
  <h1>{t3("Du lịch cộng đồng Mường Cốc", "Muong Coc Community Tourism", "Tourisme communautaire Mường Cốc")}</h1>
  <p>{t3("Chạm vào bình yên — chọn ngôn ngữ ở góc trên rồi khám phá trải nghiệm và các cung tour.",
         "Touch the stillness — pick your language above, then explore experiences and tours.",
         "Toucher la quiétude — choisissez la langue en haut, puis explorez.")}</p>
</header>''')

    # TỔNG QUAN + 5 KHÔNG
    five = ["Không thực phẩm bẩn", "Không hoá chất độc hại", "Không rác nhựa một lần",
            "Không mất bản sắc", "Không du lịch giả tạo"]
    five_en = ["No unsafe food", "No toxic chemicals", "No single-use plastic", "No loss of identity", "No fake tourism"]
    five_fr = ["Aucun aliment douteux", "Aucun produit toxique", "Aucun plastique jetable", "Aucune perte d'identité", "Aucun tourisme artificiel"]
    chips = "".join(f'<span>{t3(v, en, fr)}</span>' for v, en, fr in zip(five, five_en, five_fr))
    parts.append(f'''<section class="kit-sec">
  <h2>{t3("Bản Mường giữa lòng Thủ đô", "A Muong village near Hanoi", "Un village Mường près de Hanoï")}</h2>
  <p class="lead">{t3("Mường Cốc (xã Mỹ Đức, Hà Nội) — du lịch cộng đồng xanh, hướng tới Net Zero, với cam kết 5 KHÔNG.",
                      "Muong Coc (My Duc, Hanoi) — green community tourism toward Net Zero, with a 5-NO pledge.",
                      "Mường Cốc (Mỹ Đức, Hanoï) — tourisme communautaire vert vers le Net Zero, engagement des 5 NON.")}</p>
  <div class="kit-five">{chips}</div>
</section>''')

    # 2 TRẢI NGHIỆM CỐT LÕI
    parts.append(f'<section class="kit-sec"><h2>{t3("Hai trải nghiệm cốt lõi", "Two signature experiences", "Deux expériences phares")}</h2></section>')
    exp = [
        ("mot-ngay-lam-nguoi-muong", "assets/img/poi/co-la-muong/hero.jpg",
         ("Một ngày làm người Mường", "One day as a Muong", "Un jour en Mường"),
         ("Nhập vai trọn vẹn nhịp sống người Mường", "Live a full day of Muong village life", "Vivez une journée Mường")),
        ("vac-gio-nui-farmstay", "assets/img/poi/gio-nui-farmstay/hero.jpg",
         ("Một ngày làm nhà nông (VAC)", "One day as a farmer (VAC)", "Un jour fermier (VAC)"),
         ("Mô hình Vườn–Ao–Chuồng tại Gió Núi Farmstay", "Garden–Pond–Barn model at Gio Nui Farmstay", "Modèle Jardin–Étang–Étable")),
    ]
    cards = ""
    for slug, img, (tv, te, tf), (sv, se, sf) in exp:
        cards += (f'<a href="{PFX}trai-nghiem/{slug}/"><img loading="lazy" src="{PFX}{img}" alt="{e(tv)}"><div class="ov"></div>'
                  f'<div class="tx"><span class="badge">{t3("Cốt lõi", "Signature", "Phare")}</span>'
                  f'<h3>{t3(tv, te, tf)}</h3><p>{t3(sv, se, sf)}</p></div></a>')
    parts.append(f'<div class="kit-exp">{cards}</div>')

    # LƯỚI TOUR THEO NHÓM
    parts.append(f'<section class="kit-sec"><h2>{t3("Các cung & tour", "Routes & tours", "Parcours & circuits")}</h2></section>')
    for icon, label, slugs in gw.GROUPS:
        title = t3(label["vi"], label["en"], label["fr"])
        grid = "".join(tour_card(s) for s in slugs)
        parts.append(f'<section class="kit-grp"><h2>{icon} {title} <span style="font-weight:400;color:var(--muted);font-size:.9rem">({len(slugs)})</span></h2><div class="kit-grid">{grid}</div></section>')

    # CẨM NANG
    parts.append(f'''<div class="kit-camnang"><a href="/assets/cam-nang-muong-coc.pdf" target="_blank" rel="noopener">
  <span style="font-size:1.9rem">📖</span>
  <span><b>{t3("Cẩm nang du lịch Mường Cốc", "Muong Coc Travel Guidebook", "Guide de voyage Mường Cốc")}</b>
  <small>{t3("Bản đầy đủ (PDF) — 60 trang song ngữ", "Full guidebook (PDF) — 60 bilingual pages", "Guide complet (PDF)")}</small></span></a></div>''')

    parts.append(gw.tail(PFX))
    out = BASE / "kit" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"[OK] kit/index.html ({sum(len(s) for _,_,s in gw.GROUPS)} tour + 2 trải nghiệm)")


if __name__ == "__main__":
    render()
