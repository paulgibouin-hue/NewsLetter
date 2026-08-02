# Tech Daily — Newsletter tech quotidienne générée par IA

Un agent qui récupère chaque jour les actus tech (via RSS), les fait résumer par Mistral,
et génère une page HTML archivée. Sert de newsletter **et** de mini-plateforme consultable.

## Installation locale

```bash
pip install -r requirements.txt
export MISTRAL_API_KEY="ta-clé-api"
python main.py
```

La clé Mistral s'obtient gratuitement sur [console.mistral.ai](https://console.mistral.ai)
(tier gratuit avec limites de débit, pas de carte bancaire requise).

Le résultat est un fichier `docs/YYYY-MM-DD.html` + un `docs/index.html`
qui liste toutes les newsletters passées (ouvre-le dans un navigateur).

## Personnalisation

- **Sources** : modifie la liste `FEEDS` dans `config.py` (ajoute/enlève des flux RSS).
- **Fenêtre temporelle** : `HOURS_WINDOW` dans `config.py` (24h par défaut).
- **Ton du résumé** : modifie le `SYSTEM_PROMPT` dans `summarize.py`.
- **Discord** : mets ton URL de webhook dans `DISCORD_WEBHOOK_URL` (config.py) ou
  en variable d'environnement `DISCORD_WEBHOOK_URL`.

## Automatisation quotidienne (sans serveur à gérer)

Le workflow `.github/workflows/daily.yml` fait tourner le script chaque jour à 7h UTC
via GitHub Actions, et commit automatiquement la newsletter du jour dans le repo.

Étapes :
1. Pousse ce dossier dans un repo GitHub.
2. Dans **Settings > Secrets and variables > Actions**, ajoute :
   - `MISTRAL_API_KEY`
   - `DISCORD_WEBHOOK_URL` (optionnel)
3. Active GitHub Pages sur le dossier `docs/` si tu veux une vraie petite
   "plateforme" accessible par URL (Settings > Pages > branch `main`, dossier `/docs` —
   c'est l'un des deux seuls choix proposés par GitHub, avec la racine du repo).

Alternative sans GitHub : un simple cron sur ta machine/serveur :
```bash
0 7 * * * cd /chemin/vers/tech-newsletter && python main.py
```

## Évolution vers une vraie plateforme

Les fichiers HTML dans `docs/` sont déjà servables tels quels (GitHub Pages,
Netlify, ou un simple `python -m http.server` dans le dossier). Si tu veux aller plus
loin (recherche full-text, abonnement email, préférences par thème), l'étape suivante
naturelle serait une petite app Flask/FastAPI qui lit ces mêmes fichiers depuis une
base SQLite au lieu du HTML brut — je peux te la construire si tu veux.
