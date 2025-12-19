import re
import requests
from bs4 import BeautifulSoup
import json

def get_magalu_info(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    name = price = image = None

    # Nome do produto
    tag = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
    if tag:
        name = tag.get("content")

    # Imagem do produto
    tag = soup.find("meta", property="og:image")
    if tag:
        image = tag.get("content")

    # Preço com regex no HTML
    match = re.search(r'"price":\s*"?([\d,\.]+)"?', resp.text)
    if match:
        price = match.group(1).replace(".", "").replace(",", ".")

    return {
        "name": name or "Desconhecido",
        "price": price or "Desconhecido",
        "image": image or ""
    }

# 🔎 Teste com link Magalu
link = "https://www.magazineluiza.com.br/smartphone-samsung-galaxy-a15-128gb-4gb-ram/p/237735900/te/sgal/"
info = get_magalu_info(link)

print(f"✅ Nome: {info['name']}")
print(f"💰 Preço: R$ {info['price']}")
print(f"🖼️ Imagem: {info['image']}")
