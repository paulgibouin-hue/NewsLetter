"""
Envoie les articles récupérés à Mistral pour générer un résumé structuré
de type newsletter (introduction + points clés par article + pourquoi ça compte).
"""

import os
import time

from mistralai import Mistral
from mistralai.models import SDKError

from config import MISTRAL_MODEL

# Codes d'erreur transitoires côté Mistral (surcharge temporaire, rate limit) :
# on retente avec un backoff plutôt que de laisser toute la newsletter échouer
# pour un aléa d'une seconde. Les autres erreurs (clé invalide, modèle non
# autorisé, requête malformée...) ne sont pas transitoires : on les laisse
# remonter immédiatement.
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_BACKOFF_SECONDS = 5

SYSTEM_PROMPT = """Tu es un rédacteur tech qui prépare une newsletter quotidienne concise.
À partir d'une liste d'articles (titre, source, lien, résumé brut), génère une newsletter
en Markdown avec cette structure :

# Tech Daily — [date]

## En bref
Un court paragraphe (3-4 phrases) qui résume les grandes tendances du jour.

## Les actus à retenir
Pour chaque article important (regroupe les doublons/sujets similaires), donne :
- Un titre accrocheur (pas juste recopié)
- 2-3 phrases de résumé clair, en français, qui expliquent ce qu'il s'est passé et pourquoi c'est important
- Le lien source en Markdown

Priorité éditoriale (important), dans cet ordre :
1. Les grandes entreprises tech américaines (Apple, Microsoft, Google/Alphabet, Meta,
   Amazon, Nvidia, OpenAI, xAI, Tesla, etc.) : résultats financiers, valorisation,
   dirigeants, rivalités entre elles.
2. Tout ce qui relie ces entreprises à la géopolitique et au pouvoir : décisions de
   l'administration américaine (Maison-Blanche, FCC, Congrès), régulation étrangère qui
   les vise (UE, Chine, Russie), procès et enquêtes antitrust, tensions commerciales,
   export de puces/technologies, rapports avec des gouvernements étrangers, dirigeants
   de ces entreprises convoqués ou sanctionnés par un État.
3. Les autres actus tech significatives, seulement si les catégories 1 et 2 ne
   suffisent pas à remplir la newsletter.

Ignore en priorité le remplissage : bons plans/promos, listicles produits
("meilleurs X de 2026"), tutoriels, projets de niche (nouveaux langages de programmation,
Show HN obscurs), et actualités sans rapport avec la tech.

Ne garde que les 8-12 articles les plus significatifs selon cette priorité.
Ton : informatif, direct, un peu incisif, pas de blabla marketing.
Format : aucun emoji, ni dans les titres ni dans le texte.
"""


def generate_newsletter(articles, api_key=None):
    """
    articles : liste de dicts issus de fetch.fetch_articles()
    Retourne le texte Markdown de la newsletter généré par Mistral.
    """
    client = Mistral(api_key=api_key or os.environ.get("MISTRAL_API_KEY"))

    articles_text = "\n\n".join(
        f"- Titre: {a['title']}\n  Source: {a['source']}\n  Lien: {a['link']}\n  Résumé brut: {a['summary'][:400]}"
        for a in articles
    )

    if not articles_text.strip():
        return "# Tech Daily\n\nAucun article récupéré aujourd'hui — vérifie les flux RSS."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Voici les articles du jour :\n\n{articles_text}"},
    ]

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.chat.complete(model=MISTRAL_MODEL, messages=messages)
            return response.choices[0].message.content
        except SDKError as e:
            status = getattr(e, "status_code", None)
            if status not in _RETRYABLE_STATUS_CODES or attempt == _MAX_RETRIES:
                raise
            wait = _BACKOFF_SECONDS * attempt
            print(f"Erreur Mistral {status} (tentative {attempt}/{_MAX_RETRIES}), "
                  f"nouvelle tentative dans {wait}s...")
            time.sleep(wait)
