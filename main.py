"""
Point d'entrée : à lancer une fois par jour (cron / GitHub Actions).

Pipeline : fetch RSS -> résumé Mistral -> rendu HTML (archive) -> envoi Discord (optionnel)
"""

from fetch import fetch_articles
from summarize import generate_newsletter
from render import render_newsletter
from send_discord import send_to_discord


def run():
    print("1/4 — Récupération des articles...")
    articles = fetch_articles()
    print(f"   -> {len(articles)} articles récupérés")

    print("2/4 — Génération du résumé par Mistral...")
    newsletter_md = generate_newsletter(articles)

    print("3/4 — Rendu HTML et archivage...")
    filepath = render_newsletter(newsletter_md, articles=articles)
    print(f"   -> Newsletter sauvegardée : {filepath}")

    print("4/4 — Envoi Discord (si configuré)...")
    send_to_discord(newsletter_md)

    print("Terminé ✅")


if __name__ == "__main__":
    run()
