#!/usr/bin/env python3
"""Render wikitext as a Wikipedia article and screenshot it (desktop + mobile).

    python wikishot.py elections/my-election.wiki

The input is the article's wikitext (infobox, lead, sections), optionally
preceded by a few "key: value" settings and a line with just "---":

    title: 2028 United States presidential election
    languages: 34
    ---
    {{Infobox election
    | election_name = 2028 United States presidential election
    ...

Nothing is imitated: Wikipedia's own parser renders the wikitext with its own
templates ({{Infobox election}}, {{Infobox legislative election}}, ...), and
the result is placed inside a real Wikipedia page (Vector 2022 on desktop,
Minerva on mobile) with Wikipedia's own stylesheets. The article is not saved
anywhere: the parse API renders it without creating a page.

Images in the wikitext can be:
  - a Commons/Wikipedia file name, as on Wikipedia:   image1 = Kamala Harris Vice Presidential Portrait (cropped).jpg
  - a local file, relative to the input file or repo: image1 = images/jane-doe.jpg
  - the lead photo of a Wikipedia article:            image1 = person:Nigel Farage
"""

import argparse
import base64
import html
import io
import json
import math
import os
import re
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlencode, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / ".cache" / "wikishot"
DEFAULT_OUTPUT_DIR = ROOT / "screenshots"

WIKI = "https://en.wikipedia.org"
API = WIKI + "/w/api.php"
USER_AGENT = ("WikiShot/1.0 (https://github.com/yechezkelbinstok-dev/Parliament; "
              "renders simulated-election articles for personal use)")
# Any ordinary, unprotected article: only its page frame (header, tabs, sidebars)
# is used, everything inside it is replaced.
FRAME_ARTICLE = "2019 Danish general election"
FRAME_MAX_AGE = 24 * 3600

SETTINGS = {
    "title": None,       # page title; default: the infobox's election_name
    "languages": "20",   # number on the desktop "N languages" button (0 = "Add languages")
    "theme": "light",    # light or dark
}

IMAGE_EXTENSIONS = ("png", "jpg", "jpeg", "gif", "svg", "webp")

# Page scripts that would show banners or surveys, log analytics, or look up
# data about the frame article. Everything else runs as on Wikipedia.
BLOCKED_MODULES = re.compile(
    r"^(ext\.centralNotice|ext\.quicksurveys|ext\.eventLogging|ext\.wikimediaEvents|ext\.navigationTiming"
    r"|ext\.testKitchen|ext\.readerExperiments|ext\.wikimediaCustomizations|ext\.checkUser|ext\.centralauth"
    r"|ext\.echo|ext\.cx|ext\.relatedArticles|mw\.externalguidance|wikibase\.databox"
    r"|ext\.readingLists\.bookmark\.anonymous)")  # its first-visit "new feature" dot
RETRY_HOSTS = {"en.wikipedia.org", "upload.wikimedia.org", "thumb.wikimedia.org"}
BLOCKED_URLS = re.compile(
    r"BannerLoader|CentralNotice|centralnotice|/beacon/|intake-analytics|intake-logging|geoiplookup"
    r"|login\.wikimedia\.org|auth\.wikimedia\.org|meta\.wikimedia\.org")

# Fonts that make the screenshots look like what most readers see: Arial and
# Georgia on Windows desktops, Roboto and Noto Serif on Android phones.
# Liberation Sans (metric clone of Arial) is assumed to be installed already.
FONT_CSS_URL = ("https://fonts.googleapis.com/css?family="
                "Gelasio:400,400i,700,700i|Roboto:400,400i,500,700,700i|Noto+Serif:400,400i,700,700i")

VARIANTS = {
    "desktop": dict(
        skin="vector-2022", frame_params={},
        viewport={"width": 1440, "height": 900}, mobile=False, scale=2,
        fonts={"sans-serif": "Liberation Sans", "serif": "Gelasio",
               "Arial": "Liberation Sans", "Helvetica": "Liberation Sans", "Georgia": "Gelasio"},
    ),
    "mobile": dict(
        skin="minerva", frame_params={"useformat": "mobile"},
        viewport={"width": 412, "height": 915}, mobile=True, scale=3,
        fonts={"sans-serif": "Roboto", "serif": "Noto Serif",
               "Arial": "Liberation Sans", "Helvetica": "Liberation Sans"},
    ),
}


