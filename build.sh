#!/usr/bin/env bash
# build.sh — sinh toàn bộ web tĩnh Mường Cốc (dùng cho Cloudflare Pages).
# Build command trên Cloudflare Pages: bash build.sh
set -e
python3 scripts/generate-poi.py
python3 scripts/generate-cung.py
python3 scripts/generate-web.py
python3 scripts/generate-tin-tuc.py
python3 scripts/generate-trai-nghiem.py
echo "[build.sh] Hoàn tất."
