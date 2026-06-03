#!/usr/bin/env python3
"""
render-print-screenshot.py — RENDER bộ in bằng SCREENSHOT (thay print-to-PDF).

Lý do: Chrome --print-to-pdf hay sinh "ô đen sau chữ" + lỗi nền. Screenshot
raster giữ nguyên pixel đúng như trình duyệt hiển thị → KHÔNG box đen.

Pipeline mỗi cung:
  1. Tách từng .page của brochure (8) / poster (2) thành HTML tạm (ẩn page khác).
  2. Chrome headless --screenshot @ 300dpi (force-device-scale-factor=3.125).
  3. PIL crop về đúng kích thước 300dpi (bù off-by-1 do làm tròn CSS mm→px).
  4. img2pdf ghép PNG → RGB PDF khổ đúng (A4/A5 + bleed 3mm).
  5. gs convert RGB PDF (đã raster) → CMYK prepress cho nhà in.

Dùng:
  python3 scripts/render-print-screenshot.py                 # 19 cung
  python3 scripts/render-print-screenshot.py vong-xe-xanh    # 1 cung

Output: print/{slug}/brochure.pdf (CMYK), print/{slug}/poster.pdf (CMYK)
"""

import sys
import os
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
import img2pdf

# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
BASE_DIR   = SCRIPT_DIR.parent
CUNG_DIR   = BASE_DIR / "cung"
PRINT_DIR  = BASE_DIR / "print"

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
GS     = "/opt/homebrew/bin/gs"

DPI   = 300
SCALE = DPI / 96.0          # 3.125 — CSS px (96dpi) → raster px (300dpi)

# Khổ bleed (mm): brochure A4+3mm, poster A5+3mm
BROCHURE_W_MM, BROCHURE_H_MM = 216.0, 303.0
POSTER_W_MM,   POSTER_H_MM   = 154.0, 216.0


def mm_to_px(mm: float, dpi: int = DPI) -> int:
    return round(mm / 25.4 * dpi)


def mm_to_csspx(mm: float) -> float:
    return mm / 25.4 * 96.0


# ---------------------------------------------------------------------------
# Tách 1 .page thành HTML độc lập
# Chiến lược: chèn <style> ẩn mọi .page trừ .page thứ idx (nth-of-type theo
# thứ tự xuất hiện), reset body, ép page hiển thị ở top-left, in màu exact.
# ---------------------------------------------------------------------------
ISOLATE_CSS_TMPL = """
<style id="__isolate__">
  html, body {{ margin:0 !important; padding:0 !important; background:#ffffff !important; }}
  * {{ -webkit-print-color-adjust:exact !important; print-color-adjust:exact !important; }}
  .page {{ display:none !important; }}
  .page:nth-of-type({n}) {{
    display:block !important;
    margin:0 !important;
    box-shadow:none !important;
    page-break-after:auto !important;
    transform:none !important;
  }}
</style>
"""


def count_pages(html: str) -> int:
    return len(re.findall(r'class="[^"]*\bpage\b', html))


def make_isolated_html(html: str, page_index_1based: int) -> str:
    """Trả về HTML chỉ hiển thị .page thứ N (1-based theo nth-of-type)."""
    inject = ISOLATE_CSS_TMPL.format(n=page_index_1based)
    if "</head>" in html:
        return html.replace("</head>", inject + "</head>", 1)
    return inject + html


def screenshot_page(src_html: Path, page_idx: int, out_png: Path,
                    w_mm: float, h_mm: float) -> bool:
    """Render 1 trang ra PNG 300dpi bằng Chrome --screenshot."""
    html = src_html.read_text(encoding="utf-8")
    iso = make_isolated_html(html, page_idx)

    # File tạm cùng thư mục src để giữ nguyên relative path (../../assets ...)
    tmp = src_html.parent / f".__tmp_render_{src_html.stem}_{page_idx}.html"
    tmp.write_text(iso, encoding="utf-8")

    css_w = round(mm_to_csspx(w_mm))
    css_h = round(mm_to_csspx(h_mm))

    raw_png = out_png.with_suffix(".raw.png")
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        "--run-all-compositor-stages-before-draw",
        "--disable-features=TranslateUI",
        "--disable-extensions",
        "--no-first-run",
        "--default-background-color=00000000",
        f"--force-device-scale-factor={SCALE}",
        f"--window-size={css_w},{css_h}",
        "--virtual-time-budget=8000",   # chờ font + ảnh load
        f"--screenshot={raw_png}",
        f"file://{tmp}",
    ]
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        tmp.unlink(missing_ok=True)
        return False
    finally:
        tmp.unlink(missing_ok=True)

    if not raw_png.exists():
        return False

    # Crop/pad về đúng kích thước 300dpi (bù off-by-1 do làm tròn)
    target_w = mm_to_px(w_mm)
    target_h = mm_to_px(h_mm)
    im = Image.open(raw_png).convert("RGB")
    if im.size != (target_w, target_h):
        canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
        canvas.paste(im, (0, 0))
        im = canvas.crop((0, 0, target_w, target_h))
    im.save(out_png, "PNG")
    raw_png.unlink(missing_ok=True)
    return True


