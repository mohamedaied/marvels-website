"""Builds the Marvels static website (Arabic at the root, English under /en/).
Content lives in ./content (edited from the /admin dashboard or by hand).
Run:  python3 build.py      Output: ./dist
Uses only the Python standard library, so any host with Python 3.8+ can build it."""
import os, sys, shutil, html, json, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")
CONTENT = os.path.join(HERE, "content")

# ------------------------------------------------------------------ CONFIG
def _load(name):
    with open(os.path.join(CONTENT, name), encoding="utf-8") as f:
        return json.load(f)

SET = _load("settings.json")
PRICING = _load("pricing.json")
try:
    HOME = _load("home.json")
except FileNotFoundError:
    HOME = {}

def H(key, lang, default=""):
    """Home-page text from content/home.json, falling back to the other language, then to default."""
    a, e = (HOME.get(key + "_ar") or "").strip(), (HOME.get(key + "_en") or "").strip()
    v = (a or e) if lang == "ar" else (e or a)
    return v or default

def _pair(key):
    a, e = (SET.get(key + "_ar") or "").strip(), (SET.get(key + "_en") or "").strip()
    return {"ar": a or e, "en": e or a} if (a or e) else None

_email = (SET.get("email") or "").strip()
CONFIG = {
    "domain": "https://marvels-digital.com",
    "wa_number": re.sub(r"\D", "", str(SET.get("wa_number", ""))),
    "phone": _pair("phone") or {"ar": "", "en": ""},
    "email": {"ar": _email, "en": _email} if _email else None,
    "address": _pair("address") or {"ar": "", "en": ""},
    "hours": _pair("hours"),
    "maps": (SET.get("maps_url") or "#").strip(),
    "gbp": (SET.get("google_business") or "").strip(),
    "social": {n: SET[k].strip() for k, n in [("instagram", "Instagram"), ("facebook", "Facebook"), ("tiktok", "TikTok"), ("youtube", "YouTube"), ("linkedin", "LinkedIn")] if (SET.get(k) or "").strip()},
    "studio_rate": int(PRICING.get("studio_rate", 700)),
}

def money(n):
    return f"{int(n):,}"
PLACEHOLDER_MARK = "["

# ------------------------------------------------------------------ helpers
def esc(s):
    return html.escape(s, quote=True)

def ph(s):
    """Wrap unfilled placeholders so they are easy to spot."""
    return f'<span class="ph">{esc(s)}</span>' if s.startswith(PLACEHOLDER_MARK) or PLACEHOLDER_MARK in s else esc(s)

_uid = [0]
def emblem(label=None):
    _uid[0] += 1
    u = f"m{_uid[0]}"
    aria = f'role="img" aria-label="{esc(label)}"' if label else 'aria-hidden="true"'
    return f'''<svg viewBox="0 0 120 132" {aria}><defs><mask id="{u}" maskUnits="userSpaceOnUse" x="0" y="0" width="120" height="132"><rect width="120" height="132" fill="#fff"/><path d="M60 72L88 42V92" fill="none" stroke="#000" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/></mask></defs><path d="M60 8H112V80L60 124Z" fill="currentColor" mask="url(#{u})"/><path d="M60 8H8V80L60 124" fill="none" stroke="currentColor" stroke-width="6" stroke-linejoin="round"/><path d="M32 92V42L60 72" fill="none" stroke="currentColor" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/><g stroke-width="5" stroke-linecap="round"><path d="M60 4V31" stroke="#F28C28"/><path d="M60 37V64" stroke="#2BB0C2"/><path d="M60 70V97" stroke="#5B8BD9"/><path d="M60 103V128" stroke="#E9B84A"/></g></svg>'''

SHIELD = "M8 8H112V80L60 124L8 80Z"
GLYPHS = {
    "reels":   lambda g: f'<rect x="43" y="24" width="34" height="58" rx="8" fill="none" stroke="{g}" stroke-width="7"/><path d="M52 60L60 51L68 60" fill="none" stroke="{g}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>',
    "podcast": lambda g: f'<rect x="48" y="22" width="24" height="42" rx="12" fill="{g}"/><path d="M38 54C38 68 48 76 60 76C72 76 82 68 82 54M60 76V90M48 92H72" fill="none" stroke="{g}" stroke-width="6" stroke-linecap="round"/>',
    "ads":     lambda g: f'<path d="M38 86V70M56 86V56M74 86V42" fill="none" stroke="{g}" stroke-width="10" stroke-linecap="round"/><circle cx="88" cy="30" r="7" fill="#E9B84A"/>',
    "studio":  lambda g: f'<rect x="34" y="22" width="52" height="36" rx="5" fill="{g}"/><path d="M60 58V80M60 80L44 96M60 80L76 96M60 80V96" fill="none" stroke="{g}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>',
}
SVC_FILL = {"reels": "var(--orange)", "podcast": "var(--teal)", "ads": "var(--blue)", "studio": "var(--gold)"}

def shield(kind):
    g = "#12324A" if kind == "studio" else "#FFFFFF"
    return f'<svg viewBox="0 0 120 132" aria-hidden="true"><path d="{SHIELD}" fill="{SVC_FILL[kind]}" stroke="{SVC_FILL[kind]}" stroke-width="6" stroke-linejoin="round"/>{GLYPHS[kind](g)}</svg>'

ICON_CHECK = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5L10 17L19 7" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
ICON_CHAT = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5C4 4.7 4.7 4 5.5 4h13c.8 0 1.5.7 1.5 1.5v9c0 .8-.7 1.5-1.5 1.5H10l-4.5 4v-4H5.5C4.7 16 4 15.3 4 14.5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><circle cx="8.5" cy="10" r="1.2" fill="currentColor"/><circle cx="12" cy="10" r="1.2" fill="currentColor"/><circle cx="15.5" cy="10" r="1.2" fill="currentColor"/></svg>'
ICON_MENU = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
SEAM = '<span class="seam" aria-hidden="true"><i></i><i></i><i></i><i></i></span>'

SLUGS = ["index", "reels", "podcast", "ads", "studio", "pricing", "audit"]

def href(lang, slug):
    """Link to a page in the same language (works on any static host and in the preview)."""
    return "./" if slug == "index" else slug

def other_lang_href(lang, slug):
    if lang == "ar":
        return "en/" if slug == "index" else f"en/{slug}"
    return "../" if slug == "index" else f"../{slug}"

def asset(lang, path):
    return (path if lang == "ar" else "../" + path)

def url_of(lang, slug):
    base = CONFIG["domain"] + ("/" if lang == "ar" else "/en/")
    return base if slug == "index" else base + slug

def L(lang, ar, en):
    return ar if lang == "ar" else en

# ------------------------------------------------------------------ layout
def header(lang, slug):
    nav = [("reels", "ريلز", "Reels"), ("podcast", "بودكاست", "Podcast"), ("ads", "إعلانات", "Ads"),
           ("studio", "الاستوديو", "Studio"), ("pricing", "الأسعار", "Pricing"),
           ("experience", "خبراتنا", "Experience"), ("blog", "مقالات", "Articles")]
    cur = "blog" if slug.startswith("blog") else slug
    links = "".join(
        f'<a href="{href(lang, s)}"{" aria-current=\"page\"" if s == cur else ""}>{L(lang, a, e)}</a>' for s, a, e in nav)
    lang_link = f'<a class="lang" href="{other_lang_href(lang, slug)}" hreflang="{L(lang, "en", "ar")}" lang="{L(lang, "en", "ar")}">{L(lang, "EN", "عربي")}</a>'
    return f'''<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{href(lang, "index")}" aria-label="{L(lang, "Marvels — الرئيسية", "Marvels — Home")}">{emblem()}<span class="wordmark">MARVELS</span></a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="{L(lang, "القائمة", "Menu")}">{ICON_MENU}</button>
    <nav class="nav" id="site-nav" aria-label="{L(lang, "الصفحات", "Pages")}">
      {links}
      {lang_link}
      <a class="btn btn-cta" href="{href(lang, "audit")}">{L(lang, "Audit مجاني", "Free audit")}</a>
    </nav>
  </div>
</header>'''

