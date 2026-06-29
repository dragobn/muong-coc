#!/usr/bin/env python3
"""
generate-trai-nghiem.py — Sinh trang 2 trải nghiệm cốt lõi Mường Cốc.
Output: trai-nghiem/<slug>/index.html (mobile-first, timeline).
Nội dung VN (nguồn docx GĐ20). Poster Canva sẽ nhúng sau khi có ảnh export.
"""
import html
from pathlib import Path

BASE = Path(__file__).parent.parent
OUT = BASE / "trai-nghiem"
TEL = "+84962029198"
TEL_SHOW = "0962 029 198"
FB_URL = "https://www.facebook.com/profile.php?id=61575640444733"
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:'
         'ital,wght@0,500;0,600;0,700&family=Be+Vietnam+Pro:wght@300;400;500;600;700&display=swap" rel="stylesheet">')


def e(s):
    return html.escape(str(s or ""))


EXTRA_CSS = """
.tn-hero{position:relative;padding:54px 22px 30px;text-align:center;background:linear-gradient(160deg,var(--green-dark),var(--green));color:#fff}
.tn-hero .kicker{letter-spacing:.14em;text-transform:uppercase;font-size:.74rem;opacity:.9}
.tn-hero h1{font-family:var(--serif,'Cormorant Garamond',serif);font-size:2.3rem;margin:10px 0 6px;line-height:1.15}
.tn-hero .tagline{font-style:italic;opacity:.95;margin:0 auto;max-width:560px}
.tn-meta{max-width:760px;margin:0 auto;padding:18px 22px;display:flex;flex-wrap:wrap;gap:10px 20px;justify-content:center;border-bottom:1px solid #e6e0d4}
.tn-meta div{font-size:.92rem;color:var(--ink)}
.tn-meta b{color:var(--green-dark)}
.tn-sec{max-width:760px;margin:0 auto;padding:26px 22px}
.tn-sec h2{font-family:var(--serif,serif);color:var(--green-dark);font-size:1.5rem;margin:0 0 12px}
.tn-sec p{line-height:1.7;margin:0 0 12px}
.tn-intro{background:var(--cream)}
.timeline{position:relative;max-width:760px;margin:0 auto;padding:8px 22px 26px}
.tl-item{position:relative;padding:0 0 22px 70px}
.tl-item:before{content:"";position:absolute;left:54px;top:6px;bottom:-6px;width:2px;background:#e0d8c8}
.tl-item:last-child:before{display:none}
.tl-time{position:absolute;left:0;top:2px;width:46px;text-align:right;font-weight:700;color:var(--green);font-size:.8rem;line-height:1.2}
.tl-dot{position:absolute;left:48px;top:4px;width:14px;height:14px;border-radius:50%;background:var(--green);border:3px solid #fff;box-shadow:0 0 0 1px var(--green)}
.tl-item h3{margin:0 0 4px;font-size:1.05rem;color:var(--ink)}
.tl-item .sub{color:var(--amber);font-size:.9rem;font-style:italic;margin:0 0 6px}
.tl-item p{margin:0 0 8px;line-height:1.65;color:#3a3530;font-size:.96rem}
.tl-item ul{margin:4px 0 8px;padding-left:1.1em}
.tl-item li{margin:2px 0}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
.chips span{background:#eef5ee;color:var(--green-dark);border-radius:999px;padding:6px 13px;font-size:.86rem}
.incl{display:grid;gap:8px;margin:8px 0}
.incl .yes:before{content:"✔ ";color:var(--green)}
.incl .no:before{content:"✘ ";color:#b44}
.tn-cta{background:var(--green-dark);color:#fff;text-align:center;padding:30px 22px}
.tn-cta a{color:#fff;font-weight:700}
.tn-cta .btn{display:inline-block;margin-top:12px;background:#fff;color:var(--green-dark);padding:12px 22px;border-radius:999px;text-decoration:none;font-weight:700}
.tn-hero.has-photo{background-size:cover;background-position:center}
.tl-img{width:100%;border-radius:12px;margin:6px 0 10px;aspect-ratio:16/10;object-fit:cover;display:block}
.tn-gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;max-width:760px;margin:0 auto;padding:4px 22px 8px}
.tn-gallery img{width:100%;height:130px;object-fit:cover;border-radius:10px}
"""


