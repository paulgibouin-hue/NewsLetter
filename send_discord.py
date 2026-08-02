"""
Envoie la newsletter (ou un extrait) sur un salon Discord via webhook.
Discord limite les messages à 2000 caractères, donc on découpe si besoin.
"""

import requests

from config import DISCORD_WEBHOOK_URL


def send_to_discord(markdown_text, webhook_url=None):
    webhook_url = webhook_url or DISCORD_WEBHOOK_URL
    if not webhook_url:
        print("Aucun webhook Discord configuré, envoi ignoré.")
        return

    chunks = [markdown_text[i:i + 1900] for i in range(0, len(markdown_text), 1900)]
    for chunk in chunks:
        response = requests.post(webhook_url, json={"content": chunk})
        response.raise_for_status()