def footer(lang):
    c = CONFIG
    soc = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener noreferrer">{n}</a></li>' for n, u in c["social"].items())
    soc_col = f'<div><h3>{L(lang, "تابعنا", "Follow")}</h3><ul>{soc}</ul></div>' if soc else ""
    email_li = f'<li>{esc(c["email"][lang])}</li>' if c["email"] else ""
    hours_li = f'<li>{esc(c["hours"][lang])}</li>' if c["hours"] else ""
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <a class="brand" href="{href(lang, "index")}">{emblem()}<span class="wordmark">MARVELS</span></a>
        <p>{L(lang, "وكالة ماركتنج واستوديو محتوى في العبور. ريلز وبودكاست وإعلانات واستوديو تحت سقف واحد.", "A marketing agency and content studio in Obour City. Reels, podcast, ads and studio under one roof.")}</p>
      </div>
      <div>
        <h3>{L(lang, "الخدمات", "Services")}</h3>
        <ul>
          <li><a href="{href(lang, "reels")}">{L(lang, "ريلز", "Reels")}</a></li>
          <li><a href="{href(lang, "podcast")}">{L(lang, "بودكاست", "Podcast")}</a></li>
          <li><a href="{href(lang, "ads")}">{L(lang, "إعلانات ممولة", "Paid ads")}</a></li>
          <li><a href="{href(lang, "studio")}">{L(lang, "إيجار الاستوديو", "Studio rental")}</a></li>
          <li><a href="{href(lang, "pricing")}">{L(lang, "الباقات والأسعار", "Pricing")}</a></li>
        </ul>
      </div>
      <div>
        <h3>{L(lang, "تواصل", "Contact")}</h3>
        <ul>
          <li><a href="#" data-wa="">{L(lang, "واتساب", "WhatsApp")}: <span dir="ltr">{esc(c["phone"][lang])}</span></a></li>
          {email_li}
          <li><a href="{esc(c["maps"])}" target="_blank" rel="noopener">{esc(c["address"][lang])}</a></li>
          {f'<li><a href="{esc(c["gbp"])}" target="_blank" rel="noopener noreferrer">{L(lang, "قيّمنا على جوجل", "Review us on Google")}</a></li>' if c["gbp"] else ""}
          {hours_li}
        </ul>
      </div>
      <div>
        <h3>{L(lang, "الشركة", "Company")}</h3>
        <ul>
          <li><a href="{href(lang, "experience")}">{L(lang, "خبراتنا", "Experience")}</a></li>
          <li><a href="{href(lang, "blog")}">{L(lang, "مقالات", "Articles")}</a></li>
          <li><a href="{href(lang, "audit")}">{L(lang, "Audit مجاني", "Free audit")}</a></li>
        </ul>
      </div>
      {soc_col}
    </div>
    <div class="footer-bottom">
      <span>© 2026 Marvels — Marketing &amp; Studio</span>
      <a href="{other_lang_href(lang, "index")}">{L(lang, "English", "العربية")}</a>
    </div>
  </div>
</footer>
<a class="chat-fab" href="#" data-wa="{esc(L(lang, "أهلًا Marvels، عايز أعرف تفاصيل أكتر.", "Hi Marvels, I'd like to know more."))}" aria-label="{L(lang, "كلمنا على واتساب", "Chat on WhatsApp")}">{ICON_CHAT}<span>{L(lang, "كلمنا واتساب", "WhatsApp us")}</span></a>'''

SVC_NAMES = {"reels": ("تصوير ومونتاج ريلز", "Reels production"), "podcast": ("إنتاج وتسجيل بودكاست", "Podcast production"),
             "ads": ("إدارة الإعلانات الممولة", "Paid ads management"), "studio": ("إيجار استوديو تصوير", "Studio rental")}
CRUMB = {"reels": ("ريلز", "Reels"), "podcast": ("بودكاست", "Podcast"), "ads": ("إعلانات", "Ads"), "studio": ("الاستوديو", "Studio"),
         "pricing": ("الأسعار", "Pricing"), "experience": ("خبراتنا", "Experience"), "blog": ("مقالات", "Articles"), "audit": ("Audit مجاني", "Free audit")}

def business_ld(lang):
    c, d = CONFIG, CONFIG["domain"]
    b = {"@type": "ProfessionalService", "@id": d + "/#business", "name": "Marvels",
         "alternateName": "Marvels Marketing & Studio",
         "description": L(lang, "وكالة ماركتنج واستوديو محتوى في العبور: ريلز، بودكاست، إعلانات ممولة، واستوديو للإيجار.",
                          "Marketing agency and content studio in Obour City: reels, podcasts, paid ads and studio rental."),
         "url": d + L(lang, "/", "/en/"), "logo": d + "/assets/apple-touch-icon.png", "image": d + "/assets/og.png",
         "telephone": "+" + c["wa_number"],
         "address": {"@type": "PostalAddress", "streetAddress": c["address"][lang],
                     "addressLocality": L(lang, "مدينة العبور", "Obour City"), "addressRegion": L(lang, "القليوبية", "Qalyubia"),
                     "addressCountry": "EG"},
         "areaServed": [{"@type": "City", "name": n} for n in L(lang, ["العبور", "مدينتي", "مدينة المستقبل", "الشروق", "القاهرة"],
                                                                     ["Obour City", "Madinaty", "Mostakbal City", "El Shorouk", "Cairo"])],
         "priceRange": "EGP 700 - 60,000",
         "knowsLanguage": ["ar", "en"],
         "hasOfferCatalog": {"@type": "OfferCatalog", "name": L(lang, "خدمات Marvels", "Marvels services"),
                             "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": L(lang, *v),
                                                  "url": url_of(lang, k)}} for k, v in SVC_NAMES.items()]}}
    if c["email"]:
        b["email"] = c["email"]["en"] if isinstance(c["email"], dict) else c["email"]
    same = list(c["social"].values()) + ([c["gbp"]] if c["gbp"] else [])
    if same:
        b["sameAs"] = same
    if c["gbp"]:
        b["hasMap"] = c["gbp"]
    return b

def json_ld(lang, slug, title, desc, art, img):
    d = CONFIG["domain"]
    home = url_of(lang, "index")
    graph = []
    if slug == "index":
        graph.append(business_ld(lang))
        graph.append({"@type": "WebSite", "@id": d + "/#website", "name": "Marvels", "url": home,
                      "inLanguage": lang, "publisher": {"@id": d + "/#business"}})
    else:
        crumbs = [("Marvels", home)]
        if art:
            crumbs.append((L(lang, *CRUMB["blog"]), url_of(lang, "blog")))
            crumbs.append((L(lang, *art["title"]), url_of(lang, slug)))
        else:
            crumbs.append((L(lang, *CRUMB.get(slug, (title, title))), url_of(lang, slug)))
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(crumbs)]})
    if slug in SVC_NAMES:
        graph.append({"@type": "Service", "name": L(lang, *SVC_NAMES[slug]), "description": desc, "url": url_of(lang, slug),
                      "serviceType": L(lang, *SVC_NAMES[slug]),
                      "provider": {"@type": "ProfessionalService", "@id": d + "/#business", "name": "Marvels"},
                      "areaServed": L(lang, "العبور والقاهرة الجديدة والشروق ومدينتي", "Obour City, New Cairo, El Shorouk, Madinaty")})
    if art:
        a = {"@type": "BlogPosting", "headline": L(lang, *art["title"]), "description": desc, "url": url_of(lang, slug),
             "mainEntityOfPage": url_of(lang, slug), "image": img, "inLanguage": lang,
             "author": {"@type": "Organization", "name": "Marvels", "url": home},
             "publisher": {"@type": "Organization", "name": "Marvels", "logo": {"@type": "ImageObject", "url": d + "/assets/apple-touch-icon.png"}}}
        if art["date"]:
            a["datePublished"] = art["date"]
        graph.append(a)
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/ld+json">{data}</script>'

def head(lang, slug, title, desc, for_artifact=False):
    fonts = "https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,600..900&family=IBM+Plex+Sans+Arabic:wght@400;500;700&display=swap"
    alt = (f'<link rel="alternate" hreflang="ar" href="{url_of("ar", slug)}"><link rel="alternate" hreflang="en" href="{url_of("en", slug)}">'
           f'<link rel="alternate" hreflang="x-default" href="{url_of("ar", slug)}">')
    art = next((a for a in ARTICLES if a["slug"] == slug), None)
    og_img = CONFIG["domain"] + "/assets/og.png"
    if art and art["cover"]:
        og_img = art["cover"] if art["cover"].startswith("http") else CONFIG["domain"] + "/" + art["cover"].lstrip("/")
    ld = json_ld(lang, slug, title, desc, art, og_img)
    common = f'''<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="wa-number" content="{esc(CONFIG["wa_number"])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="{"article" if art else "website"}">
<meta property="og:url" content="{url_of(lang, slug)}">
<meta property="og:site_name" content="Marvels">
<meta property="og:locale" content="{L(lang, "ar_EG", "en_US")}">
<meta property="og:locale:alternate" content="{L(lang, "en_US", "ar_EG")}">
<meta property="og:image" content="{esc(og_img)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#12324A">
<link rel="icon" href="{asset(lang, "assets/favicon.svg")}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{asset(lang, "assets/apple-touch-icon.png")}">
<link rel="canonical" href="{url_of(lang, slug)}">{alt}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{fonts}">
<link rel="stylesheet" href="{asset(lang, "assets/site.css")}">
{ld}
<script>document.documentElement.classList.add("js")</script>'''
    if for_artifact:
        return '<meta name="claude:viewport-fit-sides" content="cover">\n' + common
    return f'<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n{common}'

def page(lang, slug, title, desc, main, body_class="", for_artifact=False):
    d = L(lang, "rtl", "ltr")
    inner = f'''{header(lang, slug)}
<main id="main">
{main}
</main>
{footer(lang)}
<script src="{asset(lang, "assets/site.js")}" defer></script>'''
    if for_artifact:
        # The preview host supplies <html>/<body>; set language and direction from script.
        boot = f'<script>document.documentElement.lang="{lang}";document.documentElement.dir="{d}";{"document.body.className=" + repr(body_class) + ";" if body_class else ""}</script>'
        return head(lang, slug, title, desc, True) + "\n" + boot + "\n" + inner
    cls = f' class="{body_class}"' if body_class else ""
    return f'''<!doctype html>
<html lang="{lang}" dir="{d}">
<head>
{head(lang, slug, title, desc)}
</head>
<body{cls}>
{inner}
</body>
</html>
'''

