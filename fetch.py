"""
Récupère les derniers articles tech depuis les flux RSS définis dans config.py,
filtre par fenêtre temporelle et déduplique.
"""

import re
import time
from datetime import datetime, timezone, timedelta

import feedparser

from config import FEEDS, HOURS_WINDOW, MAX_ARTICLES, MAX_PER_FEED

_IMG_TAG_RE = re.compile(r'<img[^>]+src="([^"]+)"')

# Le CDN de la BBC sert une miniature basse résolution par défaut (souvent 240px de
# large), mais accepte n'importe quelle taille dans l'URL : on demande la plus grande.
_BBC_THUMBNAIL_RE = re.compile(r"(ichef\.bbci\.co\.uk/[^/]+/standard/)\d+(/)")


def _upgrade_bbc_resolution(url):
    return _BBC_THUMBNAIL_RE.sub(r"\g<1>976\g<2>", url)


def _entry_datetime(entry):
    """Récupère la date de publication d'une entrée RSS, ou None si absente."""
    for field in ("published_parsed", "updated_parsed"):
        value = entry.get(field)
        if value:
            return datetime.fromtimestamp(time.mktime(value), tz=timezone.utc)
    return None


def _candidate_images(entry):
    """Liste toutes les images candidates d'une entrée RSS, avec leur largeur si connue."""
    candidates = []

    for media in entry.get("media_content", []):
        if media.get("url") and media.get("medium", "image") == "image":
            candidates.append((int(media.get("width") or 0), media["url"]))

    for thumb in entry.get("media_thumbnail", []):
        if thumb.get("url"):
            candidates.append((int(thumb.get("width") or 0), thumb["url"]))

    for link in entry.get("links", []):
        if link.get("rel") == "enclosure" and link.get("type", "").startswith("image"):
            candidates.append((0, link["href"]))

    for field in ("content", "summary"):
        value = entry.get(field)
        html = value[0].get("value", "") if field == "content" and value else value or ""
        match = _IMG_TAG_RE.search(html)
        if match:
            candidates.append((0, match.group(1)))

    return candidates


def _entry_image(entry):
    """
    Récupère l'URL de l'image en meilleure qualité disponible pour une entrée RSS,
    ou None si le flux n'en fournit pas. On ne fabrique jamais d'URL : pas d'image
    trouvée = pas d'image dans la newsletter. Quand plusieurs résolutions existent
    (miniature vs image pleine taille), on garde toujours la plus grande.
    """
    candidates = _candidate_images(entry)
    if not candidates:
        return None

    candidates.sort(key=lambda c: c[0], reverse=True)
    best_url = candidates[0][1]
    return _upgrade_bbc_resolution(best_url)


def fetch_articles():
    """
    Retourne une liste de dicts : {title, link, summary, source, published}
    triée du plus récent au plus ancien, limitée à MAX_ARTICLES.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_WINDOW)
    seen_links = set()
    articles = []

    for feed in FEEDS:
        feed_articles = []
        parsed = feedparser.parse(feed["url"])
        for entry in parsed.entries:
            link = entry.get("link")
            if not link or link in seen_links:
                continue

            published = _entry_datetime(entry)
            if published and published < cutoff:
                continue

            feed_articles.append({
                "title": entry.get("title", "Sans titre"),
                "link": link,
                "summary": entry.get("summary", ""),
                "source": feed["name"],
                "published": published,
                "image": _entry_image(entry),
            })
            seen_links.add(link)

        # Tri du plus récent au plus ancien avant de ne garder que les MAX_PER_FEED
        # premiers : un flux très prolifique ne doit pas écraser les autres flux.
        feed_articles.sort(key=lambda a: a["published"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        articles.extend(feed_articles[:MAX_PER_FEED])

    # Tri global du plus récent au plus ancien (les articles sans date passent en dernier)
    articles.sort(key=lambda a: a["published"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    return articles[:MAX_ARTICLES]


if __name__ == "__main__":
    # Test rapide : affiche les titres récupérés
    for art in fetch_articles():
        print(f"[{art['source']}] {art['title']}")
