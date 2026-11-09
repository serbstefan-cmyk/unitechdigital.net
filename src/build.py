"""Build the multilingual UNITECH DIGITAL site.

    python src/build.py

Reads src/template.html and src/i18n/<lang>.json, writes index.html (English,
the default) and <lang>/index.html for every other language, plus sitemap.xml.
Edit texts in the JSON files and the layout in the template, then rebuild.
"""
import base64
import hashlib
import html
import json
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
SITE = "https://unitechdigital.net/"
LASTMOD = "2026-11-09"

# code, native name, og:locale. English first: it is the default at the root.
LANGS = [
    ("en", "English", "en_GB"),
    ("fr", "Français", "fr_FR"),
    ("nl", "Nederlands", "nl_NL"),
    ("de", "Deutsch", "de_DE"),
    ("it", "Italiano", "it_IT"),
    ("es", "Español", "es_ES"),
    ("pt", "Português", "pt_PT"),
    ("pl", "Polski", "pl_PL"),
    ("sv", "Svenska", "sv_SE"),
    ("da", "Dansk", "da_DK"),
    ("fi", "Suomi", "fi_FI"),
]
HTML_KEYS = {"hero_h1", "footer_tagline"}  # values that contain markup on purpose

# The only inline script: marks JS as available before first paint (scroll reveals).
# The Content Security Policy allows it by its hash and nothing else inline.
HEAD_SCRIPT = "document.documentElement.classList.add('js');"
HEAD_SCRIPT_HASH = "sha256-" + base64.b64encode(hashlib.sha256(HEAD_SCRIPT.encode("utf-8")).digest()).decode()
CSP = ("default-src 'self'; "
       f"script-src 'self' '{HEAD_SCRIPT_HASH}'; "
       "style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
       "object-src 'none'; base-uri 'self'; form-action 'none'")
EU_LANG_CODES = ["bg", "hr", "cs", "da", "nl", "en", "et", "fi", "fr", "de", "el", "hu",
                 "ga", "it", "lv", "lt", "mt", "pl", "pt", "ro", "sk", "sl", "es", "sv"]


def url_for(code: str) -> str:
    return SITE if code == "en" else f"{SITE}{code}/"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def jsonld(t: dict, code: str) -> str:
    org = {
        "@type": "Organization",
        "@id": f"{SITE}#org",
        "name": "UNITECH DIGITAL",
        "url": SITE,
        "logo": f"{SITE}assets/logo.png",
        "description": t["og_description"],
        "email": "stefan.serb@unitechdigital.net",
        "sameAs": ["https://www.linkedin.com/company/102183329/"],
        "knowsLanguage": EU_LANG_CODES,
        "areaServed": "Europe",
        "contactPoint": {"@type": "ContactPoint", "contactType": "sales",
                         "email": "stefan.serb@unitechdigital.net", "name": "Stefan Serb"},
        "subOrganization": [
            {"@type": "Organization", "legalName": "UNITECH DIGITAL sp. z o.o.", "taxID": "9532812157",
             "address": {"@type": "PostalAddress", "streetAddress": "ul. Pawia 3 lok. 3",
                         "postalCode": "85-309", "addressLocality": "Bydgoszcz", "addressCountry": "PL"}},
            {"@type": "Organization", "legalName": "UNITECH DIGITAL SOLUTIONS S.R.L.", "vatID": "RO45750762",
             "address": {"@type": "PostalAddress", "addressLocality": "Bucharest", "addressCountry": "RO"}},
        ],
    }
    page = {"@type": "WebPage", "@id": f"{url_for(code)}#page", "url": url_for(code),
            "name": t["meta_title"], "inLanguage": code, "about": {"@id": f"{SITE}#org"}}
    faq = {"@type": "FAQPage", "@id": f"{url_for(code)}#faq", "inLanguage": code,
           "mainEntity": [{"@type": "Question", "name": item["q"],
                           "acceptedAnswer": {"@type": "Answer", "text": item["a"]}} for item in t["faq"]]}
    data = {"@context": "https://schema.org", "@graph": [org, page, faq]}
    return json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")