# ------------------------------------------------------------------ shared blocks
def services_grid(lang):
    items = [
        ("reels", "REELS", "ريلز بتشد من أول 3 ثواني: فكرة وسكريبت وتصوير ومونتاج، جاهزة تتنشر وتشتغل إعلان.",
         "Scroll-stopping reels: script, studio shoot and edit, ready to post and to run as ads."),
        ("podcast", "PODCAST", "حلقات بصورة وصوت استوديو، وكل حلقة بتطلّعلك ريلز تكفيك طول الأسبوع.",
         "Professionally shot episodes, each one cut into reels you can post all week."),
        ("ads", "ADS", "حملات على فيسبوك وإنستجرام وتيك توك، هدفها رسايل وحجوزات ومبيعات، مش لايكات.",
         "Paid campaigns on Meta and TikTok built on numbers: messages, bookings and sales."),
        ("studio", "STUDIO", "استوديو مجهز بالإضاءة والصوت في العبور، تأجره بالساعة وتصوّر على طول.",
         "A ready studio in Obour City, rented by the hour to creators and photographers."),
    ]
    more = L(lang, "اعرف أكتر ←", "Learn more →")
    cards = "".join(
        f'<a class="svc-card" href="{href(lang, k)}">{shield(k)}<span class="name">MARVELS <span class="c-{k}">{n}</span></span><p>{L(lang, a, e)}</p><span class="more c-{k}">{more}</span></a>'
        for k, n, a, e in items)
    return f'<div class="svc-grid">{cards}</div>'

def cta_band(lang):
    return f'''<section class="band-navy cta-band">
  <div class="wrap">
    <div>
      <h2>{L(lang, "عايز تعرف صفحتك بتخسر عملاء فين؟", "Want to know where your page is losing customers?")}</h2>
      <p>{L(lang, "Audit مجاني: نراجع صفحتك وإعلاناتك ونقولك فين الرسايل والحجوزات اللي بتضيع، و3 حاجات تبدأ بيها فورًا.", "A free audit: we review your page and ads, show you where messages and bookings slip away, and give you three fixes to start with.")}</p>
    </div>
    <div class="center-actions">
      <a class="btn btn-cta" href="{href(lang, "audit")}">{L(lang, "احجز Audit مجاني", "Book a free audit")}</a>
      <a class="btn btn-ghost" href="#" data-wa="{esc(L(lang, "أهلًا Marvels، عايز أحجز Audit مجاني لصفحتي.", "Hi Marvels, I'd like a free audit of my page."))}">{L(lang, "كلمنا واتساب", "WhatsApp us")}</a>
    </div>
  </div>
</section>'''

def svc_hero(lang, kind, name, h1, lead, primary):
    return f'''<section class="band-navy hero svc-hero">
  <div class="wrap">
    <div class="hero-copy">
      <span class="eyebrow" dir="ltr">MARVELS <b>{name}</b></span>
      <h1>{h1}</h1>
      <p class="lead">{lead}</p>
      <div class="hero-actions">{primary}</div>
    </div>
    <div class="hero-mark">{shield(kind)}</div>
  </div>
</section>'''

def checks(items):
    return '<ul class="checks">' + "".join(
        f'<li>{ICON_CHECK}<div><h3>{h}</h3><p>{p}</p></div></li>' for h, p in items) + "</ul>"

def chips(items):
    return '<ul class="chips">' + "".join(f"<li>{x}</li>" for x in items) + "</ul>"

def plan_card(lang, name, price, per, feats, tag=None, featured=False, wa_text=""):
    lis = "".join(f"<li>{ICON_CHECK}<span>{f}</span></li>" for f in feats)
    t = f'<span class="tag">{tag}</span>' if tag else ""
    btn_cls = "btn-cta" if featured else "btn-line"
    return f'''<article class="plan{" featured" if featured else ""}">
  {t}
  <h3>{name}</h3>
  <div class="price"><b>{price}</b><span>{per}</span></div>
  <ul>{lis}</ul>
  <a class="btn {btn_cls}" href="#" data-wa="{esc(wa_text)}">{L(lang, "اطلب الباقة على واتساب", "Ask for this plan on WhatsApp")}</a>
</article>'''

def reels_plans(lang):
    per = L(lang, "جنيه / شهر", "EGP / month")
    cards = []
    for p in PRICING["plans"]:
        feats = p["features_ar"] if lang == "ar" else p["features_en"]
        tag = (p.get("tag_ar") if lang == "ar" else p.get("tag_en")) or None
        wa = L(lang, f"أهلًا Marvels، عايز أعرف تفاصيل باقة {p['name']}.", f"Hi Marvels, I'd like details on the {p['name']} plan.")
        cards.append(plan_card(lang, esc(p["name"]), money(p["price"]), per, [esc(f) for f in feats], tag=esc(tag) if tag else None,
                               featured=bool(p.get("featured")), wa_text=wa))
    return '<div class="price-grid">' + "".join(cards) + "</div>"

def rates_table(lang, rows):
    head_ = f'<thead><tr><th>{L(lang, "الخدمة", "Service")}</th><th>{L(lang, "بتشمل", "Includes")}</th><th>{L(lang, "السعر", "Price")}</th></tr></thead>'
    body = "".join(f'<tr><td><b>{a}</b></td><td>{b}</td><td class="num">{c}<small>{d}</small></td></tr>' for a, b, c, d in rows)
    return f'<div class="table-wrap"><table class="rates">{head_}<tbody>{body}</tbody></table></div>'

def podcast_rows(lang):
    rows = [(esc(L(lang, r["name_ar"], r["name_en"])), esc(L(lang, r["desc_ar"], r["desc_en"])), money(r["price"]),
             esc(L(lang, r["unit_ar"], r["unit_en"]))) for r in PRICING["podcast"]]
    rows.append((L(lang, "إيجار استوديو البودكاست", "Podcast studio rental"),
                 L(lang, "المكان والمعدات، من غير مونتاج", "Space and equipment, no editing"),
                 money(CONFIG["studio_rate"]), L(lang, "جنيه / ساعة", "EGP / hour")))
    return rows

def result_panel(lang):
    return f'''<div class="result" hidden>
  <h3>{L(lang, "رسالتك جاهزة", "Your message is ready")}</h3>
  <p>{L(lang, "اضغط الزرار يفتح واتساب والرسالة مكتوبة، وبعدها اضغط إرسال. هنرد عليك في أقرب وقت.", "Tap the button to open WhatsApp with the message filled in, then press send. We'll reply as soon as we can.")}</p>
  <pre></pre>
  <div class="row">
    <a class="btn btn-chat go" href="#" target="_blank" rel="noopener">{ICON_CHAT}{L(lang, "افتح واتساب وابعت", "Open WhatsApp and send")}</a>
    <button class="btn btn-line copy" type="button">{L(lang, "انسخ الرسالة", "Copy message")}</button>
  </div>
</div>'''

# ------------------------------------------------------------------ pages
def launch_bar(lang):
    if not SET.get("launch_show"):
        return ""
    t, x = _pair("launch_title"), _pair("launch_text")
    return f'''<div class="launch">
  <div class="wrap">
    {f"<strong>{esc(t[lang])}</strong>" if t else ""}
    {f"<span>{esc(x[lang])}</span>" if x else ""}
    <a href="{href(lang, "pricing")}#founders">{L(lang, "التفاصيل", "Details")}</a>
  </div>
</div>'''