def pngs_to_pdf(pngs: list[Path], out_pdf: Path, w_mm: float, h_mm: float) -> None:
    """Ghép PNG → PDF khổ chính xác (mm). img2pdf nhúng ảnh không nén lại."""
    layout = img2pdf.get_layout_fun(
        (img2pdf.mm_to_pt(w_mm), img2pdf.mm_to_pt(h_mm))
    )
    with open(out_pdf, "wb") as f:
        f.write(img2pdf.convert([str(p) for p in pngs], layout_fun=layout))


def rgb_to_cmyk(in_pdf: Path, out_pdf: Path) -> bool:
    cmd = [
        GS, "-q", "-dBATCH", "-dNOPAUSE", "-dNOSAFER",
        "-sDEVICE=pdfwrite",
        "-dColorConversionStrategy=/CMYK",
        "-dProcessColorModel=/DeviceCMYK",
        "-dPDFSETTINGS=/prepress",
        "-dCompatibilityLevel=1.4",
        "-dAutoRotatePages=/None",
        "-dDownsampleColorImages=false",
        "-dDownsampleGrayImages=false",
        f"-sOutputFile={out_pdf}",
        str(in_pdf),
    ]
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_pdf.exists()
    except subprocess.CalledProcessError:
        return False


def render_doc(slug: str, kind: str, w_mm: float, h_mm: float,
               expect_pages: int) -> bool:
    """kind = 'brochure' | 'poster'."""
    src = CUNG_DIR / slug / f"{kind}.html"
    if not src.exists():
        print(f"    [WARN] {kind}.html không tồn tại")
        return False

    n = count_pages(src.read_text(encoding="utf-8"))
    if n != expect_pages:
        print(f"    [WARN] {kind}: phát hiện {n} .page (kỳ vọng {expect_pages})")
    if n == 0:
        return False

    out_dir = PRINT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    png_dir = out_dir / f"{kind}-png"
    png_dir.mkdir(exist_ok=True)

    pngs = []
    for i in range(1, n + 1):
        out_png = png_dir / f"p{i:02d}.png"
        ok = screenshot_page(src, i, out_png, w_mm, h_mm)
        if not ok:
            print(f"    [ERROR] screenshot {kind} trang {i} thất bại")
            return False
        pngs.append(out_png)
    print(f"    [SHOT] {kind}: {len(pngs)} PNG @ {DPI}dpi")

    rgb_pdf = out_dir / f"{kind}-rgb.pdf"
    pngs_to_pdf(pngs, rgb_pdf, w_mm, h_mm)

    cmyk_pdf = out_dir / f"{kind}.pdf"
    if not rgb_to_cmyk(rgb_pdf, cmyk_pdf):
        print(f"    [ERROR] gs CMYK {kind} thất bại")
        return False
    rgb_pdf.unlink(missing_ok=True)
    print(f"    [OK] print/{slug}/{kind}.pdf (CMYK)")
    return True


def render_cung(slug: str) -> bool:
    print(f"→ {slug}")
    if not (CUNG_DIR / slug).is_dir():
        print(f"    [SKIP] cung/{slug} không tồn tại")
        return False
    only = os.environ.get("ONLY_KIND", "").strip()  # "brochure"|"poster"|"" (cả 2)
    b = p = True
    if only in ("", "brochure"):
        b = render_doc(slug, "brochure", BROCHURE_W_MM, BROCHURE_H_MM, 8)
    if only in ("", "poster"):
        p = render_doc(slug, "poster",   POSTER_W_MM,   POSTER_H_MM,   2)
    return b and p


def main():
    if not Path(CHROME).exists():
        print(f"[ERROR] Chrome không tìm thấy: {CHROME}"); sys.exit(1)
    if not Path(GS).exists():
        print(f"[ERROR] gs không tìm thấy: {GS}"); sys.exit(1)

    if len(sys.argv) > 1:
        slugs = sys.argv[1:]
    else:
        slugs = sorted(p.name for p in CUNG_DIR.iterdir() if p.is_dir())

    print(f"[render-screenshot] DPI={DPI} scale={SCALE}")
    print(f"[render-screenshot] {len(slugs)} cung\n")

    ok, fail = 0, []
    for slug in slugs:
        if render_cung(slug):
            ok += 1
        else:
            fail.append(slug)
        print()

    print(f"[render-screenshot] Kết quả: {ok}/{len(slugs)} cung OK")
    if fail:
        print(f"[render-screenshot] Lỗi: {', '.join(fail)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
