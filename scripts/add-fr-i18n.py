#!/usr/bin/env python3
"""
add-fr-i18n.py — Thêm field _fr (tiếng Pháp) vào data/*.json cho 19 cung.

Cơ chế:
  1. Quét mọi field *_en (str + list[str]) trong 19 file tour.
  2. Gom unique EN strings → dịch sang tiếng Pháp du lịch (Gemini) theo batch.
  3. Ghi field _fr song song với _en (giữ nguyên thứ tự, chỉ THÊM key mới).

Tên riêng (Mường Cốc, Baibóo, Mỹ Đức, Hà Nội...) giữ nguyên.
Idempotent: chạy lại sẽ refresh _fr từ _en hiện tại.

Dùng:  python3 scripts/add-fr-i18n.py
"""
import json
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "data"
SKIP = {"images.json", "master-poi-coords.json"}

# ---- API key qua resolver chung ----
def get_key():
    k = os.getenv("GEMINI_API_KEY")
    if k:
        return k
    import subprocess
    r = subprocess.run(
        ["python3", str(Path.home() / ".claude/scripts/resolve_env.py"),
         "GEMINI_API_KEY", "--skill", "ai-multimodal"],
        capture_output=True, text=True)
    return r.stdout.strip()


def tour_files():
    return sorted(f for f in DATA.glob("*.json") if f.name not in SKIP)


def collect_en(files):
    """Trả set tất cả EN string-values (str + phần tử list)."""
    vals = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k.endswith("_en"):
                    if isinstance(v, str) and v.strip():
                        vals.add(v)
                    elif isinstance(v, list):
                        for it in v:
                            if isinstance(it, str) and it.strip():
                                vals.add(it)
                walk(v)
        elif isinstance(o, list):
            for it in o:
                walk(it)

    for f in files:
        walk(json.loads(f.read_text(encoding="utf-8")))
    return vals


SYS_PROMPT = (
    "You are a professional FR translator for community-based tourism marketing. "
    "Translate each English string into natural, idiomatic French suited to a "
    "tourism website (warm, evocative, concise). Rules:\n"
    "- Keep proper nouns EXACTLY as-is: Mường Cốc, Muong Coc, Baibóo, Baiboo, "
    "Mỹ Đức, My Duc, Hà Nội, Hanoi, Đồi Dùng, Doi Dung, Tourism Hub, Net-Zero, "
    "Google My Maps, and all Vietnamese place/person names.\n"
    "- Preserve any leading numbering / symbols (e.g. '01 ·', '→', '5-NO').\n"
    "- Preserve inline HTML tags like <b>, <span>, exactly.\n"
    "- Do NOT add explanations. Return ONLY a JSON object mapping each input "
    "string to its French translation."
)


def translate_batch(client, model, batch):
    """batch = list[str] → dict{en: fr}."""
    payload = json.dumps({str(i): s for i, s in enumerate(batch)}, ensure_ascii=False)
    prompt = (SYS_PROMPT + "\n\nTranslate the VALUES of this JSON (keys are ids). "
              "Return a JSON object with the SAME keys and French values.\n\n" + payload)
    from google.genai import types
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )
    out = json.loads(resp.text)
    return {batch[int(i)]: out[i] for i in out if i.isdigit() and int(i) < len(batch)}


def build_table(en_vals):
    from google import genai
    client = genai.Client(api_key=get_key())
    model = "gemini-2.5-flash"
    items = sorted(en_vals)
    table = {}
    B = 40  # strings / batch
    for start in range(0, len(items), B):
        batch = items[start:start + B]
        for attempt in range(3):
            try:
                table.update(translate_batch(client, model, batch))
                print(f"[FR] {min(start + B, len(items))}/{len(items)}")
                break
            except Exception as ex:
                print(f"[retry {attempt + 1}] batch @{start}: {ex}", file=sys.stderr)
                time.sleep(2 * (attempt + 1))
        else:
            print(f"[WARN] batch @{start} failed → fallback EN", file=sys.stderr)
            for s in batch:
                table[s] = s  # fallback EN
    # đảm bảo mọi value có entry
    for s in items:
        table.setdefault(s, s)
    return table


def apply_fr(obj, table):
    """Thêm _fr sibling cho mọi _en (str/list). In-place trên dict mới giữ order."""
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            new[k] = apply_fr(v, table)
            if k.endswith("_en"):
                fr_key = k[:-3] + "_fr"
                if isinstance(v, str):
                    new[fr_key] = table.get(v, v)
                elif isinstance(v, list):
                    new[fr_key] = [table.get(x, x) if isinstance(x, str) else apply_fr(x, table)
                                   for x in v]
        return new
    if isinstance(obj, list):
        return [apply_fr(x, table) for x in obj]
    return obj


def main():
    files = tour_files()
    print(f"Quét {len(files)} file tour…")
    en_vals = collect_en(files)
    print(f"Unique EN strings: {len(en_vals)}")
    table = build_table(en_vals)
    print(f"Dịch xong {len(table)} mục. Ghi _fr…")
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        data = apply_fr(data, table)
        f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
        print(f"[OK] {f.name}")
    print("Xong.")


if __name__ == "__main__":
    main()