def p_index(lang):
    title = L(lang, "Marvels — ماركتنج واستوديو في العبور", "Marvels — Marketing & Studio, Obour City")
    desc = L(lang, "وكالة ماركتنج واستوديو محتوى في العبور: ريلز، بودكاست، إعلانات ممولة، واستوديو للإيجار. احجز Audit مجاني لصفحتك.",
             "Marketing agency and content studio in Obour City: reels, podcast, paid ads and studio rental. Book a free audit of your page.")
    why = [(L(lang, (w.get("title_ar") or w.get("title_en") or ""), (w.get("title_en") or w.get("title_ar") or "")),
            L(lang, (w.get("text_ar") or w.get("text_en") or ""), (w.get("text_en") or w.get("text_ar") or "")))
           for w in HOME.get("why", [])]
    why_html = "".join(f'<div class="why-item"><span class="why-n latin">{i:02d}</span><h3>{esc(h)}</h3><p>{esc(p)}</p></div>' for i, (h, p) in enumerate(why, 1))
    steps = [
        (L(lang, "Audit مجاني", "Free audit"), L(lang, "بنراجع صفحتك وإعلاناتك، ونحدد معاك الهدف والرقم.", "We review your page and ads and agree the goal and the number.")),
        (L(lang, "خطة الشهر", "The month's plan"), L(lang, "الأفكار والسكريبتات بتوصلك قبل التصوير بـ5 أيام.", "Ideas and scripts reach you 5 days before the shoot.")),
        (L(lang, "التصوير", "The shoot"), L(lang, "بنصوّر محتوى الشهر في الاستوديو في أيام ثابتة.", "We film the month's content in the studio on fixed days.")),
        (L(lang, "النشر والإعلانات", "Publish and promote"), L(lang, "مونتاج ونشر، وتشغيل الإعلانات ومتابعتها كل يوم.", "Editing, posting, and ads run and watched every day.")),
        (L(lang, "التقرير", "The report"), L(lang, "أرقام الشهر، واجتماع نقرر فيه الخطوة الجاية.", "The month's numbers and a review to decide what's next.")),
    ]
    steps_html = "".join(f"<li><h3>{h}</h3><p>{p}</p></li>" for h, p in steps)

    def cta(n, cls):
        return cta_btn(lang, HOME, n, cls, L(lang, "أهلًا Marvels، عايز أعرف أكتر عن خدماتكم.", "Hi Marvels, I would like to know more about your services."))

    style = (HOME.get("hero_style") or "navy").strip()
    style = style if style in ("navy", "teal", "light", "orange") else "navy"
    img = (HOME.get("hero_image") or "").strip()
    if img and not img.startswith(("http://", "https://", "/")):
        img = "/" + img
    mark = f'<img class="hero-img" src="{esc(img)}" alt="">' if img else emblem("Marvels")
    band = "band-navy" if style in ("navy", "teal") else ""
    title_h = esc(H("hero_title", lang, L(lang, "محتوى بيتشاف، وإعلانات بتجيب عملاء", "Content people watch. Ads that bring customers.")))
    main = f'''<section class="{band} hero hero-{style}">
  <div class="wrap">
    <div class="hero-copy">
      <span class="eyebrow">{SEAM}{esc(H("hero_eyebrow", lang, "MARKETING & STUDIO"))}</span>
      <h1>{title_h}</h1>
      <p class="lead">{esc(H("hero_lead", lang))}</p>
      <div class="hero-actions">
        {cta(1, "btn-cta")}
        {cta(2, "btn-ghost")}
      </div>
    </div>
    <div class="hero-mark{" has-img" if img else ""}">{mark}</div>
  </div>
</section>
{launch_bar(lang)}
<section>
  <div class="wrap">
    <div class="section-head">
      <h2>{esc(H("services_title", lang, L(lang, "خدماتنا", "What we do")))}</h2>
      <p>{esc(H("services_lead", lang))}</p>
    </div>
    {services_grid(lang)}
  </div>
</section>
<section class="band-surface">
  <div class="wrap">
    <div class="section-head">
      <h2>{esc(H("why_title", lang, L(lang, "ليه تختار Marvels؟", "Why brands choose Marvels")))}</h2>
      <p>{esc(H("why_lead", lang))}</p>
    </div>
    <div class="why-grid">{why_html}</div>
  </div>
</section>
<section class="band-navy">
  <div class="wrap">
    <div class="section-head">
      <h2>{L(lang, "إزاي بنشتغل", "How we work")}</h2>
      <p>{L(lang, "نفس الخطوات كل شهر، عشان المحتوى ينزل في ميعاده والنتيجة تتقاس.", "The same steps every month, so content ships on time and results get measured.")}</p>
    </div>
    <ol class="steps">{steps_html}</ol>
  </div>
</section>
{experience_teaser(lang)}
{cta_band(lang)}'''
    return title, desc, main, ""

# ------------------------------------------------------------------ editable pages (content/pages/*.json)
SERVICE_PAGES = ("reels", "podcast", "ads", "studio")
SVC_CONTENT = {}
for _k in SERVICE_PAGES:
    try:
        SVC_CONTENT[_k] = _load(f"pages/{_k}.json")
    except FileNotFoundError:
        SVC_CONTENT[_k] = {}

def T(d, key, lang, default=""):
    """Bilingual field from a content dict (key_ar / key_en), falling back to the other language."""
    a, e = (d.get(key + "_ar") or "").strip(), (d.get(key + "_en") or "").strip()
    v = (a or e) if lang == "ar" else (e or a)
    return v or default

def fill(text):
    return (text.replace("{trial_price}", money(PRICING.get("trial_price", 0)))
                .replace("{studio_rate}", money(PRICING.get("studio_rate", 0))))

def cta_btn(lang, d, n, cls, wa_text):
    label = T(d, f"cta{n}_label", lang)
    target = (d.get(f"cta{n}_link") or "").strip()
    if not label or not target:
        return ""
    if target == "whatsapp":
        return f'<a class="btn {cls}" href="#" data-wa="{esc(wa_text)}">{esc(label)}</a>'
    if target == "studio-book":
        return f'<a class="btn {cls}" href="{href(lang, "studio")}#book">{esc(label)}</a>'
    if target.startswith(("http://", "https://")):
        return f'<a class="btn {cls}" href="{esc(target)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'
    return f'<a class="btn {cls}" href="{href(lang, target)}">{esc(label)}</a>'

def hero_parts(d):
    style = (d.get("hero_style") or "navy").strip()
    style = style if style in ("navy", "teal", "light", "orange") else "navy"
    img = (d.get("hero_image") or "").strip()
    if img and not img.startswith(("http://", "https://", "/")):
        img = "/" + img
    band = "band-navy" if style in ("navy", "teal") else ""
    return style, img, band

def page_hero(lang, kind, name, d):
    style, img, band = hero_parts(d)
    wa = L(lang, f"أهلًا Marvels، عايز أعرف أكتر عن خدمة {SVC_NAMES[kind][0]}.", f"Hi Marvels, I'd like to know more about {SVC_NAMES[kind][1].lower()}.")
    mark = f'<img class="hero-img" src="{esc(img)}" alt="">' if img else shield(kind)
    return f'''<section class="{band} hero svc-hero hero-{style}">
  <div class="wrap">
    <div class="hero-copy">
      <span class="eyebrow" dir="ltr">MARVELS <b>{name}</b></span>
      <h1>{esc(T(d, "hero_title", lang))}</h1>
      <p class="lead">{esc(fill(T(d, "hero_lead", lang)))}</p>
      <div class="hero-actions">{cta_btn(lang, d, 1, "btn-cta", wa)}{cta_btn(lang, d, 2, "btn-ghost", wa)}</div>
    </div>
    <div class="hero-mark{" has-img" if img else ""}">{mark}</div>
  </div>
</section>'''

def page_features(lang, d):
    items = [(esc(T(f, "title", lang)), esc(fill(T(f, "text", lang)))) for f in d.get("features", []) if T(f, "title", lang)]
    head = T(d, "features_title", lang)
    return (f'<div class="section-head"><h2>{esc(head)}</h2></div>' if head else "") + (checks(items) if items else "")

def page_aside(lang, d, extra=""):
    parts = []
    aud = [x for x in (d.get("audience_ar" if lang == "ar" else "audience_en") or d.get("audience_ar") or []) if str(x).strip()]
    if aud:
        parts.append(f'<h3>{esc(T(d, "audience_title", lang, L(lang, "مناسب لمين", "Who it is for")))}</h3>{chips([esc(x) for x in aud])}')
    if T(d, "box_title", lang) or T(d, "box_text", lang):
        parts.append(f'<h3>{esc(T(d, "box_title", lang))}</h3><p>{esc(fill(T(d, "box_text", lang)))}</p>')
    if T(d, "note", lang):
        parts.append(f'<p class="note">{esc(fill(T(d, "note", lang)))}</p>')
    if extra:
        parts.append(extra)
    return f'<aside class="aside-box">{"".join(parts)}</aside>' if parts else ""

def p_reels(lang):
    title = L(lang, "تصوير ومونتاج ريلز للبيزنس في العبور — Marvels", "Reels Production for Businesses in Obour City — Marvels")
    desc = L(lang, f"سكريبت وتصوير ومونتاج ريلز في استوديو Marvels بالعبور، جاهزة للنشر والإعلان. باقات تبدأ من {money(min(p['price'] for p in PRICING['plans']))} جنيه شهريًا.",
             f"Reels scripted, shot and edited at Marvels studio in Obour City, ready to post and promote. Plans from EGP {money(min(p['price'] for p in PRICING['plans']))} a month.")
    d = SVC_CONTENT["reels"]
    main = page_hero(lang, "reels", "REELS", d) + f'''<section>
  <div class="wrap two-col">
    <div>{page_features(lang, d)}</div>
    {page_aside(lang, d)}
  </div>
</section>
<section class="band-surface">
  <div class="wrap">
    <div class="section-head"><h2>{L(lang, "الباقات الشهرية", "Monthly plans")}</h2><p>{L(lang, "عقد 3 شهور على الأقل، والدفع مقدم أول كل شهر. ميزانية الإعلان نفسها بتتدفع للمنصة مباشرة.", "Minimum 3-month contract, paid at the start of each month. Ad spend is paid to the platform directly.")}</p></div>
    {reels_plans(lang)}
  </div>
</section>
{cta_band(lang)}'''
    return title, desc, main, "svc-reels"

def p_podcast(lang):
    title = L(lang, "استوديو بودكاست وتسجيل حلقات في العبور — Marvels", "Podcast Studio & Production in Obour City — Marvels")
    desc = L(lang, "سجّل البودكاست بتاعك في استوديو Marvels بالعبور: 2–3 كاميرات، مونتاج، وريلز مقصوصة من كل حلقة.",
             "Record your podcast at Marvels studio in Obour City: 2–3 cameras, editing and reels cut from every episode.")
    d = SVC_CONTENT["podcast"]
    main = page_hero(lang, "podcast", "PODCAST", d) + f'''<section>
  <div class="wrap two-col">
    <div>{page_features(lang, d)}</div>
    {page_aside(lang, d)}
  </div>
</section>
<section class="band-surface">
  <div class="wrap">
    <div class="section-head"><h2>{L(lang, "أسعار البودكاست", "Podcast pricing")}</h2></div>
    {rates_table(lang, podcast_rows(lang))}
  </div>
</section>
{cta_band(lang)}'''
    return title, desc, main, "svc-podcast"