def build_page(template: str, t: dict, code: str) -> str:
    base = "" if code == "en" else "../"
    hreflang = [f'<link rel="alternate" hreflang="{c}" href="{url_for(c)}">' for c, _, _ in LANGS]
    hreflang.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}">')
    items = []
    for c, name, _ in LANGS:
        href = (base or "./") if c == "en" else f"{base}{c}/"
        current = ' aria-current="true"' if c == code else ""
        items.append(f'<li><a href="{href}" hreflang="{c}" lang="{c}"{current}>{esc(name)} <span>{c.upper()}</span></a></li>')
    langswitch = (f'<details class="lang"><summary aria-label="{esc(t["lang_menu_label"])}">{code.upper()}</summary>'
                  f'<ul>{"".join(items)}</ul></details>')
    faq_html = "".join(f'<details><summary>{esc(i["q"])}</summary><p>{esc(i["a"])}</p></details>' for i in t["faq"])

    values = {
        "lang": code,
        "csp": CSP,
        "head_script": HEAD_SCRIPT,
        "base": base,
        "home": base or "./",
        "canonical": url_for(code),
        "og_locale": next(loc for c, _, loc in LANGS if c == code),
        "hreflang_html": "\n".join(hreflang),
        "langswitch_html": langswitch,
        "jsonld": jsonld(t, code),
        "strip_html": "".join(f"<span>{esc(s)}</span>" for s in t["strip"]),
        "svc1_chips_html": "".join(f'<span class="chip">{esc(s)}</span>' for s in t["svc1_chips"]),
        "svc2_chips_html": "".join(f'<span class="chip">{esc(s)}</span>' for s in t["svc2_chips"]),
        "lang_names_html": "".join(f"<span>{esc(s)}</span>" for s in t["lang_names"]),
        "faq_html": faq_html,
        "offer1_subject_url": urllib.parse.quote(t["offer1_subject"]),
        "offer2_subject_url": urllib.parse.quote(t["offer2_subject"]),
    }
    for key, value in t.items():
        if isinstance(value, str) and key not in values:
            values[key] = value if key in HTML_KEYS else esc(value)

    out = template
    for key, value in values.items():
        out = out.replace("{{" + key + "}}", value)
    if "{{" in out:
        start = out.index("{{")
        raise SystemExit(f"[{code}] unfilled placeholder: {out[start:start + 40]}")
    return out


def sitemap(codes: list) -> str:
    alts = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{c}" href="{url_for(c)}"/>' for c in codes)
    alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}"/>'
    urls = [f"  <url>\n    <loc>{url_for(c)}</loc>\n    <lastmod>{LASTMOD}</lastmod>{alts}\n  </url>" for c in codes]
    urls.append(f"  <url>\n    <loc>{SITE}privacy.html</loc>\n    <lastmod>{LASTMOD}</lastmod>\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(urls) + "\n</urlset>\n")


def main() -> None:
    template = (SRC / "template.html").read_text(encoding="utf-8")
    english = json.loads((SRC / "i18n" / "en.json").read_text(encoding="utf-8"))
    built = []
    for code, _, _ in LANGS:
        path = SRC / "i18n" / f"{code}.json"
        if not path.exists():
            print(f"skip {code}: no {path.name}")
            continue
        t = json.loads(path.read_text(encoding="utf-8"))
        missing = set(english) - set(t)
        if missing:
            raise SystemExit(f"[{code}] missing keys: {sorted(missing)}")
        for key in ("strip", "svc1_chips", "svc2_chips", "lang_names", "faq"):
            if len(t[key]) != len(english[key]):
                raise SystemExit(f"[{code}] {key} has {len(t[key])} items, English has {len(english[key])}")
        page = build_page(template, t, code)
        target = ROOT / "index.html" if code == "en" else ROOT / code / "index.html"
        target.parent.mkdir(exist_ok=True)
        target.write_text(page, encoding="utf-8", newline="\n")
        built.append(code)
    # Only languages that exist get hreflang/sitemap entries; rebuild after adding one.
    if len(built) != len(LANGS):
        print("note: not every language was built, so hreflang links point to missing pages until they are")
    (ROOT / "sitemap.xml").write_text(sitemap(built), encoding="utf-8", newline="\n")
    print("built:", ", ".join(built))


if __name__ == "__main__":
    sys.exit(main())
