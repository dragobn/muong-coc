#!/usr/bin/env python3
"""
gen-qr.py — Sinh QR codes cho tất cả cung + landing + mymaps.
Màu: #0A6A2F (deep brand green) trên nền trắng.
Output: assets/qr/qr-{slug}.png, qr-landing.png, qr-mymaps.png
"""

import sys
from pathlib import Path

try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
except ImportError:
    print("[ERROR] Thiếu qrcode. Chạy: pip install qrcode[pil]")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
BASE_DIR   = SCRIPT_DIR.parent
QR_DIR     = BASE_DIR / "assets" / "qr"
QR_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://dragobn.github.io/muong-coc"

FILL_COLOR = "#0A6A2F"
BACK_COLOR = "white"

# Tất cả cung (19 slug, loại images + master-poi-coords)
DATA_DIR = BASE_DIR / "data"
SKIP = {"images", "master-poi-coords"}
CUNG_SLUGS = sorted(p.stem for p in DATA_DIR.glob("*.json") if p.stem not in SKIP)


def make_qr(url: str, out_path: Path) -> None:
    """Sinh QR code đơn giản, màu brand green, nền trắng."""
    qr = qrcode.QRCode(
        version=None,           # auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color=FILL_COLOR, back_color=BACK_COLOR)
    img.save(str(out_path))
    print(f"  [OK] {out_path.name} → {url}")


def main():
    targets: list[tuple[str, str]] = []

    # 19 cung
    for slug in CUNG_SLUGS:
        url = f"{BASE_URL}/cung/{slug}/"
        fname = f"qr-cung-{slug}.png"
        targets.append((url, fname))

    # Landing
    targets.append((f"{BASE_URL}/", "qr-landing.png"))

    # Google My Maps
    targets.append((
        "https://www.google.com/maps/d/viewer?mid=1hNSY53YglDigLPa4YQzp13XTxxnTbHM",
        "qr-mymaps.png",
    ))

    print(f"[gen-qr] Sinh {len(targets)} QR → {QR_DIR}")
    for url, fname in targets:
        out = QR_DIR / fname
        make_qr(url, out)

    print(f"[gen-qr] DONE — {len(targets)} QR đã lưu tại {QR_DIR}")


if __name__ == "__main__":
    main()