def p_ads(lang):
    title = L(lang, "إدارة إعلانات ممولة فيسبوك وإنستجرام وتيك توك — Marvels", "Paid Ads Management: Meta & TikTok — Marvels")
    desc = L(lang, "إدارة إعلانات ممولة على ميتا وتيك توك من Marvels بالعبور: استهداف، تجهيز إعلانات، متابعة يومية، وتقرير بالأرقام.",
             "Paid ads on Meta and TikTok managed by Marvels in Obour City: targeting, ad creative, daily optimisation and a monthly report.")
    d = SVC_CONTENT["ads"]
    quote = f'<a class="btn btn-line" href="#" data-wa="{esc(L(lang, "أهلًا Marvels، عايز عرض سعر لإدارة الإعلانات.", "Hi Marvels, I would like a quote for ads management."))}">{L(lang, "اطلب عرض سعر", "Request a quote")}</a>'
    main = page_hero(lang, "ads", "ADS", d) + f'''<section>
  <div class="wrap two-col">
    <div>{page_features(lang, d)}</div>
    {page_aside(lang, d, quote)}
  </div>
</section>
{cta_band(lang)}'''
    return title, desc, main, "svc-ads"

def p_studio(lang):
    rate = CONFIG["studio_rate"]
    title = L(lang, "استوديو للإيجار في العبور — Marvels", "Studio Rental in Obour — Marvels")
    desc = L(lang, f"استوديو Marvels في العبور للإيجار بالساعة: ركن بودكاست وركن ريلز. {rate} جنيه للساعة. احجز ميعادك على واتساب.",
             f"Rent Marvels studio in Obour City by the hour: a podcast set and a reels set. EGP {rate} per hour. Book on WhatsApp.")
    d = SVC_CONTENT["studio"]
    hero = page_hero(lang, "studio", "STUDIO", d)
    hours_opts = "".join(f'<option value="{h}"{" selected" if h == 2 else ""}>{h} {L(lang, "ساعة" if h in (1,) else ("ساعتين" if h == 2 else "ساعات"), "hour" if h == 1 else "hours")}</option>' for h in range(1, 9))
    hours_opts = hours_opts.replace(f'>2 {L(lang, "ساعتين", "hours")}<', f'>{L(lang, "ساعتين", "2 hours")}<')
    main = hero + f'''<section>
  <div class="wrap two-col">
    <div>
      {page_features(lang, d)}
    </div>
    <aside class="aside-box">
      <h3>{L(lang, "السعر", "Price")}</h3>
      <div class="price"><b class="latin" style="font-weight:900;font-size:40px;line-height:1">{rate:,}</b> <span class="muted">{L(lang, "جنيه / ساعة", "EGP / hour")}</span></div>
      <p class="muted">{L(lang, "المكان والمعدات، من غير مونتاج.", "Space and equipment, without editing.")}</p>
      {f'<h3>{L(lang, "المواعيد", "Hours")}</h3><p>{esc(CONFIG["hours"][lang])}</p>' if CONFIG["hours"] else ""}
      <h3>{L(lang, "العنوان", "Address")}</h3>
      <p><a href="{esc(CONFIG["maps"])}" target="_blank" rel="noopener">{esc(CONFIG["address"][lang])}</a></p>
    </aside>
  </div>
</section>
<section class="band-surface" id="book">
  <div class="wrap">
    <div class="section-head">
      <h2>{L(lang, "احجز ساعات في الاستوديو", "Book studio hours")}</h2>
      <p>{L(lang, "املا البيانات، وهتتبعت لنا رسالة على واتساب نأكدلك فيها الميعاد. الحجز بيتأكد بعد العربون.", "Fill in the details and they'll be sent to us on WhatsApp so we can confirm. A booking is confirmed once the deposit is paid.")}</p>
    </div>
    <div class="form-card">
      <form data-wa-form="{esc(L(lang, "حجز استوديو — Marvels", "Studio booking — Marvels"))}" novalidate>
        <div class="form-grid">
          <div class="field"><label for="s-type">{L(lang, "نوع الحجز", "Booking type")}</label>
            <select id="s-type" name="type" data-label="{L(lang, "النوع", "Type")}">
              <option value="rental">{L(lang, f"إيجار الاستوديو بالساعة ({rate} جنيه)", f"Hourly studio rental (EGP {rate})")}</option>
              <option value="podcast">{L(lang, "تسجيل بودكاست بالمونتاج", "Podcast recording with editing")}</option>
              <option value="reels">{L(lang, "تصوير ريلز بالمونتاج", "Reels shoot with editing")}</option>
            </select></div>
          <div class="field"><label for="s-hours">{L(lang, "المدة", "Duration")}</label>
            <select id="s-hours" name="hours" data-label="{L(lang, "المدة", "Duration")}">{hours_opts}</select></div>
          <div class="field"><label for="s-date">{L(lang, "اليوم", "Date")}</label>
            <input id="s-date" name="date" type="date" required data-min-today data-label="{L(lang, "اليوم", "Date")}"></div>
          <div class="field"><label for="s-time">{L(lang, "الساعة", "Start time")}</label>
            <input id="s-time" name="time" type="time" required data-label="{L(lang, "الساعة", "Start time")}"></div>
          <div class="field"><label for="s-name">{L(lang, "الاسم", "Name")}</label>
            <input id="s-name" name="name" type="text" autocomplete="name" required data-label="{L(lang, "الاسم", "Name")}"></div>
          <div class="field"><label for="s-phone">{L(lang, "رقم الموبايل", "Mobile number")}</label>
            <input id="s-phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" required dir="ltr" placeholder="01xxxxxxxxx" data-label="{L(lang, "الموبايل", "Mobile")}"></div>
          <div class="field"><label for="s-people">{L(lang, "عدد الأشخاص", "Number of people")}</label>
            <input id="s-people" name="people" type="number" min="1" max="10" value="1" data-label="{L(lang, "عدد الأشخاص", "People")}"></div>
          <div class="field"><label for="s-notes">{L(lang, "ملاحظات", "Notes")} <span class="hint">{L(lang, "(اختياري)", "(optional)")}</span></label>
            <input id="s-notes" name="notes" type="text" data-label="{L(lang, "ملاحظات", "Notes")}"></div>
        </div>
        <div class="estimate" data-estimate data-rate="{rate}"><span></span><b></b></div>
        <div class="form-actions">
          <button class="btn btn-cta" type="submit">{L(lang, "ابعت الحجز على واتساب", "Send booking on WhatsApp")}</button>
          <span class="small">{L(lang, "مفيش حاجة بتتبعت غير لما تضغط إرسال في واتساب.", "Nothing is sent until you press send in WhatsApp.")}</span>
        </div>
      </form>
      {result_panel(lang)}
    </div>
  </div>
</section>'''
    return title, desc, main, "svc-studio"

