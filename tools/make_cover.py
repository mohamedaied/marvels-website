"""Make a 1600x900 article cover in the Marvels look.

Usage:
    python3 tools/make_cover.py <slug> <service> "<English title>" [number]

    slug     file name of the article (without .json), e.g. facebook-ads-no-messages
    service  ads | reels | podcast | studio
    number   optional article number shown on the cover, e.g. 7

Writes static/uploads/articles/<slug>.jpg. Needs Python Playwright + Pillow.
The cover carries Latin text only (the Arabic title is shown next to it on the site).
"""
import html
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

COLORS = {"ads": "#3E6DB5", "reels": "#F28C28", "podcast": "#2B7A8A", "studio": "#E9B84A"}
NAMES = {"ads": "ADS", "reels": "REELS", "podcast": "PODCAST", "studio": "STUDIO"}


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    slug, service, title = sys.argv[1], sys.argv[2], sys.argv[3]
    number = sys.argv[4] if len(sys.argv) > 4 else ""
    if service not in COLORS:
        sys.exit(f"service must be one of {', '.join(COLORS)}")

    import build  # noqa: E402  (shield + emblem SVGs; build.py only builds when run directly)

    color = COLORS[service]
    shield = build.shield(service)
    emblem = build.emblem()
    num = f'<div class="num">{html.escape(number.zfill(2))}</div>' if number else ""
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0}}
:root{{--orange:#F28C28;--teal:#2B7A8A;--blue:#3E6DB5;--gold:#E9B84A}}
body{{width:1600px;height:900px;overflow:hidden;background:#12324A;font-family:'Inter Display','Inter',sans-serif;color:#fff;position:relative}}
.grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:64px 64px}}
.glow{{position:absolute;right:-160px;top:-160px;width:900px;height:900px;border-radius:50%;background:{color};opacity:.16}}
.shield{{position:absolute;right:150px;top:50%;transform:translateY(-50%);height:470px}}
.shield svg{{height:100%;width:auto}}
.copy{{position:absolute;left:110px;top:120px;bottom:120px;width:820px;display:flex;flex-direction:column;justify-content:space-between}}
.tag{{display:flex;align-items:center;gap:14px;font-weight:800;font-size:28px;letter-spacing:.14em}}
.tag i{{width:44px;height:8px;background:{color};border-radius:4px}}
.tag b{{color:{color}}}
h1{{font-weight:800;font-size:68px;line-height:1.08;letter-spacing:-.01em}}
.foot{{display:flex;align-items:center;gap:16px}}
.foot svg{{height:58px;width:auto;color:#fff}}
.foot span{{font-weight:900;font-size:30px;letter-spacing:.12em;transform:scaleX(1.18);transform-origin:left}}
.num{{position:absolute;right:110px;bottom:90px;font-weight:900;font-size:40px;color:rgba(255,255,255,.35);letter-spacing:.08em}}
.seam{{position:absolute;left:0;right:0;bottom:0;height:14px;display:flex}}
.seam i{{flex:1}}
</style></head><body>
<div class="grid"></div><div class="glow"></div>
<div class="shield">{shield}</div>
<div class="copy">
  <div class="tag"><i></i>MARVELS <b>{NAMES[service]}</b></div>
  <h1>{html.escape(title)}</h1>
  <div class="foot">{emblem}<span>MARVELS</span></div>
</div>
{num}
<div class="seam"><i style="background:#F28C28"></i><i style="background:#2BB0C2"></i><i style="background:#5B8BD9"></i><i style="background:#E9B84A"></i></div>
</body></html>"""

    from playwright.sync_api import sync_playwright
    from PIL import Image

    out_dir = os.path.join(ROOT, "static", "uploads", "articles")
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, f".{slug}.png")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1600, "height": 900})
        pg.set_content(page)
        pg.wait_for_timeout(200)
        pg.screenshot(path=png)
        b.close()
    jpg = os.path.join(out_dir, f"{slug}.jpg")
    Image.open(png).convert("RGB").save(jpg, quality=86, optimize=True)
    os.remove(png)
    print(f"/uploads/articles/{slug}.jpg")


if __name__ == "__main__":
    main()