def head(title, desc, og):
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:image" content="{og}">
{FONTS}
<link rel="stylesheet" href="../../assets/css/site.css">
<style>{EXTRA_CSS}</style>
</head>
<body>
<div class="wrap">
<nav class="topbar">
  <a class="brand" href="../../"><span class="logo-sm"><img src="../../assets/img/logo-muong-coc.png" alt="Logo Mường Cốc"></span>
  <span class="brand-tx">Du lịch cộng đồng Mường Cốc</span></a>
  <a class="home-link" href="../../">← Trang chủ</a>
</nav>"""


def foot():
    return f"""<section class="tn-cta">
  <div>📞 Hotline: <a href="tel:{TEL}">{TEL_SHOW}</a> · 🌐 <a href="{FB_URL}" target="_blank" rel="noopener">Fanpage</a></div>
  <a class="btn" href="../../">Khám phá toàn bộ điểm đến →</a>
  <p style="opacity:.85;margin:14px 0 0;font-size:.9rem">Mường Cốc — Chạm vào bình yên</p>
</section>
</div>
<script src="../../assets/js/site.js"></script>
</body>
</html>"""


def render(exp):
    h = head(exp["title"] + " — Mường Cốc", exp["tagline"], exp["og"])
    hb = exp.get("hero_img")
    hstyle = f" style=\"background-image:linear-gradient(rgba(8,40,20,.45),rgba(8,55,28,.72)),url('{hb}')\"" if hb else ""
    hcls = "tn-hero has-photo" if hb else "tn-hero"
    h += f'<header class="{hcls}"{hstyle}><div class="kicker">Trải nghiệm cốt lõi Mường Cốc</div><h1>{e(exp["title"])}</h1><p class="tagline">{e(exp["tagline"])}</p></header>'
    h += '<div class="tn-meta">' + "".join(f'<div><b>{e(k)}:</b> {e(v)}</div>' for k, v in exp["meta"]) + '</div>'
    h += '<section class="tn-sec tn-intro"><h2>Giới thiệu</h2>' + "".join(f"<p>{e(p)}</p>" for p in exp["intro"]) + '</section>'
    if exp.get("gallery"):
        h += '<div class="tn-gallery">' + "".join(f'<img loading="lazy" src="{e(g)}" alt="Mường Cốc">' for g in exp["gallery"]) + '</div>'
    # timeline
    h += '<section class="tn-sec"><h2>Lịch trình trong ngày</h2></section><div class="timeline">'
    for it in exp["timeline"]:
        h += '<div class="tl-item"><div class="tl-time">' + e(it["time"]) + '</div><div class="tl-dot"></div>'
        h += '<h3>' + e(it["head"]) + '</h3>'
        if it.get("sub"):
            h += '<p class="sub">' + e(it["sub"]) + '</p>'
        if it.get("img"):
            h += f'<img class="tl-img" loading="lazy" src="{e(it["img"])}" alt="{e(it["head"])}">'
        for p in it.get("body", []):
            h += '<p>' + e(p) + '</p>'
        if it.get("list"):
            h += '<ul>' + "".join(f"<li>{e(x)}</li>" for x in it["list"]) + '</ul>'
        h += '</div>'
    h += '</div>'
    # extra sections
    for sec in exp.get("sections", []):
        h += '<section class="tn-sec"><h2>' + e(sec["h"]) + '</h2>'
        for p in sec.get("p", []):
            h += '<p>' + e(p) + '</p>'
        if sec.get("chips"):
            h += '<div class="chips">' + "".join(f"<span>{e(x)}</span>" for x in sec["chips"]) + '</div>'
        if sec.get("incl"):
            h += '<div class="incl">' + "".join(f'<div class="{c}">{e(t)}</div>' for c, t in sec["incl"]) + '</div>'
        h += '</section>'
    h += foot()
    d = OUT / exp["slug"]
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(h, encoding="utf-8")
    print(f"[OK] trai-nghiem/{exp['slug']}/index.html")


EXP1 = {
    "slug": "mot-ngay-lam-nguoi-muong",
    "title": "Một ngày làm người Mường",
    "tagline": "Chạm vào bình yên – Sống như một người Mường thực thụ",
    "og": "/assets/img/poi/co-la-muong/hero.jpg",
    "hero_img": "/assets/img/poi/co-la-muong/hero.jpg",
    "gallery": ["/assets/img/poi/nha-tho-ho-ong-che/02.jpg", "/assets/img/poi/gio-nui-farmstay/02.jpg",
                "/assets/img/poi/ban-moc-muong-coc/02.jpg", "/assets/img/poi/nha-niem-nga/02.jpg",
                "/assets/img/poi/tourism-hub-doi-dung/02.jpg", "/assets/img/poi/dam-sen-nguyet-farm/hero.jpg"],
    "meta": [("Thời lượng", "01 ngày (08h00 – 17h30)"), ("Điểm đến", "DLCĐ Mường Cốc, xã Mỹ Đức, Hà Nội"),
             ("Quy mô", "08 – 30 khách"), ("Phù hợp", "Gia đình · học sinh · đoàn nghiên cứu · khách quốc tế")],
    "intro": [
        "Có những chuyến đi để ngắm nhìn. Có những chuyến đi để nghỉ ngơi. Nhưng cũng có những chuyến đi để trở thành một phần của cộng đồng bản địa.",
        "“Một ngày làm người Mường” là chương trình trải nghiệm nhập vai đầu tiên của Mường Cốc — du khách không chỉ tham quan mà được sống trọn vẹn trong nhịp sinh hoạt thường nhật của một gia đình người Mường giữa lòng Thủ đô.",
        "Trong một ngày, du khách khoác trang phục truyền thống, học vài câu tiếng Mường, chăm vườn, cho cá ăn, bẻ ngô, nhặt trứng, nướng cơm lam, đánh cồng chiêng, hát dân ca, chơi trò chơi dân gian và cùng gieo một mầm xanh cho tương lai.",
        "Chương trình tiên phong thực hành Bộ tiêu chí 5 KHÔNG, Mường Cốc Refill Station và mô hình du lịch cộng đồng hướng tới Net Zero.",
    ],
    "timeline": [
        {"time": "08h00", "head": "Chào đón tại Tourism Hub Đồi Dùng", "img": "/assets/img/poi/tourism-hub-doi-dung/hero.jpg",
         "body": ["Đón tiếp bằng chén trà thảo dược Mường ấm nóng; giới thiệu Bản Mường giữa lòng Thủ đô, Bộ tiêu chí 5 Không, mạng lưới Refill Station và định hướng Net Zero.",
                  "Mỗi khách nhận túi vải Mường Cốc, khăn đội đầu, bản đồ trải nghiệm và thẻ “Người Mường một ngày”."]},
        {"time": "08h30", "head": "Hóa thân thành người Mường", "sub": "Gặp gỡ chủ nhà ông Chế", "img": "/assets/img/poi/nha-tho-ho-ong-che/hero.jpg",
         "body": ["Khoác trang phục Mường (áo pắn, váy Mường, khăn đội đầu, túi thổ cẩm) dưới sự hướng dẫn của các bà, các mẹ trong bản.",
                  "Học những câu giao tiếp tiếng Mường, nghe ông Chế kể chuyện nhà sàn, phong tục, tín ngưỡng và vai trò của cồng chiêng."]},
        {"time": "09h30", "head": "Gió Núi Farmstay — mô hình VAC", "sub": "Chạm tay vào nông nghiệp xanh", "img": "/assets/img/poi/gio-nui-farmstay/hero.jpg",
         "body": ["Gia đình anh Nguyễn Quốc Tuấn & chị Lê Thị Hải Yến đón đoàn vào nhịp sống nhà nông thực thụ."],
         "list": ["Cho cá ăn bên ao làng", "Thu hoạch rau sạch theo mùa", "Bẻ ngô · đào khoai · nhặt trứng", "Lùa vịt về chuồng · cho gà ăn", "Tìm hiểu mô hình Vườn – Ao – Chuồng", "Khu trưng bày nông cụ cổ ngoài trời"]},
        {"time": "11h00", "head": "Leave a Green Footprint", "sub": "Gieo một mầm xanh",
         "body": ["Mỗi khách trồng một cây thuốc Nam, cây ăn quả hoặc hoa bản địa; gắn biển tên, đánh dấu trên bản đồ số và nhận chứng nhận “Tôi đã để lại một dấu chân xanh tại Mường Cốc.”"]},
        {"time": "11h30", "head": "Mộc Mường Cốc Farmstay", "sub": "Bữa cơm người Mường", "img": "/assets/img/poi/ban-moc-muong-coc/hero.jpg",
         "body": ["Lớp thực hành ẩm thực: nướng cơm lam, giã bánh, gói lá chuối, pha muối hạt dổi, chuẩn bị rau rừng.",
                  "Quây quần bên Mâm Cỗ Lá Mường: gà đồi, cá ao, cơm lam, thịt hấp lá chuối, canh lá đắng, rau rừng, trà sen, rượu cần."]},
        {"time": "13h30", "head": "Trạm Chill Farmstay", "sub": "Khoảng lặng giữa bản Mường",
         "body": ["Ngâm chân nước lá thuốc, thưởng trà thảo mộc, hoặc workshop: đan lát, ướp trà sen, thu hái thuốc Nam, làm túi thơm thảo dược."]},
        {"time": "14h30", "head": "Nét Thanh — Không gian văn hóa Mường", "sub": "Giữ hồn quê – Lan tỏa bản sắc", "img": "/assets/img/poi/nha-niem-nga/hero.jpg",
         "body": ["Nghe chuyện trang phục Mường, học may vá thêu thùa cùng nghệ nhân; làm móc khóa/túi thơm từ vải thổ cẩm tái chế theo tinh thần du lịch xanh."],
         "list": ["Workshop “Em làm cô gái Mường” (trẻ em)", "Workshop “Một mũi kim giữ hồn Mường”", "Túi thơm thảo dược Mường", "Túi vải Net Zero từ thổ cẩm tái chế"]},
        {"time": "15h00", "head": "Nhà Văn hóa Đồi Dùng", "sub": "Học làm nghệ nhân Mường",
         "body": ["Học những nhịp cồng chiêng đầu tiên, tập hát dân ca, múa Mường cùng nghệ nhân địa phương."]},
        {"time": "16h00", "head": "Vui chơi dân gian", "sub": "Trở về tuổi thơ",
         "list": ["Đi cà kheo", "Kéo co", "Ném còn", "Bịt mắt bắt vịt", "Ô ăn quan", "Nhảy sạp"]},
        {"time": "17h00", "head": "Khép lại hành trình", "sub": "Trở về Tourism Hub",
         "body": ["Nhận giấy chứng nhận “Tôi đã là người Mường một ngày” cùng quà nhỏ: túi trà thuốc Mường, hạt giống hoa đồng nội, trà sen, thiệp lưu niệm ghi vị trí cây đã trồng."]},
    ],
    "sections": [
        {"h": "Bốn trụ cột trải nghiệm", "chips": ["Nông nghiệp xanh & kinh tế tuần hoàn (VAC)", "Ẩm thực bản địa – Farm to Table", "Thủ công & trang phục truyền thống", "Di sản văn hóa phi vật thể"]},
    ],
}

EXP2 = {
    "slug": "vac-gio-nui-farmstay",
    "title": "Một ngày làm nhà nông — VAC Gió Núi Farmstay",
    "tagline": "Chạm vào bình yên – Một ngày làm nhà nông thực thụ",
    "og": "/assets/img/poi/gio-nui-farmstay/hero.jpg",
    "hero_img": "/assets/img/poi/gio-nui-farmstay/hero.jpg",
    "gallery": ["/assets/img/poi/gio-nui-farmstay/02.jpg", "/assets/img/poi/gio-nui-farmstay/03.jpg",
                "/assets/img/poi/canh-dong-roc-eo/hero.jpg", "/assets/img/poi/doi-hoa-bo-moi/hero.jpg"],
    "meta": [("Thời lượng", "01 ngày (08h00 – 17h00) · hoặc 1 ngày 1 đêm"), ("Địa điểm", "Gió Núi Farmstay, xã Mỹ Đức, Hà Nội"),
             ("Loại hình", "Nông nghiệp & nông thôn · Farm to Table · Net Zero"), ("Phù hợp", "Gia đình · học sinh · nhóm bạn · team building xanh")],
    "intro": [
        "Có những chuyến đi để nghỉ ngơi. Cũng có những chuyến đi để được xắn tay làm, để hiểu một hạt gạo, một con cá đến từ đâu.",
        "“Một ngày làm nhà nông” tại Gió Núi Farmstay — mô hình VAC (Vườn – Ao – Chuồng) đầu tiên ở Mường Cốc mở cửa đón khách — đưa du khách thành người nông dân thực thụ trong một ngày: cho cá ăn, chăn trâu, bắt cá, hái rau, rồi tự tay nấu mâm cơm Farm to Table từ chính sản vật vừa thu hoạch.",
    ],
    "timeline": [
        {"time": "08h00", "head": "Chào đón tại Gió Núi Farmstay", "img": "/assets/img/poi/gio-nui-farmstay/02.jpg", "body": ["Trà thảo mộc nhà trồng; giới thiệu mô hình VAC tuần hoàn, 5 Không và cam kết Net Zero. Nhận nón lá, ủng, giỏ tre."]},
        {"time": "08h30", "head": "Vào chuồng — cho gà vịt ăn, nhặt trứng", "body": ["Rải thóc cho đàn gà – vịt, lùa vịt ra ao, nhặt những quả trứng còn ấm trong ổ."]},
        {"time": "09h15", "head": "Cắt cỏ cho cá ăn", "body": ["Cắt cỏ voi, bó lại, rải xuống ao cho đàn cá trắm — hiểu nguyên lý “vườn nuôi ao, ao nuôi vườn”."]},
        {"time": "10h00", "head": "Chăn trâu trên đồng", "img": "/assets/img/poi/canh-dong-roc-eo/hero.jpg", "body": ["Dắt trâu ra đồng cỏ, tập làm mục đồng, chụp ảnh giữa khung cảnh đồng quê bản Mường."]},
        {"time": "10h45", "head": "Hái rau & trồng rau theo mùa", "img": "/assets/img/poi/doi-hoa-bo-moi/hero.jpg", "body": ["Thu hoạch rau vườn theo mùa; tự tay gieo một luống rau — để lại dấu chân xanh cho farmstay."]},
        {"time": "11h15", "head": "Kéo vó & câu cá dưới ao", "body": ["Lội ao kéo vó, buông cần câu cá. Cá bắt được mang thẳng vào bếp."]},
        {"time": "12h00", "head": "Ăn trưa — Mâm cơm Farm to Table", "img": "/assets/img/poi/co-la-muong/hero.jpg", "body": ["Tự xiên nướng cá vừa bắt trên than hồng (chấm muối mắc khén), cùng gia chủ nấu mâm cơm nhà nông: gà đồi, rau vườn, trứng, canh quê — tất cả từ vườn ra mâm."]},
        {"time": "13h30", "head": "Nghỉ trưa thảnh thơi", "body": ["Ngả lưng trên võng/nhà sàn, nghe gió núi, thưởng trà."]},
        {"time": "14h30", "head": "Đạp xe quanh vườn & bản", "body": ["Đạp xe vòng vườn cây – bờ ao – đường làng, ngắm cảnh đồng quê."]},
        {"time": "15h30", "head": "Lửa chiều — nướng ngô, khoai", "body": ["Nhóm bếp lửa nhỏ, nướng ngô – khoai, chơi vài trò dân gian."]},
        {"time": "16h30", "head": "Thu hoạch quà mang về", "body": ["Gói ghém rau sạch, trứng gà, sản vật vườn nhà làm quà; chụp ảnh lưu niệm cùng gia chủ."]},
        {"time": "17h00", "head": "Chia tay Gió Núi Farmstay"},
        {"time": "19h00", "head": "Đêm lửa trại nhà nông", "sub": "Lựa chọn nếu đi 1 ngày 1 đêm", "body": ["Đốt lửa trại, giao lưu văn nghệ, kể chuyện đồng quê và nghỉ đêm tại farmstay."]},
    ],
    "sections": [
        {"h": "Điểm nhấn hành trình", "chips": ["Làm nhà nông thực thụ 1 ngày", "Mô hình VAC tuần hoàn đầu tiên", "Tự bắt cá – tự nướng – tự nấu", "Cho gà vịt, chăn trâu, hái rau", "Sống chậm, sống xanh, Net Zero"]},
        {"h": "Dịch vụ", "incl": [
            ("yes", "Hướng dẫn viên / chủ nhà bản địa đồng hành cả ngày"),
            ("yes", "Toàn bộ hoạt động trải nghiệm VAC"),
            ("yes", "Bữa trưa Mâm cơm Farm to Table từ sản vật tại vườn"),
            ("yes", "Trà thảo mộc, ngô – khoai nướng buổi chiều"),
            ("yes", "Dụng cụ trải nghiệm; quà nông sản mang về; nước uống; bảo hiểm du lịch"),
            ("no", "Đưa đón Hà Nội – Mường Cốc"),
            ("no", "Lưu trú qua đêm (nếu chọn 1N1Đ)"),
            ("no", "Chi phí cá nhân ngoài chương trình"),
        ]},
    ],
}

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    render(EXP1)
    render(EXP2)
    print("Xong: 2 trang trải nghiệm.")