def p_pricing(lang):
    title = L(lang, "أسعار باقات الريلز والبودكاست والاستوديو — Marvels", "Reels, Podcast & Studio Pricing — Marvels")
    desc = L(lang, "أسعار باقات Marvels: باقات ريلز شهرية، بودكاست بالحلقة أو بالشهر، وإيجار الاستوديو بالساعة.",
             "Marvels pricing: monthly reels plans, podcast by the episode or month, and hourly studio rental.")
    faq = [
        (L(lang, "ميزانية الإعلانات داخلة في الباقة؟", "Is ad spend included?"),
         L(lang, "لأ. ميزانية الإعلان بتتدفع للمنصة مباشرة من حسابك، والباقة بتشمل الإدارة والمحتوى بس.", "No. Ad spend is paid directly to the platform from your account; the plan covers management and content.")),
        (L(lang, "مدة العقد قد إيه؟", "How long is the contract?"),
         L(lang, "3 شهور على الأقل، لأن نتايج المحتوى والإعلانات بتبان بوضوح من الشهر التاني والتالت.", "At least 3 months, because content and ad results show clearly from the second and third month.")),
        (L(lang, "الدفع إمتى؟", "When do I pay?"),
         L(lang, "مقدم أول كل شهر. ولو دفعت 3 شهور مرة واحدة تاخد خصم 10%.", "At the start of each month. Pay 3 months upfront and get 10% off.")),
        (L(lang, "ينفع أجرّب قبل ما أشترك؟", "Can I try before joining?"),
         L(lang, f"أيوه: 4 ريلز بالتصوير والمونتاج بـ{money(PRICING["trial_price"])} جنيه، وقيمتها تتخصم من أول شهر لو اشتركت خلال 30 يوم.", f"Yes: 4 reels shot and edited for EGP {money(PRICING["trial_price"])}, credited to your first month if you join within 30 days.")),
        (L(lang, "بتصوّروا برّه الاستوديو؟", "Do you shoot on location?"),
         L(lang, "أيوه، التصوير في مكانك بيتفق عليه حسب المكان ونوع المحتوى.", "Yes. Location shoots are arranged case by case, depending on the place and the content.")),
    ]
    faq_html = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faq)
    rules = [
        L(lang, "عقد 3 شهور على الأقل، والدفع مقدم أول كل شهر.", "Minimum 3-month contract, paid at the start of each month."),
        L(lang, "خصم 10% لو دفعت 3 شهور مرة واحدة.", "10% off when you pay 3 months upfront."),
        L(lang, "ميزانية الإعلان بتتدفع للمنصة مباشرة.", "Ad spend is paid directly to the platform."),
        L(lang, "الأسعار بالجنيه المصري.", "Prices are in Egyptian pounds."),
    ]
    main = f'''<section class="band-navy hero" style="padding-block:64px 56px">
  <div class="wrap" style="grid-template-columns:1fr">
    <div class="hero-copy">
      <span class="eyebrow" dir="ltr">{SEAM}PRICING</span>
      <h1>{L(lang, "الباقات والأسعار", "Plans and pricing")}</h1>
      <p class="lead">{L(lang, "أسعار واضحة من الأول. اختار الباقة، أو كلمنا ونرشحلك الأنسب لبيزنسك بعد Audit مجاني.", "Clear prices up front. Pick a plan, or talk to us and we'll recommend one after a free audit.")}</p>
    </div>
  </div>
</section>
<section>
  <div class="wrap page-gap">
    <div class="founders" id="founders">
      <div>
        <h2>{L(lang, "خصم المؤسسين", "Founders' offer")}</h2>
        <p>{L(lang, f"لأول 10 عملاء يمضوا عقد 3 شهور في شهر الافتتاح (15 نوفمبر – 15 ديسمبر 2026): خصم {PRICING["founders_discount"]}% على أول 3 شهور.", f"For the first 10 clients who sign a 3-month contract during our opening month (15 November – 15 December 2026): {PRICING["founders_discount"]}% off the first 3 months.")}</p>
      </div>
      <span class="big latin">−{PRICING["founders_discount"]}%</span>
    </div>
    <div>
      <div class="section-head"><h2>{L(lang, "الباقات الشهرية", "Monthly plans")}</h2><p>{L(lang, "كل باقة فيها بوستات وريلز وأيام تصوير في الاستوديو وإدارة إعلانات وتقارير أداء.", "Every plan covers posts, reels, studio shoot days, ads management and performance reports.")}</p></div>
      {reels_plans(lang)}
    </div>
    <div>
      <div class="section-head"><h2>{L(lang, "بودكاست واستوديو", "Podcast and studio")}</h2></div>
      {rates_table(lang, podcast_rows(lang) + [(L(lang, "ريلز منفصلة", "Standalone reels"), L(lang, "4 ريلز بالتصوير والمونتاج، وقيمتها تتخصم لو اشتركت خلال 30 يوم", "4 reels shot and edited, credited if you join a plan within 30 days"), money(PRICING["trial_price"]), L(lang, "جنيه", "EGP"))])}
    </div>
    <div>
      <div class="section-head"><h2>{L(lang, "قواعد التعامل", "Terms")}</h2></div>
      <ul class="rules">{"".join(f"<li>{r}</li>" for r in rules)}</ul>
    </div>
    <div class="faq">
      <div class="section-head"><h2>{L(lang, "أسئلة بتتكرر", "Common questions")}</h2></div>
      {faq_html}
    </div>
  </div>
</section>
{cta_band(lang)}'''
    return title, desc, main, ""

def p_audit(lang):
    title = L(lang, "Audit مجاني لصفحتك وإعلاناتك — Marvels", "Free Page & Ads Audit — Marvels")
    desc = L(lang, "احجز Audit مجاني لصفحتك وإعلاناتك مع Marvels: نقولك فين الرسايل والحجوزات اللي بتضيع، و3 خطوات تبدأ بيها.",
             "Book a free audit of your page and ads with Marvels: where messages and bookings slip away, and three steps to start with.")
    fields = L(lang, ["عيادة أو مركز طبي", "مطعم أو كافيه", "عقارات", "جيم أو بيوتي", "مدرسة أو سنتر", "مصنع أو شركة", "براند شخصي", "متجر أونلاين", "غير كده"],
               ["Clinic or medical centre", "Restaurant or café", "Real estate", "Gym or beauty", "School or tutoring", "Factory or company", "Personal brand", "Online store", "Other"])
    goals = L(lang, ["رسايل وحجوزات أكتر", "مبيعات أكتر", "ناس أكتر تعرف البراند", "محتوى أحسن للصفحة"],
              ["More messages and bookings", "More sales", "More brand awareness", "Better page content"])
    budgets = L(lang, ["مش بعمل إعلانات حاليًا", "أقل من 5,000 جنيه في الشهر", "5,000 – 20,000 جنيه", "أكتر من 20,000 جنيه"],
                ["Not running ads yet", "Under EGP 5,000 a month", "EGP 5,000 – 20,000", "Over EGP 20,000"])
    opt = lambda xs: "".join(f"<option>{x}</option>" for x in xs)
    c = CONFIG
    main = f'''<section class="band-navy hero" style="padding-block:64px 56px">
  <div class="wrap" style="grid-template-columns:1fr">
    <div class="hero-copy">
      <span class="eyebrow" dir="ltr">{SEAM}FREE AUDIT</span>
      <h1>{L(lang, "Audit مجاني لصفحتك", "A free audit of your page")}</h1>
      <p class="lead">{L(lang, "قولنا عن البيزنس بتاعك، وإحنا نراجع صفحتك وإعلاناتك ونرجعلك بتقرير قصير: فين بتخسر رسايل وحجوزات، و3 حاجات تبدأ بيها فورًا.", "Tell us about your business. We'll review your page and ads and come back with a short report: where you're losing messages and bookings, and three things to fix first.")}</p>
    </div>
  </div>
</section>
<section>
  <div class="wrap two-col">
    <div class="form-card">
      <form data-wa-form="{esc(L(lang, "طلب Audit مجاني — Marvels", "Free audit request — Marvels"))}" novalidate>
        <div class="form-grid">
          <div class="field"><label for="a-name">{L(lang, "الاسم", "Name")}</label>
            <input id="a-name" name="name" type="text" autocomplete="name" required data-label="{L(lang, "الاسم", "Name")}"></div>
          <div class="field"><label for="a-biz">{L(lang, "اسم البيزنس", "Business name")}</label>
            <input id="a-biz" name="business" type="text" autocomplete="organization" required data-label="{L(lang, "البيزنس", "Business")}"></div>
          <div class="field"><label for="a-field">{L(lang, "المجال", "Industry")}</label>
            <select id="a-field" name="field" data-label="{L(lang, "المجال", "Industry")}">{opt(fields)}</select></div>
          <div class="field"><label for="a-phone">{L(lang, "رقم الموبايل", "Mobile number")}</label>
            <input id="a-phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" required dir="ltr" placeholder="01xxxxxxxxx" data-label="{L(lang, "الموبايل", "Mobile")}"></div>
          <div class="field full"><label for="a-link">{L(lang, "لينك الصفحة", "Page link")} <span class="hint">{L(lang, "(فيسبوك أو إنستجرام أو تيك توك)", "(Facebook, Instagram or TikTok)")}</span></label>
            <input id="a-link" name="link" type="url" dir="ltr" required placeholder="https://" data-label="{L(lang, "الصفحة", "Page")}"></div>
          <div class="field"><label for="a-goal">{L(lang, "أهم هدف ليك", "Main goal")}</label>
            <select id="a-goal" name="goal" data-label="{L(lang, "الهدف", "Goal")}">{opt(goals)}</select></div>
          <div class="field"><label for="a-budget">{L(lang, "ميزانية الإعلانات الحالية", "Current ad budget")}</label>
            <select id="a-budget" name="budget" data-label="{L(lang, "ميزانية الإعلانات", "Ad budget")}">{opt(budgets)}</select></div>
          <div class="field full"><label for="a-notes">{L(lang, "حاجة عايز تقولها؟", "Anything else?")} <span class="hint">{L(lang, "(اختياري)", "(optional)")}</span></label>
            <textarea id="a-notes" name="notes" data-label="{L(lang, "ملاحظات", "Notes")}"></textarea></div>
        </div>
        <div class="form-actions">
          <button class="btn btn-cta" type="submit">{L(lang, "ابعت الطلب على واتساب", "Send request on WhatsApp")}</button>
          <span class="small">{L(lang, "مفيش حاجة بتتبعت غير لما تضغط إرسال في واتساب.", "Nothing is sent until you press send in WhatsApp.")}</span>
        </div>
      </form>
      {result_panel(lang)}
    </div>
    <aside class="aside-box">
      <h3>{L(lang, "هتاخد إيه من الـAudit", "What you get")}</h3>
      {checks([
        (L(lang, "مراجعة الصفحة والمحتوى", "Page and content review"), L(lang, "البايو، أول انطباع، ونوع المحتوى اللي شغال.", "Bio, first impression and which content works.")),
        (L(lang, "مراجعة الإعلانات", "Ads review"), L(lang, "لو عندك إعلانات شغالة: الاستهداف وتكلفة الرسالة.", "If you run ads: targeting and cost per message.")),
        (L(lang, "3 خطوات تبدأ بيها", "Three first steps"), L(lang, "حاجات تقدر تعملها بنفسك حتى لو مااشتغلتش معانا.", "Things you can do yourself, even if you don't work with us.")),
      ])}
      <h3>{L(lang, "أو كلمنا مباشرة", "Or reach us directly")}</h3>
      <ul class="contact-list">
        <li><span>{L(lang, "واتساب", "WhatsApp")}</span><b dir="ltr">{esc(c["phone"][lang])}</b></li>
        {f'<li><span>{L(lang, "الإيميل", "Email")}</span><b>{esc(c["email"][lang])}</b></li>' if c["email"] else ""}
        <li><span>{L(lang, "العنوان", "Address")}</span><b><a href="{esc(c["maps"])}" target="_blank" rel="noopener">{esc(c["address"][lang])}</a></b></li>
        {f'<li><span>{L(lang, "المواعيد", "Hours")}</span><b>{esc(c["hours"][lang])}</b></li>' if c["hours"] else ""}
      </ul>
      <a class="btn btn-chat" href="#" data-wa="{esc(L(lang, "أهلًا Marvels، عايز أحجز Audit مجاني لصفحتي.", "Hi Marvels, I'd like a free audit of my page."))}">{ICON_CHAT}{L(lang, "كلمنا واتساب", "WhatsApp us")}</a>
    </aside>
  </div>
</section>'''
    return title, desc, main, ""

