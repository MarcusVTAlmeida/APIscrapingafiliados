import requests
from bs4 import BeautifulSoup
import json

def get_magalu_info(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    name = price = image = None

    # 1️⃣ Tenta achar JSON do produto
    script = soup.find("script", string=lambda s: s and "__PRELOADED_STATE__" in s)
    if not script:
        script = soup.find("script", {"id": "__NEXT_DATA__"})

    if script:
        try:
            if "__PRELOADED_STATE__" in script.string:
                raw = script.string.replace("window.__PRELOADED_STATE__=", "")
                data = json.loads(raw)
            else:
                data = json.loads(script.string)

            # tenta diferentes caminhos
            product = None
            if "product" in data:
                product = data["product"].get("data", {}).get("product")
            elif "props" in data and "pageProps" in data["props"]:
                product = data["props"]["pageProps"].get("product")

            if product:
                name = product.get("name", name)
                price = product.get("price", {}).get("value", price)
                if "images" in product and product["images"]:
                    image = product["images"][0].get("url", image)

        except Exception as e:
            print("⚠️ Erro ao processar JSON:", e)

    # 2️⃣ Fallback: pega metatags
    if not name:
        tag = soup.find("meta", property="og:title")
        if tag: name = tag.get("content")
    if not image:
        tag = soup.find("meta", property="og:image")
        if tag: image = tag.get("content")
    if not price:
        tag = soup.find("meta", property="product:price:amount")
        if tag: price = tag.get("content")

    return {
        "name": name or "Desconhecido",
        "price": price or "Desconhecido",
        "image": image or ""
    }

# 🔎 Teste com qualquer link Magalu
link = "https://www.magazineluiza.com.br/smartphone-samsung-galaxy-a15-128gb-4gb-ram/p/237735900/te/sgal/"
info = get_magalu_info(link)

print(f"✅ Nome: {info['name']}")
print(f"💰 Preço: R$ {info['price']}")
print(f"🖼️ Imagem: {info['image']}")
