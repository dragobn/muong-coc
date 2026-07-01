#!/usr/bin/env python3
"""
generate-kit.py — Sinh Destination Kit (/kit/index.html) — BẢN SỐ HOÁ của poster A1.
Hiển thị POSTER thumbnails (không phải ảnh chụp), gom nhóm như poster tổng A1:
  Các cung Tour · 2 Trải nghiệm trung tâm · Các cung Đạp xe.
Bấm poster -> lật brochure (flipbook). Style xanh-kem-vàng đồng bộ poster.
Thumbnail: assets/kit-posters/<slug>.jpg (cắt từ print/<slug>/poster.pdf).
Tái dùng GROUPS/load/t3 từ generate-web.py.
"""
import importlib.util
from pathlib import Path

SCRIPTS = Path(__file__).parent
BASE = SCRIPTS.parent
spec = importlib.util.spec_from_file_location("gweb", SCRIPTS / "generate-web.py")
gw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gw)
t3, e, load = gw.t3, gw.e, gw.load
PFX = "../"

# Nhóm theo A1: Đạp xe (8) / Tour+Trek = "Các cung Tour" / 2 trải nghiệm trung tâm
G = {g[2][0] if False else None: None for g in []}  # noop
DAPXE = next(s for i, s in enumerate([grp[2] for grp in gw.GROUPS]) if gw.GROUPS[i][0] == "🚲")
TOUR = []
for icon, _, slugs in gw.GROUPS:
    if icon in ("🌾", "🥾"):
        TOUR += slugs

KIT_CSS = """
*{box-sizing:border-box}
html,body{overflow-x:hidden;max-width:100%;margin:0;background:var(--cream)}
.kh{background:linear-gradient(135deg,var(--green-dark),var(--green));color:#fff;text-align:center;padding:26px 20px 20px;border-bottom:3px solid var(--gold)}
.kh .logo{width:64px;height:64px;border-radius:50%;background:#fff;padding:5px;margin:0 auto 10px;display:block;object-fit:contain}
.kh h1{font-family:var(--serif,'Cormorant Garamond',serif);font-size:clamp(1.6rem,6.5vw,2.4rem);margin:0;line-height:1.1;overflow-wrap:break-word}
.kh h1 em{color:var(--gold);font-style:italic}
.kh .sub{font-style:italic;opacity:.95;margin:6px 0 12px;font-size:.98rem}
.kh .strip{display:inline-flex;flex-wrap:wrap;justify-content:center;gap:6px 14px;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;
  background:rgba(0,0,0,.18);border-radius:999px;padding:7px 16px}
.kh .strip b{color:var(--gold)}
.kintro{max-width:900px;margin:0 auto;padding:20px 20px 4px;text-align:center}
.kintro p{color:#4a443d;line-height:1.7;margin:0 auto;max-width:620px}
.kfive{display:flex;flex-wrap:wrap;gap:7px;justify-content:center;margin:12px 0 0}
.kfive span{background:#eef5ee;color:var(--green-dark);border-radius:999px;padding:5px 12px;font-size:.8rem}
.ksec{max-width:1000px;margin:0 auto;padding:22px 16px 2px}
.ksec .lbl{display:flex;align-items:center;gap:10px;justify-content:center;margin:0 0 4px}
.ksec .lbl h2{font-family:var(--serif,serif);color:var(--green-dark);font-size:1.5rem;margin:0}
.ksec .lbl .n{color:var(--muted);font-size:.85rem}
.ksec .rule{height:2px;background:linear-gradient(90deg,transparent,var(--gold),transparent);max-width:220px;margin:0 auto 16px}
.pgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
@media(min-width:560px){.pgrid{grid-template-columns:repeat(3,1fr)}}
@media(min-width:860px){.pgrid{grid-template-columns:repeat(4,1fr)}}
.pcard{display:block;text-decoration:none;color:inherit;border-radius:12px;overflow:hidden;background:#fff;
  box-shadow:0 3px 12px rgba(0,0,0,.09);transition:transform .18s,box-shadow .18s}
.pcard:active,.pcard:hover{transform:translateY(-3px);box-shadow:0 10px 24px rgba(0,0,0,.16)}
.pcard img{width:100%;height:auto;display:block;background:#e9e4d8}
.pcard .cap{padding:8px 10px 11px;font-size:.86rem;font-weight:600;line-height:1.25;text-align:center;color:var(--green-dark)}
.pcard .cap .flip{display:block;font-weight:400;font-size:.72rem;color:var(--amber);margin-top:3px}
/* 2 trải nghiệm trung tâm — nổi bật hơn */
.kcore{display:grid;grid-template-columns:1fr;gap:14px;max-width:820px;margin:0 auto}
@media(min-width:620px){.kcore{grid-template-columns:1fr 1fr}}
.kcore a{position:relative;display:block;border-radius:16px;overflow:hidden;min-height:210px;text-decoration:none;color:#fff;box-shadow:0 4px 16px rgba(0,0,0,.16)}
.kcore a img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.kcore a .ov{position:absolute;inset:0;background:linear-gradient(to top,rgba(8,30,16,.92),rgba(8,30,16,.05) 72%)}
.kcore a .tx{position:absolute;left:0;right:0;bottom:0;padding:16px 18px;z-index:1}
.kcore .badge{display:inline-block;background:var(--gold);color:#3a2c05;font-size:.68rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;padding:4px 10px;border-radius:999px;margin-bottom:8px}
.kcore h3{margin:0 0 4px;font-size:1.25rem;font-family:var(--serif,serif)}
.kcore p{margin:0;font-size:.9rem;opacity:.95}
.kcam{max-width:1000px;margin:22px auto 0;padding:0 16px}
.kcam a{display:flex;align-items:center;gap:14px;background:#fff;border:1px solid var(--gold);color:var(--green-dark);text-decoration:none;padding:15px 18px;border-radius:16px}
.kcam b{font-family:var(--serif,serif);font-size:1.12rem;display:block}
.kcam small{color:var(--muted);font-size:.82rem}
.kfoot{background:linear-gradient(135deg,var(--green-dark),var(--green));color:#fff;text-align:center;padding:26px 20px;margin-top:28px}
.kfoot .r{margin:5px 0;font-size:.92rem}.kfoot a{color:var(--gold);text-decoration:none;font-weight:600}
.kfoot .cl{font-family:var(--serif,serif);font-style:italic;font-size:1.15rem;margin:0 0 10px}
"""