# ------------------------------------------------------------------ experience
CLIENTS = _load("clients.json").get("clients", [])

def _client_bits(lang, c):
    name = L(lang, c.get("name_ar") or c.get("name_en", ""), c.get("name_en") or c.get("name_ar", ""))
    sector = L(lang, c.get("sector_ar") or c.get("sector_en", ""), c.get("sector_en") or c.get("sector_ar", ""))
    logo = (c.get("logo") or "").strip()
    if logo and not logo.startswith(("http://", "https://", "/")):
        logo = asset(lang, logo)
    initial = (L(lang, c.get("initial_ar", ""), c.get("initial_en", "")) or name[:1])[:2]
    return name, sector, logo, initial

def client_tile(lang, c, small=False):
    name, sector, logo, initial = _client_bits(lang, c)
    if logo:
        mark = f'<img src="{esc(logo)}" alt="{esc(name)}" loading="lazy">'
    else:
        mark = f'<span class="mono c-{esc(c.get("color", "orange"))}-card" aria-hidden="true">{esc(initial)}</span>'
    return mark

def client_cards(lang):
    out = []
    for c in CLIENTS:
        name, sector, _, _ = _client_bits(lang, c)
        out.append(f'''<article class="client">
  <div class="logo-box">{client_tile(lang, c)}</div>
  <div class="client-text"><h3>{esc(name)}</h3>{f'<span class="client-sector">{esc(sector)}</span>' if sector else ""}</div>
</article>''')
    return '<div class="client-grid">' + "".join(out) + "</div>"

def experience_teaser(lang):
    if not CLIENTS:
        return ""
    items = "".join(
        f'<li><div class="logo-box sm">{client_tile(lang, c)}</div><span>{esc(_client_bits(lang, c)[0])}</span></li>' for c in [c for c in CLIENTS if c.get("logo")][:8])
    return f'''<section>
  <div class="wrap">
    <div class="section-head">
      <h2>{L(lang, "خبراتنا", "Our experience")}</h2>
      <p>{L(lang, "مستشفيات وعيادات وبراندات في التجميل والأغذية والمجوهرات والتكنولوجيا، في مصر والسعودية.", "Hospitals, clinics and brands in beauty, food, jewelry and tech, in Egypt and Saudi Arabia.")}</p>
    </div>
    <ul class="logo-strip">{items}</ul>
    <a class="btn btn-line mt" href="{href(lang, "experience")}">{L(lang, "شوف كل العملاء ←", "See all clients →")}</a>
  </div>
</section>'''

def p_experience(lang):
    title = L(lang, "خبراتنا وعملاؤنا — Marvels", "Our Experience & Clients — Marvels")
    _names = [L(lang, c.get("name_ar", ""), c.get("name_en", "")) for c in CLIENTS]
    desc = L(lang, "براندات اشتغل معاها فريق Marvels: " + "، ".join(_names[:6]) + " وغيرهم.",
             "Brands the Marvels team has worked with: " + ", ".join(_names[:6]) + " and more.")
    facts = [
        (L(lang, "8 سنين", "8 years"), L(lang, "في الإعلانات المدفوعة وتحليل أداء البراندات", "in paid media and brand performance analysis")),
        (L(lang, "دولتين", "2 markets"), L(lang, "مصر والسعودية", "Egypt and Saudi Arabia")),
        (L(lang, "4 منصات", "4 platforms"), L(lang, "ميتا · جوجل · تيك توك · سناب شات", "Meta · Google · TikTok · Snapchat")),
        (L(lang, "+20 براند", "20+ brands"), L(lang, "رعاية صحية · تجميل · أغذية · مجوهرات · تكنولوجيا · صناعة", "Healthcare · Beauty · Food · Jewelry · Tech · Industry")),
    ]
    facts_html = "".join(f'<div class="fact"><b>{a}</b><span>{b}</span></div>' for a, b in facts)
    main = f'''<section class="band-navy hero" style="padding-block:64px 56px">
  <div class="wrap" style="grid-template-columns:1fr">
    <div class="hero-copy">
      <span class="eyebrow" dir="ltr">{SEAM}OUR EXPERIENCE</span>
      <h1>{L(lang, "خبراتنا", "Our experience")}</h1>
      <p class="lead">{L(lang, "قبل ما نفتح Marvels، اشتغل فريقنا على حملات ومحتوى لأكتر من 20 براند في مصر والسعودية، من مستشفيات وعيادات لبراندات تجميل وأغذية ومجوهرات. ودي الخبرة اللي بنبدأ منها معاك.", "Before opening Marvels, our team worked on campaigns and content for brands in Egypt and Saudi Arabia. This is part of the work we build on.")}</p>
    </div>
  </div>
</section>
<section>
  <div class="wrap page-gap">
    <div class="facts">{facts_html}</div>
    <div>
      <div class="section-head"><h2>{L(lang, "عملاؤنا", "Our clients")}</h2></div>
      {client_cards(lang)}
    </div>
  </div>
</section>
{cta_band(lang)}'''
    return title, desc, main, ""

# ------------------------------------------------------------------ articles
# Each block: ("p", text) | ("h2", text) | ("ul", [items]) | ("ol", [items])
# Articles are JSON files in content/articles/ (one per article). The file name becomes the URL:
# content/articles/shoot-day.json  ->  blog-shoot-day.html
SERVICES = ("ads", "reels", "podcast", "studio")
AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
EN_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def _load_articles():
    items = []
    for path in sorted(glob.glob(os.path.join(CONTENT, "articles", "*.json"))):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        if d.get("draft"):
            continue
        name = os.path.splitext(os.path.basename(path))[0]
        slug = "blog-" + re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
        kind = d.get("service") if d.get("service") in SERVICES else "reels"
        ta, te = d.get("title_ar") or d.get("title_en", ""), d.get("title_en") or d.get("title_ar", "")
        xa, xe = d.get("excerpt_ar") or d.get("excerpt_en", ""), d.get("excerpt_en") or d.get("excerpt_ar", "")
        ba, be = d.get("body_ar") or d.get("body_en", ""), d.get("body_en") or d.get("body_ar", "")
        items.append({"slug": slug, "kind": kind, "tag": kind.upper(), "mins": int(d.get("minutes") or 4),
                      "date": str(d.get("date") or "")[:10], "cover": (d.get("cover") or "").strip(),
                      "title": (ta, te), "excerpt": (xa, xe), "body": {"ar": ba, "en": be}})
    items.sort(key=lambda a: a["date"], reverse=True)
    return items

ARTICLES = _load_articles()

def _inline(text):
    # Editors escape Markdown characters ("\-", "1\."); keep the character, drop the backslash.
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!>~|])", r"\1", text)
    t = esc(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"__(.+?)__", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?![\s*])(.+?)(?<![\s*])\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+|/[^)\s]*|[a-z0-9-]+\.html[^)\s]*)\)", r'<a href="\2">\1</a>', t)
    return t

def md_to_html(md):
    """Small Markdown subset: ## / ### headings, paragraphs, - lists, 1. lists, **bold**, [links](url), ![alt](image)."""
    out, para, lst, lkind = [], [], [], None
    def flush_para():
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>"); para.clear()
    def flush_list():
        nonlocal lkind
        if lst:
            out.append(f"<{lkind}>" + "".join(f"<li>{_inline(x)}</li>" for x in lst) + f"</{lkind}>"); lst.clear()
        lkind = None
    for raw in (md or "").replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line:
            flush_para(); flush_list(); continue
        m_img = re.match(r"!\[([^\]]*)\]\(([^)\s]+)\)$", line)
        m_ul = re.match(r"[-*]\s+(.*)", line)
        m_ol = re.match(r"\d+[.)]\s+(.*)", line)
        if line.startswith("### "):
            flush_para(); flush_list(); out.append("<h3>" + _inline(line[4:]) + "</h3>")
        elif line.startswith("## ") or line.startswith("# "):
            flush_para(); flush_list(); out.append("<h2>" + _inline(line.lstrip("#").strip()) + "</h2>")
        elif m_img:
            flush_para(); flush_list(); out.append(f'<figure><img src="{esc(m_img.group(2))}" alt="{esc(m_img.group(1))}" loading="lazy"></figure>')
        elif m_ul or m_ol:
            flush_para()
            k = "ul" if m_ul else "ol"
            if lkind and lkind != k:
                flush_list()
            lkind = k
            lst.append((m_ul or m_ol).group(1))
        else:
            flush_list(); para.append(line)
    flush_para(); flush_list()
    return "\n".join(out)

