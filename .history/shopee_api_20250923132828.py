import requests
from bs4 import BeautifulSoup
import json

def get_magalu_info(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Procura os scripts que guardam o JSON
    script = soup.find("script", text=lambda t: t and "__PRELOADED_STATE__" in t)
    if not script:
        script = soup.find("script", type="application/json", id="__NEXT_DATA__")

    if not script:
        print("❌ Não consegui achar os dados do produto.")
        return

    # Extrai o JSON correto
    if "__PRELOADED_STATE__" in script.text:
        data = json.loads(script.text.replace("window.__PRELOADED_STATE__=", ""))
    else:
        data = json.loads(script.text)

    # Tenta pegar dados básicos
    try:
        product = data["product"]["data"]["product"]
        name = product.get("name", "Desconhecido")
        price = product.get("price", {}).get("value", "Desconhecido")
        image = product.get("images", [{}])[0].get("url", "")

        print(f"✅ Nome: {name}")
        print(f"💰 Preço: R$ {price}")
        print(f"🖼️ Imagem: {image}")

    except Exception as e:
        print("⚠️ Estrutura de dados diferente:", e)

# Teste
get_magalu_info("https://www.magazineluiza.com.br/smartphone-samsung-galaxy-a15-128gb-4gb-ram/p/237735900/te/sgal/")
