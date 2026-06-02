#!/usr/bin/env bash
# render-print-cmyk.sh — Chrome headless → RGB PDF → gs CMYK PDF
# Dùng: bash scripts/render-print-cmyk.sh [slug1 slug2 ...]
# Không có arg → render tất cả 19 cung trong cung/
#
# Output: print/{slug}/brochure.pdf  (CMYK, 216×303mm bleed A4)
#         print/{slug}/poster.pdf    (CMYK, 154×216mm bleed A5)
#
# Yêu cầu: Google Chrome (headless), gs 10+
# ------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CUNG_DIR="$BASE_DIR/cung"
PRINT_DIR="$BASE_DIR/print"

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
GS="/opt/homebrew/bin/gs"

# Kiểm tra dependencies
if [[ ! -x "$CHROME" ]]; then
  echo "[ERROR] Chrome không tìm thấy tại: $CHROME"; exit 1
fi
if [[ ! -x "$GS" ]]; then
  echo "[ERROR] Ghostscript không tìm thấy tại: $GS"; exit 1
fi

# GS args chung — CMYK prepress, no trim marks
GS_CMYK_ARGS=(
  -q -dBATCH -dNOPAUSE -dNOSAFER
  -sDEVICE=pdfwrite
  -dColorConversionStrategy=/CMYK
  -dProcessColorModel=/DeviceCMYK
  -dPDFSETTINGS=/prepress
  -dCompatibilityLevel=1.4
  -dEmbedAllFonts=true
  -dSubsetFonts=true
  -dCompressPages=true
  -dAutoRotatePages=/None
)

# Chrome headless PDF flags — disable animations, no sandbox, deterministic
CHROME_ARGS=(
  --headless=new
  --disable-gpu
  --no-sandbox
  --disable-dev-shm-usage
  --run-all-compositor-stages-before-draw
  --disable-features=TranslateUI
  --hide-scrollbars
  --disable-extensions
  --no-first-run
)

# ------------------------------------------------------------------
# html_to_pdf <html_path> <out_pdf> <paper_width_mm> <paper_height_mm>
# Render HTML → RGB PDF via Chrome headless
# ------------------------------------------------------------------
html_to_pdf() {
  local html_path="$1"
  local out_pdf="$2"
  local w_mm="$3"   # bleed width mm (e.g. 216 brochure, 154 poster)
  local h_mm="$4"   # bleed height mm (e.g. 303 brochure, 216 poster)

  "$CHROME" "${CHROME_ARGS[@]}" \
    --print-to-pdf="$out_pdf" \
    --print-to-pdf-no-header \
    --no-margins-for-pdf \
    --paper-width="$(echo "scale=4; $w_mm/25.4" | bc)" \
    --paper-height="$(echo "scale=4; $h_mm/25.4" | bc)" \
    "file://$html_path" 2>/dev/null
}

# ------------------------------------------------------------------
# rgb_to_cmyk <in_pdf> <out_pdf>
# Convert RGB PDF → CMYK PDF via Ghostscript
# ------------------------------------------------------------------
rgb_to_cmyk() {
  local in_pdf="$1"
  local out_pdf="$2"
  "$GS" "${GS_CMYK_ARGS[@]}" -sOutputFile="$out_pdf" "$in_pdf"
}

# ------------------------------------------------------------------
# render_cung <slug>
# ------------------------------------------------------------------
render_cung() {
  local slug="$1"
  local cung_dir="$CUNG_DIR/$slug"
  local out_dir="$PRINT_DIR/$slug"

  if [[ ! -d "$cung_dir" ]]; then
    echo "  [SKIP] cung/$slug không tồn tại — chạy generate-cung.py trước"
    return 1
  fi

  mkdir -p "$out_dir"

  local ok=0

  # --- Brochure (8 trang A4 + bleed 216×303mm) ---
  local br_html="$cung_dir/brochure.html"
  local br_rgb="$out_dir/brochure-rgb.pdf"
  local br_cmyk="$out_dir/brochure.pdf"

  if [[ -f "$br_html" ]]; then
    echo "  [CHROME] brochure..."
    if html_to_pdf "$br_html" "$br_rgb" 216 303; then
      echo "  [GS] brochure → CMYK..."
      if rgb_to_cmyk "$br_rgb" "$br_cmyk"; then
        rm -f "$br_rgb"
        echo "  [OK] print/$slug/brochure.pdf"
        ok=$((ok+1))
      else
        echo "  [ERROR] gs convert brochure thất bại"
      fi
    else
      echo "  [ERROR] Chrome render brochure thất bại"
    fi
  else
    echo "  [WARN] brochure.html không tìm thấy"
  fi

  # --- Poster (2 mặt A5 + bleed 154×216mm) ---
  local po_html="$cung_dir/poster.html"
  local po_rgb="$out_dir/poster-rgb.pdf"
  local po_cmyk="$out_dir/poster.pdf"

  if [[ -f "$po_html" ]]; then
    echo "  [CHROME] poster..."
    if html_to_pdf "$po_html" "$po_rgb" 154 216; then
      echo "  [GS] poster → CMYK..."
      if rgb_to_cmyk "$po_rgb" "$po_cmyk"; then
        rm -f "$po_rgb"
        echo "  [OK] print/$slug/poster.pdf"
        ok=$((ok+1))
      else
        echo "  [ERROR] gs convert poster thất bại"
      fi
    else
      echo "  [ERROR] Chrome render poster thất bại"
    fi
  else
    echo "  [WARN] poster.html không tìm thấy"
  fi

  [[ $ok -eq 2 ]] && return 0 || return 1
}

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
if [[ $# -gt 0 ]]; then
  SLUGS=("$@")
else
  # Lấy tất cả slug từ cung/ (macOS zsh-compatible)
  IFS=$'\n' read -r -d '' -A SLUGS < <(ls "$CUNG_DIR" && printf '\0') 2>/dev/null || \
  SLUGS=($(ls "$CUNG_DIR"))
fi

echo "[render-print-cmyk] Chrome: $CHROME"
echo "[render-print-cmyk] GS: $GS ($($GS --version 2>&1 | head -1))"
echo "[render-print-cmyk] Output: $PRINT_DIR"
echo "[render-print-cmyk] Sẽ render ${#SLUGS[@]} cung: ${SLUGS[*]}"
echo ""

OK_COUNT=0
FAIL_SLUGS=()

for slug in "${SLUGS[@]}"; do
  echo "→ $slug"
  if render_cung "$slug"; then
    OK_COUNT=$((OK_COUNT+1))
  else
    FAIL_SLUGS+=("$slug")
  fi
  echo ""
done

echo "[render-print-cmyk] Kết quả: $OK_COUNT/${#SLUGS[@]} cung thành công."
if [[ ${#FAIL_SLUGS[@]} -gt 0 ]]; then
  echo "[render-print-cmyk] Lỗi tại: ${FAIL_SLUGS[*]}"
  exit 1
fi

echo "[render-print-cmyk] DONE — bộ in lưu tại: $PRINT_DIR"