ARTICLE_CTA = {
    "ads": (("عايز حد يبص على إعلاناتك ويقولك فين الفلوس بتضيع؟", "Want someone to review your ads and show you where money is lost?"), "audit", ("اطلب Audit مجاني", "Get a free audit")),
    "reels": (("ده بالظبط نظام يوم التصوير في باقات الريلز بتاعتنا.", "This is exactly the shoot-day system in our reels plans."), "reels", ("شوف خدمة الريلز", "See our reels service")),
    "podcast": (("عايز تسجّل في استوديو جاهز بالمونتاج والكليبات؟", "Want to record in a ready studio with editing and clips included?"), "podcast", ("شوف باقات البودكاست", "See podcast plans")),
    "studio": (("محتاج استوديو جاهز للتصوير في العبور؟", "Need a ready-to-shoot studio in Obour?"), "studio", ("احجز ساعات في الاستوديو", "Book studio hours")),
}

def article_date(lang, a):
    m = re.match(r"(\d{4})-(\d{2})", a["date"] or "")
    if not m:
        return ""
    y, mo = int(m.group(1)), int(m.group(2))
    return f"{AR_MONTHS[mo - 1]} {y}" if lang == "ar" else f"{EN_MONTHS[mo - 1]} {y}"

def article_meta(lang, a):
    mins = a["mins"]
    read = L(lang, f"{mins} دقايق قراءة" if mins <= 10 else f"{mins} دقيقة قراءة", f"{mins} min read")
    d = article_date(lang, a)
    return read + (f" · {d}" if d else "")

def cover_src(lang, a):
    c = a["cover"]
    if not c or c.startswith(("http://", "https://")):
        return c
    return c if c.startswith("/") else asset(lang, c)

def post_cards(lang, exclude=None):
    cards = []
    for a in ARTICLES:
        if a["slug"] == exclude:
            continue
        img = f'<img class="post-cover" src="{esc(cover_src(lang, a))}" alt="" loading="lazy">' if a["cover"] else ""
        cards.append(f'''<a class="post-card" href="{href(lang, a["slug"])}">
  {img}
  <span class="post-tag c-{a["kind"]}">{shield(a["kind"])}<span class="latin">{a["tag"]}</span></span>
  <h3>{esc(L(lang, *a["title"]))}</h3>
  <p>{esc(L(lang, *a["excerpt"]))}</p>
  <span class="post-meta">{article_meta(lang, a)}</span>
</a>''')
    if not cards:
        return f'<p class="muted">{L(lang, "المقالات قريبًا.", "Articles coming soon.")}</p>'
    return '<div class="post-grid">' + "".join(cards) + "</div>"

def p_blog(lang):
    title = L(lang, "مقالات عن الإعلانات والريلز والبودكاست — Marvels", "Articles on Ads, Reels & Podcasts — Marvels")
    desc = L(lang, "مقالات عملية من فريق Marvels عن الإعلانات الممولة والريلز والبودكاست للبيزنس في مصر.",
             "Practical articles from the Marvels team on paid ads, reels and podcasts for businesses in Egypt.")
    main = f'''<section class="band-navy hero" style="padding-block:64px 56px">
  <div class="wrap" style="grid-template-columns:1fr">
    <div class="hero-copy">
      <span class="eyebrow" dir="ltr">{SEAM}ARTICLES</span>
      <h1>{L(lang, "مقالات", "Articles")}</h1>
      <p class="lead">{L(lang, "اللي بنتعلمه من الشغل اليومي في الإعلانات والمحتوى، مكتوب بشكل تقدر تطبّقه على البيزنس بتاعك على طول.", "What we learn from day-to-day work in ads and content, written so you can apply it to your business right away.")}</p>
    </div>
  </div>
</section>
<section>
  <div class="wrap">{post_cards(lang)}</div>
</section>
{cta_band(lang)}'''
    return title, desc, main, ""

def make_article(a):
    def fn(lang):
        t = L(lang, *a["title"])
        title = f"{t} — Marvels"
        desc = L(lang, *a["excerpt"])
        cta_text, cta_slug, cta_btn = ARTICLE_CTA[a["kind"]]
        cover = f'<figure class="post-hero-img"><img src="{esc(cover_src(lang, a))}" alt=""></figure>' if a["cover"] else ""
        more = post_cards(lang, exclude=a["slug"]) if len(ARTICLES) > 1 else ""
        more_sec = f'''<section class="band-surface">
  <div class="wrap">
    <div class="section-head"><h2>{L(lang, "مقالات تانية", "More articles")}</h2></div>
    {more}
  </div>
</section>''' if more else ""
        main = f'''<section class="band-navy hero svc-hero" style="padding-block:56px 52px">
  <div class="wrap" style="grid-template-columns:1fr">
    <div class="hero-copy article-head">
      <a class="back" href="{href(lang, "blog")}">{L(lang, "→ كل المقالات", "← All articles")}</a>
      <span class="eyebrow" dir="ltr">MARVELS <b>{a["tag"]}</b></span>
      <h1>{esc(t)}</h1>
      <p class="post-meta-light">{article_meta(lang, a)}</p>
    </div>
  </div>
</section>
<section>
  <div class="wrap">
    <article class="prose">
      {cover}
      {md_to_html(a["body"][lang])}
      <div class="article-cta">
        <p>{L(lang, *cta_text)}</p>
        <a class="btn btn-cta" href="{href(lang, cta_slug)}">{L(lang, *cta_btn)}</a>
      </div>
    </article>
  </div>
</section>
{more_sec}'''
        return title, desc, main, f"svc-{a['kind']}"
    return fn

PAGES = {"index": p_index, "reels": p_reels, "podcast": p_podcast, "ads": p_ads,
         "studio": p_studio, "pricing": p_pricing, "experience": p_experience, "blog": p_blog, "audit": p_audit}
for _a in ARTICLES:
    PAGES[_a["slug"]] = make_article(_a)
SLUGS = list(PAGES.keys())

# ------------------------------------------------------------------ build
def _wa_href(m):
    from urllib.parse import quote
    url = "https://wa.me/" + CONFIG["wa_number"]
    msg = html.unescape(m.group(1))
    if msg:
        url += "?text=" + quote(msg)
    return 'href="' + esc(url) + '" data-wa="' + m.group(1) + '"'

def write(path, text):
    # Real WhatsApp links in the HTML itself (works without JS and for crawlers).
    if path.endswith(".html") and CONFIG["wa_number"]:
        text = re.sub(r'href="#" data-wa="([^"]*)"', _wa_href, text)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def favicon_svg():
    return emblem().replace('currentColor', '#12324A').replace('viewBox="0 0 120 132" aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg" viewBox="-6 -2 132 136"')

def build(preview=False):
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    for lang in ("ar", "en"):
        for slug, fn in PAGES.items():
            title, desc, main, cls = fn(lang)
            write(os.path.join(DIST, ("" if lang == "ar" else "en"), f"{slug}.html"), page(lang, slug, title, desc, main, cls))
    if preview:  # entry page for a claude.ai preview (the host supplies <html>/<body>)
        title, desc, main, cls = p_index("ar")
        write(os.path.join(HERE, "preview", "index.html"), page("ar", "index", title, desc, main, cls, for_artifact=True))
    # static files (images, uploads) -> dist/
    static = os.path.join(HERE, "static")
    if os.path.isdir(static):
        shutil.copytree(static, DIST, dirs_exist_ok=True)
    src = os.path.join(HERE, "src")
    os.makedirs(os.path.join(DIST, "assets"), exist_ok=True)
    shutil.copy(os.path.join(src, "site.css"), os.path.join(DIST, "assets", "site.css"))
    shutil.copy(os.path.join(src, "site.js"), os.path.join(DIST, "assets", "site.js"))
    write(os.path.join(DIST, "assets", "favicon.svg"), favicon_svg())
    # the editing dashboard
    admin = os.path.join(HERE, "admin")
    if os.path.isdir(admin):
        shutil.copytree(admin, os.path.join(DIST, "admin"), dirs_exist_ok=True)
    # 404 + robots + sitemap
    _, d404, _, _ = p_index("ar")
    write(os.path.join(DIST, "404.html"), page("ar", "index", "الصفحة مش موجودة — Marvels", d404,
        '''<section class="band-navy hero"><div class="wrap" style="grid-template-columns:1fr"><div class="hero-copy"><span class="eyebrow">404</span><h1>الصفحة دي مش موجودة</h1><p class="lead">يمكن اللينك اتغيّر. ارجع للرئيسية أو كلمنا على واتساب.</p><div class="hero-actions"><a class="btn btn-cta" href="/">الرئيسية</a><a class="btn btn-ghost" href="/en/">English</a></div></div></div></section>''').replace('href="assets/', 'href="/assets/').replace('src="assets/', 'src="/assets/'))
    write(os.path.join(DIST, "robots.txt"), f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {CONFIG['domain']}/sitemap.xml\n")
    import datetime
    today = datetime.date.today().isoformat()
    dates = {a["slug"]: a["date"] for a in ARTICLES if a["date"]}
    def u(l, s):
        alts = "".join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{url_of(hl, s)}"/>' for h, hl in (("ar", "ar"), ("en", "en"), ("x-default", "ar")))
        return f"<url><loc>{url_of(l, s)}</loc><lastmod>{dates.get(s, today)}</lastmod>{alts}</url>"
    urls = "".join(u(l, s) for l in ("ar", "en") for s in SLUGS)
    write(os.path.join(DIST, "sitemap.xml"), f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">{urls}</urlset>\n')
    print("built", sum(len(fs) for _, _, fs in os.walk(DIST)), "files,", len(ARTICLES), "articles,", len(CLIENTS), "clients")

if __name__ == "__main__":
    build(preview="--preview" in sys.argv)