def pcard(slug):
    d = load(slug)
    return (f'<a class="pcard" href="{PFX}flipbook/{slug}/">'
            f'<img loading="lazy" src="{PFX}assets/kit-posters/{slug}.jpg" alt="{e(d.get("ten",""))}">'
            f'<div class="cap">{e(d.get("ten",""))}<span class="flip">Lật xem brochure ›</span></div></a>')


def render():
    P = [gw.head("Cẩm nang điểm đến — Bộ sản phẩm Tour Mường Cốc",
                 "Bộ sản phẩm tour Du lịch cộng đồng Mường Cốc: 2 trải nghiệm trung tâm, các cung tour và cung đạp xe.",
                 PFX, "assets/img/thung-canh.jpg")]
    P.append(f"<style>{KIT_CSS}</style>")
    P.append(gw.topbar(PFX, with_home=True))

    # HEADER kiểu A1
    P.append(f'''<header class="kh">
  <img class="logo" src="{PFX}assets/img/logo-muong-coc.png" alt="Logo Mường Cốc">
  <h1>{t3("Bộ sản phẩm Tour", "Muong Coc Tour Collection", "Collection de circuits")} <em>Mường Cốc</em></h1>
  <div class="sub">{t3("18 cung trải nghiệm · hướng tới Net Zero", "18 experiences · toward Net Zero", "18 expériences · vers le Net Zero")}</div>
  <div class="strip"><span><b>{len(TOUR)}</b> {t3("Cung Tour","Tours","Circuits")}</span><span><b>{len(DAPXE)}</b> {t3("Cung Đạp xe","Cycling","Vélo")}</span><span><b>02</b> {t3("Trải nghiệm trung tâm","Signature","Phares")}</span></div>
</header>''')

    # INTRO + 5 KHÔNG
    five = list(zip(
        ["Không thực phẩm bẩn", "Không hoá chất độc hại", "Không rác nhựa một lần", "Không mất bản sắc", "Không du lịch giả tạo"],
        ["No unsafe food", "No toxic chemicals", "No single-use plastic", "No loss of identity", "No fake tourism"],
        ["Aucun aliment douteux", "Aucun produit toxique", "Aucun plastique jetable", "Aucune perte d'identité", "Aucun tourisme artificiel"]))
    chips = "".join(f'<span>{t3(v, en, fr)}</span>' for v, en, fr in five)
    P.append(f'''<section class="kintro">
  <p>{t3("Mường Cốc (xã Mỹ Đức, Hà Nội) — bản Mường giữa lòng Thủ đô. Chọn ngôn ngữ ở góc trên; chạm mỗi poster để lật xem chương trình đầy đủ.",
         "Muong Coc (My Duc, Hanoi) — a Muong village near Hanoi. Pick your language above; tap a poster to flip through the full brochure.",
         "Mường Cốc (Mỹ Đức, Hanoï) — un village Mường près de Hanoï. Touchez un poster pour feuilleter la brochure.")}</p>
  <div class="kfive">{chips}</div>
</section>''')

    # 2 TRẢI NGHIỆM TRUNG TÂM
    P.append(f'<section class="ksec"><div class="lbl"><h2>{t3("2 Trải nghiệm trung tâm", "2 Signature experiences", "2 Expériences phares")}</h2></div><div class="rule"></div></section>')
    core = [
        ("mot-ngay-lam-nguoi-muong", "assets/img/poi/co-la-muong/hero.jpg",
         ("Một ngày làm người Mường", "One day as a Muong", "Un jour en Mường"),
         ("Nhập vai trọn nhịp sống bản Mường", "Full immersion in Muong village life", "Immersion dans la vie Mường")),
        ("vac-gio-nui-farmstay", "assets/img/poi/gio-nui-farmstay/hero.jpg",
         ("Một ngày làm nhà nông (VAC)", "One day as a farmer (VAC)", "Un jour fermier (VAC)")
         , ("Mô hình Vườn–Ao–Chuồng, Gió Núi Farmstay", "Garden–Pond–Barn model", "Modèle Jardin–Étang–Étable")),
    ]
    cc = ""
    for slug, img, (tv, te, tf), (sv, se, sf) in core:
        cc += (f'<a href="{PFX}trai-nghiem/{slug}/"><img loading="lazy" src="{PFX}{img}" alt="{e(tv)}"><div class="ov"></div>'
               f'<div class="tx"><span class="badge">{t3("Trung tâm","Signature","Phare")}</span><h3>{t3(tv,te,tf)}</h3><p>{t3(sv,se,sf)}</p></div></a>')
    P.append(f'<div class="kcore" style="padding:0 16px">{cc}</div>')

    # CÁC CUNG TOUR
    P.append(f'<section class="ksec"><div class="lbl"><h2>🌾 {t3("Các cung Tour","Tour routes","Circuits")}</h2><span class="n">({len(TOUR)})</span></div><div class="rule"></div>'
             f'<div class="pgrid">{"".join(pcard(s) for s in TOUR)}</div></section>')

    # CÁC CUNG ĐẠP XE
    P.append(f'<section class="ksec"><div class="lbl"><h2>🚲 {t3("Các cung Đạp xe","Cycling routes","Parcours à vélo")}</h2><span class="n">({len(DAPXE)})</span></div><div class="rule"></div>'
             f'<div class="pgrid">{"".join(pcard(s) for s in DAPXE)}</div></section>')

    # CẨM NANG
    P.append(f'''<div class="kcam"><a href="/assets/cam-nang-muong-coc.pdf" target="_blank" rel="noopener">
  <span style="font-size:1.9rem">📖</span><span><b>{t3("Cẩm nang du lịch Mường Cốc","Muong Coc Guidebook","Guide Mường Cốc")}</b>
  <small>{t3("Bản đầy đủ (PDF) — 60 trang song ngữ","Full guidebook (PDF) — 60 pages","Guide complet (PDF)")}</small></span></a></div>''')

    # FOOTER liên hệ (kiểu A1)
    P.append(f'''<footer class="kfoot">
  <div class="cl">Chạm vào bình yên</div>
  <div class="r">📞 Hotline: <a href="tel:+84962029198">0962 029 198</a></div>
  <div class="r">🌐 <a href="https://www.facebook.com/profile.php?id=61575640444733" target="_blank" rel="noopener">Fanpage: Du lịch cộng đồng Mường Cốc</a></div>
  <div class="r">🔗 <a href="{PFX}">dulichcongdongmuongcoc.vn</a></div>
  <div class="r" style="opacity:.85;font-size:.82rem;margin-top:8px">Tourism Hub Đồi Dùng · xã Mỹ Đức · Hà Nội</div>
</footer>''')
    P.append(f'{gw.fab()}\n<script src="{PFX}assets/js/site.js"></script>\n</div>\n</body>\n</html>')

    out = BASE / "kit" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(P), encoding="utf-8")
    print(f"[OK] kit/index.html — {len(TOUR)} tour + {len(DAPXE)} đạp xe + 2 trải nghiệm (poster thumbnails)")


if __name__ == "__main__":
    render()
