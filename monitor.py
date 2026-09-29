import os
import json
import requests

# 1. Configuración de credenciales
API_KEY_SERPER = os.getenv("API_KEY_SERPER")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 2. Configuración de búsqueda ampliada
QUERY = '"Universidad de La Sabana" OR Unisabana OR "Puente del Común"'
DATA_FILE = "enviados.json"

def cargar_enviados():
    """Carga el historial usando un set (conjunto) para búsquedas ultra rápidas."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                # Convertimos a set() para que buscar si un enlace ya existe sea O(1)
                return set(json.load(f))
        except json.JSONDecodeError:
            return set() # Evita que el programa falle si el archivo se corrompe
    return set()

def guardar_enviados(enviados):
    """Guarda el set convertido nuevamente a lista."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(enviados), f, indent=4)

def enviar_alerta_telegram(titulo, link):
    """Envía el mensaje manejando posibles caídas de la red."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    mensaje = f"🔔 *Nueva mención detectada*\n\n📌 *{titulo}*\n🔗 {link}"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        # Se añade un timeout para evitar que el script se quede colgado
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error al enviar a Telegram: {e}")

def buscar_menciones():
    """Consulta la API abarcando todas las categorías posibles de Google."""
    url = "https://google.serper.dev/search"
    # Se optimiza añadiendo país (Colombia = 'co') e idioma (Español = 'es')
    payload = json.dumps({
        "q": QUERY, 
        "hl": "es", 
        "gl": "co"
    }) 
    headers = {
        'X-API-KEY': API_KEY_SERPER,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error al consultar Serper: {e}")
        return []

    links_encontrados = []
    
    # Aplicando el principio DRY (Don't Repeat Yourself)
    # Iteramos sobre todas las secciones posibles en lugar de repetir código
    secciones_google = ["organic", "news", "videos", "places", "topStories", "knowledgeGraph"]
    
    for seccion in secciones_google:
        for item in data.get(seccion, []):
            link = item.get("link")
            titulo = item.get("title", "Mención sin título")
            
            if link:
                links_encontrados.append((titulo, link))
                
    return links_encontrados

def main():
    print("Iniciando monitoreo omnicanal...")
    enviados = cargar_enviados()
    nuevos_resultados = buscar_menciones()
    
    nuevos_enviados_count = 0
    
    for titulo, link in nuevos_resultados:
        if link not in enviados:
            enviar_alerta_telegram(titulo, link)
            enviados.add(link)
            nuevos_enviados_count += 1
            
    if nuevos_enviados_count > 0:
        guardar_enviados(enviados)
        print(f"✅ Se enviaron {nuevos_enviados_count} alertas nuevas a Telegram.")
    else:
        print("💤 No se encontraron menciones nuevas en esta ejecución.")

if __name__ == "__main__":
    main()
