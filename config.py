"""
Configuration du projet : sources RSS et paramètres généraux.
"""

# Sources RSS tech (tu peux en ajouter/enlever librement)
FEEDS = [
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss"},
    {"name": "Hacker News (top)", "url": "https://hnrss.org/frontpage"},
    {"name": "The Next Web", "url": "https://thenextweb.com/feed"},
    {"name": "Engadget", "url": "https://www.engadget.com/rss.xml"},
    {"name": "NYT Technology", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"},
    {"name": "BBC Technology", "url": "http://feeds.bbci.co.uk/news/technology/rss.xml"},
    {"name": "Ars Technica Policy", "url": "https://feeds.arstechnica.com/arstechnica/tech-policy"},
]

# Fenêtre temporelle : ne garder que les articles publiés dans les X dernières heures
HOURS_WINDOW = 48

# Nombre max d'articles retenus par flux avant sélection finale : évite qu'un flux très
# prolifique (Hacker News, Engadget...) ne monopolise le quota et n'écrase les flux plus
# lents mais plus pertinents (BBC Technology, Ars Technica Policy...)
MAX_PER_FEED = 4

# Nombre max d'articles à envoyer à Mistral pour le résumé (évite un prompt trop long).
# Doit rester >= MAX_PER_FEED x nombre de flux pour que l'équilibrage par flux ci-dessus
# ne soit pas annulé par une troncature finale qui ne connaît que les dates.
MAX_ARTICLES = 40

# Modèle Mistral à utiliser (API gratuite sur console.mistral.ai)
MISTRAL_MODEL = "mistral-large-latest"

# Dossier où sont stockées les newsletters générées (sert de "plateforme" d'archives)
OUTPUT_DIR = "newsletters"

# Webhook Discord (optionnel) — laisser vide si tu ne veux pas l'utiliser
import os
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
