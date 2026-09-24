import os
import json
import requests

API_KEY_SERPER = os.getenv("API_KEY_SERPER")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
QUERY = '"Universidad de La Sabana" OR Unisabana OR "Puente del Común"'
DATA_FILE = "enviados.json"

def cargar_enviados():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return set(json.load(f))
    return set()

def guardar_enviados(enviados):
    with open(DATA_FILE, "w") as f:
        json.dump(list(enviados), f)

def enviar_alerta_telegram(titulo, link):
    mensaje = f"🚨 *Nueva mención de La Sabana* 🚨\n\n*{titulo}*\n\n🔗 [Ver publicación directa]({link})"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def buscar_menciones():
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": API_KEY_SERPER, "Content-Type": "application/json"}
    payload = {"q": QUERY, "num": 10, "gl": "co"}

    enviados = cargar_enviados()
    nuevos = False

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        resultados = response.json().get("organic", [])
        for item in resultados:
            titulo = item.get("title")
            link = item.get("link")
            if link not in enviados:
                print(f"Nueva mención: {titulo}")
                enviar_alerta_telegram(titulo, link)
                enviados.add(link)
                nuevos = True

        if nuevos:
            guardar_enviados(enviados)

if __name__ == "__main__":
    buscar_menciones()
