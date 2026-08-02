"""
Convertit le Markdown généré par Mistral en une page HTML stylée,
et l'enregistre dans le dossier d'archives (base de la future "plateforme").
"""

import os
import re
from datetime import date
from urllib.parse import urlparse

import markdown as md

from config import OUTPUT_DIR

MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

# Mots à ignorer en tête de titre pour ne garder que le mot-clé principal
_LEADING_STOPWORDS = {"le", "la", "les", "l", "un", "une", "des", "du", "de", "au", "aux", "à"}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tech Daily — {date}</title>
<style>
  :root {{
    --bg: #fafafa;
    --text: #1a1a1a;
    --text-muted: #555;
    --accent: #ff5c35;
    --link: #0066cc;
    --border: #ddd;
    --img-bg: #eee;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #15130f;
      --text: #e9e6e1;
      --text-muted: #b6b0a8;
      --accent: #ff8360;
      --link: #6cb3ff;
      --border: #35322c;
      --img-bg: #2a2822;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 720px;
    margin: 40px auto;
    padding: 0 20px;
    line-height: 1.6;
    color: var(--text);
    background: var(--bg);
  }}
  h1 {{ font-size: 1.8em; border-bottom: 3px solid var(--accent); padding-bottom: 10px; }}
  h2 {{ font-size: 1.3em; margin-top: 2em; color: var(--accent); }}
  h3 {{ font-size: 1.05em; margin-top: 1.6em; }}
  p {{ color: var(--text); }}
  a {{ color: var(--link); text-decoration: none; word-break: break-word; }}
  a:hover {{ text-decoration: underline; }}
  .nav {{ margin-bottom: 30px; font-size: 0.9em; }}
  hr {{ border: none; border-top: 1px solid var(--border); margin: 2em 0; }}
  img {{
    display: block;
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 14px 0 6px;
    background: var(--img-bg);
  }}
  @media (max-width: 600px) {{
    body {{ margin: 20px auto; padding: 0 16px; line-height: 1.55; }}
    h1 {{ font-size: 1.5em; }}
    h2 {{ font-size: 1.15em; margin-top: 1.6em; }}
    h3 {{ font-size: 1em; }}
  }}
</style>
</head>
<body>
<div class="nav"><a href="index.html">← Toutes les newsletters</a></div>
{content}
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tech Daily — Archives</title>
<style>
  :root {{
    --bg: #fafafa;
    --text: #1a1a1a;
    --text-muted: #777;
    --accent: #ff5c35;
    --link: #0066cc;
    --border: #e2e2e2;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #15130f;
      --text: #e9e6e1;
      --text-muted: #948e84;
      --accent: #ff8360;
      --link: #6cb3ff;
      --border: #33302a;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 720px;
    margin: 40px auto;
    padding: 0 20px;
    color: var(--text);
    background: var(--bg);
  }}
  h1 {{ border-bottom: 3px solid var(--accent); padding-bottom: 10px; }}
  ul {{ list-style: none; padding: 0; margin: 1.5em 0 0; }}
  li {{ border-bottom: 1px solid var(--border); }}
  li a {{ display: block; padding: 14px 0; color: var(--text); text-decoration: none; }}
  li a:hover .entry-date {{ color: var(--link); }}
  .entry-date {{ font-size: 1.05em; font-weight: 600; text-transform: capitalize; }}
  .entry-keywords {{ font-size: 0.9em; color: var(--text-muted); margin-top: 4px; }}
  @media (max-width: 600px) {{
    body {{ margin: 20px auto; padding: 0 16px; }}
  }}
</style>
</head>
<body>
<h1>Tech Daily — Archives</h1>
<ul>
{items}
</ul>
</body>
</html>
"""


def _normalize_url(url):
    """Ignore le protocole et la query string pour comparer deux liens de façon robuste."""
    parsed = urlparse(url)
    return (parsed.netloc + parsed.path).rstrip("/")


def _insert_article_images(markdown_text, articles):
    """
    Ajoute l'image originale de chaque article (celle du flux RSS) juste après son titre
    ###, en la faisant correspondre au lien source déjà présent dans le Markdown généré
    par le modèle. Aucune image n'est inventée : si l'article n'a pas d'image dans le
    flux RSS, aucune image n'est ajoutée.
    """
    image_by_link = {
        _normalize_url(a["link"]): a["image"]
        for a in articles
        if a.get("image")
    }
    if not image_by_link:
        return markdown_text

    sections = re.split(r"(?=^### )", markdown_text, flags=re.MULTILINE)

    def add_image(section):
        if not section.startswith("### ") or "![" in section:
            return section
        for normalized_link, image_url in image_by_link.items():
            if normalized_link in section:
                heading, _, rest = section.partition("\n")
                return f"{heading}\n![]({image_url})\n{rest}"
        return section

    return "".join(add_image(section) for section in sections)


def render_newsletter(markdown_text, output_dir=None, articles=None):
    """
    Génère le fichier HTML du jour + met à jour l'index des archives.
    Retourne le chemin du fichier HTML créé.
    """
    output_dir = output_dir or OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    if articles:
        markdown_text = _insert_article_images(markdown_text, articles)

    today = date.today().isoformat()
    filename = f"{today}.html"
    filepath = os.path.join(output_dir, filename)

    content_html = md.markdown(markdown_text)
    full_html = HTML_TEMPLATE.format(date=today, content=content_html)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_html)

    _update_index(output_dir)

    return filepath


def _format_date_fr(iso_date):
    """Convertit '2026-08-02' en '2 août 2026'."""
    d = date.fromisoformat(iso_date)
    return f"{d.day} {MONTHS_FR[d.month - 1]} {d.year}"


def _keyword_from_title(title):
    """Extrait le mot-clé principal (souvent une entité) en tête d'un titre d'article."""
    normalized = title.replace("’", "'").replace("'", " ")
    words = re.findall(r"[A-Za-zÀ-ÿ]+", normalized)
    for word in words:
        if word.lower() not in _LEADING_STOPWORDS:
            return word
    return words[0] if words else ""


def _keywords_for_newsletter(filepath, limit=5):
    """Récupère les mots-clés des articles (titres <h3>) d'une newsletter archivée."""
    with open(filepath, encoding="utf-8") as f:
        html = f.read()

    keywords = []
    for title in re.findall(r"<h3>(.*?)</h3>", html):
        keyword = _keyword_from_title(title)
        if keyword and keyword not in keywords:
            keywords.append(keyword)
        if len(keywords) >= limit:
            break

    return keywords


def _update_index(output_dir):
    files = sorted(
        (f for f in os.listdir(output_dir) if f.endswith(".html") and f != "index.html"),
        reverse=True,
    )

    entries = []
    for f in files:
        iso_date = f.replace(".html", "")
        keywords = _keywords_for_newsletter(os.path.join(output_dir, f))
        entries.append(f"""  <li><a href="{f}">
    <div class="entry-date">{_format_date_fr(iso_date)}</div>
    <div class="entry-keywords">{" · ".join(keywords)}</div>
  </a></li>""")

    items = "\n".join(entries)
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(INDEX_TEMPLATE.format(items=items))