class WikishotError(Exception):
    pass


# ---------------------------------------------------------------- HTTP

_session = requests.Session()
_session.headers["User-Agent"] = USER_AGENT


def http(method: str, url: str, **kwargs) -> requests.Response:
    """Request with retries: Wikimedia rate-limits shared addresses with 429s."""
    for attempt in range(10):
        response = _session.request(method, url, timeout=90, **kwargs)
        if response.status_code == 429 or response.status_code >= 500:
            try:
                wait = float(response.headers.get("retry-after", 2))
            except ValueError:
                wait = 2
            time.sleep(min(wait, 30) + attempt)
            continue
        response.raise_for_status()
        return response
    response.raise_for_status()
    return response


def api(**params) -> dict:
    params.update(format="json", formatversion=2)
    data = http("POST", API, data=params).json()
    if "error" in data:
        raise WikishotError(f"Wikipedia API error: {data['error'].get('info', data['error'])}")
    return data


# ---------------------------------------------------------------- input

def read_input(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    settings = dict(SETTINGS)
    head, sep, body = text.partition("\n---\n")
    if sep and all(re.match(r"^\s*([\w-]+)\s*:", line) or not line.strip() for line in head.splitlines()):
        for line in head.splitlines():
            if not line.strip():
                continue
            key, _, value = line.partition(":")
            key = key.strip().lower()
            if key not in SETTINGS:
                raise WikishotError(f"unknown setting {key!r} (known: {', '.join(SETTINGS)})")
            settings[key] = value.strip()
        wikitext = body
    else:
        wikitext = text

    if not settings["title"]:
        match = re.search(r"\|\s*election_name\s*=\s*([^\n|]+)", wikitext)
        if match:
            settings["title"] = re.sub(r"'{2,}|\[\[(?:[^|\]]*\|)?|\]\]", "", match.group(1)).strip()
        else:
            settings["title"] = path.stem.replace("-", " ").replace("_", " ")
    if settings["theme"] not in ("light", "dark"):
        raise WikishotError("theme must be light or dark")
    try:
        settings["languages"] = int(settings["languages"])
    except ValueError:
        raise WikishotError("languages must be a whole number") from None
    return settings, wikitext


def resolve_people(wikitext: str) -> str:
    """Replace person:Article Name with that article's lead image file."""
    pattern = re.compile(r"(?<==)([ \t]*)person:[ \t]*([^|\n\]}]+)")
    names = sorted(set(m.group(2).strip() for m in pattern.finditer(wikitext)))
    if not names:
        return wikitext
    found = {}
    for i in range(0, len(names), 50):
        data = api(action="query", prop="pageimages", piprop="name", redirects=1,
                   titles="|".join(names[i:i + 50]))["query"]
        aliases = {}
        for entry in data.get("normalized", []) + data.get("redirects", []):
            aliases[entry["to"]] = aliases.get(entry["from"], entry["from"])
        for page in data.get("pages", []):
            original = page["title"]
            while original in aliases:
                original = aliases[original]
            if "pageimage" in page:
                found[original] = page["pageimage"]
    missing = [n for n in names if n not in found]
    if missing:
        raise WikishotError(f"no Wikipedia photo found for: {', '.join(missing)}")
    return pattern.sub(lambda m: m.group(1) + found[m.group(2).strip()], wikitext)


def find_local_images(wikitext: str, base_dirs: list[Path]) -> tuple[str, dict]:
    """Swap local image paths for placeholder names the parser will report as missing."""
    token = secrets.token_hex(4)
    local = {}
    pattern = re.compile(
        r"(?<=[=:])([ \t]*)([^\n|=\[\]{}<>]+?\.(?:%s))(?=[ \t]*(?:\||\]\]|\}\}|\n|$))"
        % "|".join(IMAGE_EXTENSIONS), re.IGNORECASE)

    def swap(match):
        candidate = match.group(2).strip()
        for base in base_dirs:
            path = (base / candidate).resolve()
            if path.is_file():
                name = f"Wikishot-{token}-{len(local) + 1}.png"
                local[name] = path
                return match.group(1) + name
        return match.group(0)

    return pattern.sub(swap, wikitext), local


# ---------------------------------------------------------------- local images

def image_data_uri(path: Path, box_w: int | None, box_h: int | None, scale: float) -> tuple[str, int, int]:
    """Return (data URI, display width, display height) fitted into the box."""
    if path.suffix.lower() == ".svg":
        svg = path.read_text(encoding="utf-8")
        w, h = svg_size(svg)
        width, height = fit(w, h, box_w, box_h)
        return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode(), width, height

    # Like MediaWiki: scale to fit inside the box, never crop.
    image = Image.open(path)
    image.load()
    w, h = image.size
    width, height = fit(w, h, box_w, box_h)
    target = (max(1, round(width * scale)), max(1, round(height * scale)))
    if target[0] < w:
        image = image.resize(target, Image.LANCZOS)
    buffer = io.BytesIO()
    if image.mode in ("RGBA", "LA", "P"):
        image.save(buffer, "PNG")
        mime = "image/png"
    else:
        image.convert("RGB").save(buffer, "JPEG", quality=92)
        mime = "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(buffer.getvalue()).decode(), width, height


def svg_size(svg: str) -> tuple[float, float]:
    root = re.search(r"<svg\b[^>]*>", svg, re.DOTALL)
    attrs = root.group(0) if root else ""
    w = re.search(r'\bwidth="([\d.]+)', attrs)
    h = re.search(r'\bheight="([\d.]+)', attrs)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    box = re.search(r'viewBox="[\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', attrs)
    if box:
        return float(box.group(1)), float(box.group(2))
    return 300.0, 150.0


def fit(w: float, h: float, box_w: int | None, box_h: int | None) -> tuple[int, int]:
    if not box_w and not box_h:
        box_w = 220
    ratio = min(box_w / w if box_w else float("inf"), box_h / h if box_h else float("inf"))
    return max(1, round(w * ratio)), max(1, round(h * ratio))


def insert_local_images(soup: BeautifulSoup, local: dict, scale: float) -> None:
    for element in soup.select(".mw-broken-media"):
        name = element.get_text().removeprefix("File:").replace("_", " ").strip()
        match = next((k for k in local if k.replace("_", " ").lower() == name.lower()), None)
        if match is None:
            continue
        box_w = int(element["data-width"]) if element.get("data-width") else None
        box_h = int(element["data-height"]) if element.get("data-height") else None
        uri, width, height = image_data_uri(local[match], box_w, box_h, scale)
        wrapper = element.find_parent(attrs={"typeof": re.compile("mw:File")}) or element
        if wrapper.get("typeof"):
            wrapper["typeof"] = "mw:File"
            wrapper.attrs.pop("data-mw", None)
        link = soup.new_tag("a", href=f"/wiki/File:{local[match].stem}", attrs={"class": "mw-file-description"})
        link.append(soup.new_tag("img", src=uri, decoding="async", width=str(width), height=str(height),
                                 attrs={"class": "mw-file-element", "alt": ""}))
        if wrapper is element:
            element.replace_with(link)
        else:
            wrapper.clear()
            wrapper.append(link)


# ---------------------------------------------------------------- page frame

def get_frame(variant: str) -> str:
    """A real Wikipedia article page, cached for a day, to place the content in."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"frame-{variant}.html"
    if path.exists() and time.time() - path.stat().st_mtime < FRAME_MAX_AGE:
        return path.read_text(encoding="utf-8")
    url = f"{WIKI}/wiki/{FRAME_ARTICLE.replace(' ', '_')}"
    page = http("GET", url, params=VARIANTS[variant]["frame_params"]).text
    path.write_text(page, encoding="utf-8")
    return page


def expand_modules(spec: str) -> list[str]:
    """Expand ResourceLoader's compact module list: 'a.b.c,d|e' -> a.b.c, a.b.d, e."""
    modules = []
    for group in spec.split("|"):
        parts = group.split(",")
        prefix = parts[0].rsplit(".", 1)[0] if "." in parts[0] else ""
        modules.append(parts[0])
        modules.extend(f"{prefix}.{p}" if prefix else p for p in parts[1:])
    return modules


def patch_scripts(soup: BeautifulSoup, title: str, parsed: dict) -> None:
    """Point the page's script configuration at the new article.

    The page keeps Wikipedia's own JavaScript, which is what fills in the
    Appearance menu, collapses mobile sections and so on. Its configuration
    still describes the frame article, so the title is swapped in and the
    modules that would fetch data about that article (or show banners and
    surveys) are dropped.
    """
    page_name = title.replace(" ", "_")
    for script in soup.find_all("script"):
        if script.get("type") == "application/ld+json":
            script.decompose()
            continue
        text = script.string
        if not text or "RLCONF" not in text and "RLPAGEMODULES" not in text:
            continue
        for key, value in (("wgPageName", page_name), ("wgRelevantPageName", page_name), ("wgTitle", title)):
            text = re.sub(rf'"{key}":"(?:[^"\\]|\\.)*"', lambda m: f'"{key}":{json.dumps(value)}', text)
        text = re.sub(r'"wgWikibaseItemId":"[^"]*"', '"wgWikibaseItemId":null', text)
        match = re.search(r"RLPAGEMODULES=(\[[^\]]*\])", text)
        if match:
            modules = [m for m in json.loads(match.group(1)) if not BLOCKED_MODULES.match(m)]
            modules += [m for m in parsed.get("modules", []) if m not in modules and not BLOCKED_MODULES.match(m)]
            text = text[:match.start(1)] + json.dumps(modules) + text[match.end(1):]
        script.string = text


def build_page(variant: str, settings: dict, parsed: dict, content: BeautifulSoup) -> str:
    skin = VARIANTS[variant]["skin"]
    soup = BeautifulSoup(get_frame(variant), "lxml")
    patch_scripts(soup, settings["title"], parsed)
    if settings["theme"] == "dark":
        html_tag = soup.html
        html_tag["class"] = [c for c in html_tag.get("class", []) if not c.startswith("skin-theme-clientpref-")] \
            + ["skin-theme-clientpref-night"]
        for script in soup.find_all("script"):
            if script.string and "skin-theme-clientpref-day" in script.string:
                script.string = script.string.replace("skin-theme-clientpref-day", "skin-theme-clientpref-night")

    # Stylesheets the content needs that the frame article did not load.
    loaded = set()
    first_link = None
    for link in soup.find_all("link", rel="stylesheet"):
        query = parse_qs(urlparse(link.get("href", "")).query)
        if "modules" in query:
            loaded.update(expand_modules(query["modules"][0]))
            first_link = first_link or link
    missing = [m for m in parsed.get("modulestyles", []) if m not in loaded]
    if missing and first_link is not None:
        extra = soup.new_tag("link", rel="stylesheet", href="/w/load.php?" + urlencode(
            {"lang": "en", "modules": "|".join(missing), "only": "styles", "skin": skin}))
        first_link.insert_after(extra)

    title = settings["title"]
    soup.title.string = f"{title} - Wikipedia"
    heading = soup.find(id="firstHeading")
    heading.clear()
    heading.append(BeautifulSoup(parsed["displaytitle"], "lxml").body.contents[0])

    # The article itself.
    new = content.find(class_="mw-parser-output")
    if variant == "mobile":
        # The mobile page view wraps each section body so it can collapse.
        for section in new.find_all("section", recursive=False):
            section_heading = section.find("div", class_="mw-heading", recursive=False)
            if section_heading is None:
                continue
            body = soup.new_tag("div", attrs={"class": "mw-collapsible-content"})
            for child in list(section_heading.next_siblings):
                body.append(child.extract())
            section_heading.insert_after(body)
    old = soup.find(id="mw-content-text").find(class_="mw-parser-output")
    old.replace_with(new)

    indicators = soup.find(class_="mw-indicators")
    if indicators is not None:
        indicators.clear()
        for name, markup in (parsed.get("indicators") or {}).items():
            indicator = soup.new_tag("div", id=f"mw-indicator-{name}", attrs={"class": "mw-indicator"})
            indicator.append(BeautifulSoup(f'<div class="mw-parser-output">{markup}</div>', "lxml").body.contents[0])
            indicators.append(indicator)

    # Categories sit at the very end of a real article; with a short test
    # article they would end up right under the infobox, so leave them out.
    catlinks = soup.find(id="catlinks")
    if catlinks is not None:
        catlinks.decompose()

    for element_id in ("siteNotice", "mw-content-subtitle"):
        element = soup.find(id=element_id)
        if element is not None:
            element.clear()

    lastmod = soup.find(id="footer-info-lastmod")
    if lastmod is not None:
        now = datetime.now(timezone.utc)
        lastmod.string = (f" This page was last edited on {now.day} {now:%B %Y}, at {now:%H:%M} (UTC).")

    if variant == "desktop":
        rebuild_toc(soup, parsed.get("sections", []))
        label = soup.select_one("#p-lang-btn-label .vector-dropdown-label-text")
        if label is not None:
            n = settings["languages"]
            label.string = "Add languages" if n <= 0 else f"{n} language{'s' if n != 1 else ''}"

    # Load every image immediately so nothing is missing from the screenshot.
    for img in soup.find_all("img"):
        img.attrs.pop("loading", None)
    return str(soup)


def rebuild_toc(soup: BeautifulSoup, sections: list[dict]) -> None:
    toc_list = soup.find(id="mw-panel-toc-list")
    if toc_list is None:
        return
    toc_list.clear()
    top = BeautifulSoup(
        '<li id="toc-mw-content-text" class="vector-toc-list-item vector-toc-level-1 vector-toc-list-item-active">'
        '<a href="#" class="vector-toc-link"><div class="vector-toc-text">(Top)</div></a></li>', "lxml").li
    toc_list.append(top)

    parents = {0: toc_list}
    for section in sections:
        level = int(section["toclevel"])
        anchor = section.get("linkAnchor") or section["anchor"]
        item = BeautifulSoup(
            f'<li id="toc-{html.escape(anchor, quote=True)}" class="vector-toc-list-item vector-toc-level-{level}">'
            f'<a class="vector-toc-link" href="#{html.escape(anchor, quote=True)}"><div class="vector-toc-text">'
            f'<span class="vector-toc-numb">{section["number"]}</span><span>{section["line"]}</span></div></a>'
            f'<ul id="toc-{html.escape(anchor, quote=True)}-sublist" class="vector-toc-list"></ul></li>', "lxml").li
        parent = parents.get(level - 1, toc_list)
        parent.append(item)
        parents[level] = item.find("ul")
        for deeper in [k for k in parents if k > level]:
            del parents[deeper]

    # Sections with subsections get the collapse toggle Vector adds.
    for item in toc_list.find_all("li"):
        sublist = item.find("ul", recursive=False)
        if sublist is not None and sublist.find("li"):
            toggle = BeautifulSoup(
                f'<button aria-controls="{sublist["id"]}" class="cdx-button cdx-button--weight-quiet '
                f'cdx-button--icon-only vector-toc-toggle"><span class="vector-icon mw-ui-icon-wikimedia-expand">'
                f'</span><span>Toggle subsection</span></button>', "lxml").button
            sublist.insert_before(toggle)


# ---------------------------------------------------------------- fonts

def ensure_fonts() -> Path:
    font_dir = CACHE_DIR / "fonts"
    if font_dir.exists() and any(font_dir.glob("*.ttf")):
        return font_dir
    font_dir.mkdir(parents=True, exist_ok=True)
    css = http("GET", FONT_CSS_URL).text  # an old-style client gets plain TTF files
    for block in re.findall(r"@font-face\s*{(.*?)}", css, re.DOTALL):
        family = re.search(r"font-family:\s*'([^']+)'", block).group(1)
        style = re.search(r"font-style:\s*(\w+)", block).group(1)
        weight = re.search(r"font-weight:\s*(\d+)", block).group(1)
        url = re.search(r"url\((https://[^)]+)\)", block).group(1)
        (font_dir / f"{family.replace(' ', '')}-{weight}-{style}.ttf").write_bytes(http("GET", url).content)
    return font_dir


def fontconfig_file(variant: str, font_dir: Path) -> Path:
    aliases = "\n".join(
        f'  <alias binding="same"><family>{family}</family><prefer><family>{target}</family></prefer></alias>'
        for family, target in VARIANTS[variant]["fonts"].items())
    config = f"""<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>/usr/share/fonts</dir>
  <dir>/usr/local/share/fonts</dir>
  <dir>{font_dir}</dir>
  <cachedir>{CACHE_DIR / 'fontconfig-cache'}</cachedir>
{aliases}
</fontconfig>
"""
    path = CACHE_DIR / f"fonts-{variant}.conf"
    path.write_text(config, encoding="utf-8")
    return path


# ---------------------------------------------------------------- rendering

def parse_wikitext(wikitext: str, title: str, variant: str) -> dict:
    params = dict(action="parse", title=title, text=wikitext, contentmodel="wikitext", parsoid=1,
                  prop="text|modules|modulestyles|sections|displaytitle|indicators",
                  disablelimitreport=1, useskin=VARIANTS[variant]["skin"])
    if variant == "mobile":
        params["mobileformat"] = 1
    return api(**params)["parse"]


INFOBOX_RECT_JS = """() => {
    const box = document.querySelector('.mw-parser-output .infobox');
    if (!box) return null;
    const rects = [box.getBoundingClientRect()];
    const caption = box.querySelector('caption');
    if (caption) rects.push(caption.getBoundingClientRect());
    const top = Math.min(...rects.map(r => r.top)) + window.scrollY;
    const bottom = Math.max(...rects.map(r => r.bottom)) + window.scrollY;
    const left = Math.min(...rects.map(r => r.left)) + window.scrollX;
    const right = Math.max(...rects.map(r => r.right)) + window.scrollX;
    return {x: left, y: top, width: right - left, height: bottom - top};
}"""


def screenshot(variant: str, page_html: str, title: str, out_base: Path, scale: float,
               infobox_shot: bool) -> list[Path]:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

    settings = VARIANTS[variant]
    font_dir = ensure_fonts()
    env = dict(os.environ, FONTCONFIG_FILE=str(fontconfig_file(variant, font_dir)))
    url = f"{WIKI}/wiki/" + requests.utils.quote(title.replace(" ", "_"), safe="()_,:'!")
    written = []

    def handle(route):
        request_url = route.request.url
        if route.request.is_navigation_request() and unquote(request_url.split("#")[0]) == unquote(url):
            route.fulfill(status=200, content_type="text/html; charset=utf-8", body=page_html)
        elif BLOCKED_URLS.search(request_url):
            route.abort()
        elif route.request.method == "GET" and urlparse(request_url).hostname in RETRY_HOSTS:
            # Wikimedia rate-limits shared addresses; retry instead of leaving a hole.
            for attempt in range(6):
                try:
                    response = route.fetch(timeout=60_000)
                except Exception:
                    response = None
                if response is not None and response.status != 429 and response.status < 500:
                    route.fulfill(response=response)
                    return
                time.sleep(1.5 * (attempt + 1))
            if response is not None:
                route.fulfill(response=response)
            else:
                route.abort()
        else:
            route.continue_()

    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    with sync_playwright() as p:
        browser = p.chromium.launch(env=env, proxy={"server": proxy} if proxy else None)
        context = browser.new_context(viewport=settings["viewport"], device_scale_factor=scale,
                                      is_mobile=settings["mobile"], has_touch=settings["mobile"])
        context.route("**/*", handle)
        page = context.new_page()
        # The article is served at its would-be Wikipedia address, so the page's
        # own scripts run exactly as they do on Wikipedia.
        page.goto(url, wait_until="load", timeout=120_000)
        skin_module = "skins.vector.js" if variant == "desktop" else "skins.minerva.scripts"
        try:
            page.wait_for_function(
                "m => window.mw && mw.loader && ['ready', 'error'].includes(mw.loader.getState(m))",
                arg=skin_module, timeout=60_000)
            page.wait_for_load_state("networkidle", timeout=30_000)
        except PlaywrightTimeout:
            print(f"warning: {variant} page scripts did not finish loading", file=sys.stderr)
        try:
            # "networkidle" counts as reached once it has happened, so wait for
            # the images themselves.
            page.wait_for_function("[...document.images].every(i => i.complete || i.loading === 'lazy')",
                                   timeout=90_000)
        except PlaywrightTimeout:
            print(f"warning: {variant}: some images were still loading", file=sys.stderr)
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(500)
        broken = page.evaluate("[...document.images].filter(i => i.complete && !i.naturalWidth && i.src)"
                               ".map(i => decodeURIComponent(i.src.split('/').pop()))")
        if broken:
            print(f"warning: {variant}: images failed to load: {', '.join(broken)}", file=sys.stderr)

        # Capture down to the end of the infobox. Make the window that tall first:
        # Chromium only paints images (and decodes them) once they are on screen,
        # so a capture reaching below the window can come out with blank images.
        width = settings["viewport"]["width"]
        bottom = settings["viewport"]["height"]
        for _ in range(2):  # resizing can reflow the page, so measure again
            rect = page.evaluate(INFOBOX_RECT_JS)
            if rect:
                bottom = max(bottom, rect["y"] + rect["height"] + (24 if settings["mobile"] else 40))
            bottom = math.ceil(min(bottom, page.evaluate("document.documentElement.scrollHeight")))
            page.set_viewport_size({"width": width, "height": bottom})
            page.evaluate("Promise.all([...document.images].map(i => i.decode().catch(() => null)))")
            page.wait_for_timeout(300)

        path = out_base.with_name(f"{out_base.name}-{variant}.png")
        page.screenshot(path=str(path), clip={"x": 0, "y": 0, "width": width, "height": bottom})
        written.append(path)

        if infobox_shot and rect:
            pad = 8
            path = out_base.with_name(f"{out_base.name}-infobox.png")
            page.screenshot(path=str(path), clip={
                "x": rect["x"] - pad, "y": rect["y"] - pad,
                "width": rect["width"] + 2 * pad, "height": rect["height"] + 2 * pad})
            written.append(path)
        browser.close()
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help=".wiki file with the article's wikitext")
    parser.add_argument("-o", "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--only", choices=list(VARIANTS), help="render just one of desktop/mobile")
    parser.add_argument("--scale", type=float,
                        help="pixel density of the screenshots (default: 2 desktop, 3 mobile like a phone)")
    args = parser.parse_args()

    try:
        settings, wikitext = read_input(args.input)
        wikitext = resolve_people(wikitext)
        wikitext, local_images = find_local_images(wikitext, [args.input.resolve().parent, ROOT])
        args.output_dir.mkdir(parents=True, exist_ok=True)
        out_base = args.output_dir / args.input.stem
        for variant in [args.only] if args.only else list(VARIANTS):
            scale = args.scale or VARIANTS[variant]["scale"]
            parsed = parse_wikitext(wikitext, settings["title"], variant)
            content = BeautifulSoup(parsed["text"], "lxml")
            insert_local_images(content, local_images, scale=max(scale, 2))
            page_html = build_page(variant, settings, parsed, content)
            for path in screenshot(variant, page_html, settings["title"], out_base, scale,
                                   infobox_shot=variant == "desktop"):
                print(f"wrote {path}")
    except (OSError, WikishotError, requests.RequestException) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
