#!/usr/bin/env python3
"""
build-poi-i18n.py — Dịch chuỗi VI của trang HỒ SƠ ĐIỂM ĐẾN sang EN + FR.

Quy trình:
  1. Chạy `python3 scripts/generate-poi.py --collect` -> data/poi-i18n-strings.json
     (danh sách chuỗi VI duy nhất generate-poi sẽ render).
  2. Script này dịch từng chuỗi sang EN + FR (Gemini) theo batch, ghi cache
     data/poi-i18n.json = { "<vi>": {"en": "...", "fr": "..."} }.
  3. Chạy lại `python3 scripts/generate-poi.py` -> page 3 ngôn ngữ thật.

Idempotent: chuỗi đã có trong cache -> bỏ qua (không dịch lại). Dùng --force
để dịch lại toàn bộ. --limit N để chỉ dịch N chuỗi mới (ưu tiên dài/quan trọng).

Tên riêng (Mường Cốc, Mỹ Đức, Hà Nội, Baibóo, tên người...) giữ nguyên.
Thiếu key -> generate-poi tự fallback EN/VI nên không vỡ trang.
"""
import json
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "data"
STRINGS_FILE = DATA / "poi-i18n-strings.json"
CACHE_FILE = DATA / "poi-i18n.json"


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


SYS_PROMPT = (
    "You are a professional translator for a community-based tourism (CBT) "
    "website about Muong Coc, an ethnic Muong village in My Duc, Hanoi, Vietnam. "
    "For each Vietnamese string, produce a natural, idiomatic ENGLISH translation "
    "AND a natural, idiomatic FRENCH translation, both in a warm, evocative, "
    "concise tourism-marketing tone. Rules:\n"
    "- Keep proper nouns EXACTLY as-is: Mường Cốc / Muong Coc, Mỹ Đức / My Duc, "
    "Hà Nội / Hanoi, Đồi Dùng / Doi Dung, Baibóo / Baiboo, Tourism Hub, Net-Zero, "
    "Google My Maps, and ALL Vietnamese place names and person names.\n"
    "- Vietnamese place names without an established English form: keep the "
    "Vietnamese name (you may drop diacritics), do not invent translations.\n"
    "- Preserve leading numbering/symbols (e.g. '01 ·', '→', '–', '☑') and any "
    "inline HTML tags (<b>, <span ...>) exactly.\n"
    "- Do NOT add notes or explanations.\n"
    "- Return ONLY a JSON object. Keys = the input ids. Each value = an object "
    '{"en": "...", "fr": "..."}.'
)


def translate_batch(client, model, batch):
    """batch list[str] -> dict{vi: {"en":..,"fr":..}}."""
    payload = json.dumps({str(i): s for i, s in enumerate(batch)}, ensure_ascii=False)
    prompt = (SYS_PROMPT + "\n\nTranslate the VALUES of this JSON (keys are ids). "
              'Return {"<id>": {"en": "...", "fr": "..."}, ...} with the SAME keys.\n\n'
              + payload)
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
    res = {}
    for i, cell in out.items():
        if i.isdigit() and int(i) < len(batch) and isinstance(cell, dict):
            res[batch[int(i)]] = {
                "en": cell.get("en") or batch[int(i)],
                "fr": cell.get("fr") or cell.get("en") or batch[int(i)],
            }
    return res


def main(argv):
    force = "--force" in argv
    limit = None
    for a in argv:
        if a.startswith("--limit"):
            limit = int(a.split("=")[1]) if "=" in a else int(argv[argv.index(a) + 1])

    if not STRINGS_FILE.exists():
        print("Thiếu poi-i18n-strings.json. Chạy: "
              "python3 scripts/generate-poi.py --collect", file=sys.stderr)
        sys.exit(1)
    strings = json.loads(STRINGS_FILE.read_text(encoding="utf-8"))
    cache = {}
    if CACHE_FILE.exists() and not force:
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))

    todo = [s for s in strings if s not in cache or force]
    # ưu tiên chuỗi dài (nội dung body) trước khi tới label ngắn
    todo.sort(key=len, reverse=True)
    if limit:
        todo = todo[:limit]
    print(f"Tổng {len(strings)} chuỗi · đã có {len(cache)} · cần dịch {len(todo)}")
    if not todo:
        print("Không có gì để dịch.")
        return

    from google import genai
    client = genai.Client(api_key=get_key())
    model = "gemini-2.5-flash"
    B = 30
    done = 0
    for start in range(0, len(todo), B):
        batch = todo[start:start + B]
        for attempt in range(3):
            try:
                cache.update(translate_batch(client, model, batch))
                done += len(batch)
                print(f"[i18n] {done}/{len(todo)}")
                break
            except Exception as ex:
                print(f"[retry {attempt + 1}] batch @{start}: {ex}", file=sys.stderr)
                time.sleep(2 * (attempt + 1))
        else:
            print(f"[WARN] batch @{start} fail -> để generate-poi fallback", file=sys.stderr)
        # ghi tăng dần để không mất tiến độ nếu crash giữa chừng
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
    print(f"Xong. Cache: {len(cache)} mục -> {CACHE_FILE.name}")


if __name__ == "__main__":
    main(sys.argv[1:])
