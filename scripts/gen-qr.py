#!/usr/bin/env python3
"""
gen-qr.py — Sinh QR codes cho tất cả cung + landing + mymaps + bản đồ per-cung.
Màu: #0A6A2F (deep brand green) trên nền trắng.
Output:
  assets/qr/qr-cung-{slug}.png   — microsite cung (T1 cover + poster)
  assets/qr/qr-map-{slug}.png    — Google My Maps bản đồ cung riêng (T4 brochure)
  assets/qr/qr-landing.png       — trang chủ
  assets/qr/qr-mymaps.png        — bản đồ tổng (backward compat)
"""

import json
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

BASE_URL   = "https://dragobn.github.io/muong-coc"
MAPS_BASE  = "https://www.google.com/maps/d/viewer?mid="

FILL_COLOR = "#0A6A2F"
BACK_COLOR = "white"

# Tất cả cung (19 slug, loại file reference không phải cung)
DATA_DIR = BASE_DIR / "data"
SKIP = {"images", "master-poi-coords", "map-mids", "poi-i18n", "poi-i18n-strings"}
CUNG_SLUGS = sorted(p.stem for p in DATA_DIR.glob("*.json") if p.stem not in SKIP)

# Đọc map-mids.json — slug → mid Google My Maps
_MIDS_PATH = DATA_DIR / "map-mids.json"
try:
    MAP_MIDS: dict[str, str] = json.loads(_MIDS_PATH.read_text(encoding="utf-8"))
except Exception as e:
    print(f"[WARN] Không đọc được map-mids.json: {e}")
    MAP_MIDS = {}

MID_TONG = MAP_MIDS.get("_tong", "1hNSY53YglDigLPa4YQzp13XTxxnTbHM")


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

    # --- QR microsite (T1 cover + poster) — KHÔNG thay đổi ---
    for slug in CUNG_SLUGS:
        url = f"{BASE_URL}/cung/{slug}/"
        targets.append((url, f"qr-cung-{slug}.png"))

    # --- QR bản đồ per-cung (T4 brochure) — MID riêng, fallback _tong ---
    for slug in CUNG_SLUGS:
        mid = MAP_MIDS.get(slug, MID_TONG)
        url = f"{MAPS_BASE}{mid}"
        targets.append((url, f"qr-map-{slug}.png"))

    # Landing
    targets.append((f"{BASE_URL}/", "qr-landing.png"))

    # Google My Maps tổng (backward compat — qr-mymaps.png vẫn giữ)
    targets.append((f"{MAPS_BASE}{MID_TONG}", "qr-mymaps.png"))

    print(f"[gen-qr] Sinh {len(targets)} QR → {QR_DIR}")
    for url, fname in targets:
        out = QR_DIR / fname
        make_qr(url, out)

    print(f"[gen-qr] DONE — {len(targets)} QR đã lưu tại {QR_DIR}")


if __name__ == "__main__":
    main()
