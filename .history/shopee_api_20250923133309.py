import re
import requests
from bs4 import BeautifulSoup
import json

def get_magalu_info(url):
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/"
}
    resp = requests.get(url, headers=headers, timeout=10)
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
link = "https://www.magazineluiza.com.br/guarda-roupa-casal-com-espelho-6-portas-6-gavetas-moveis-europa-ripado-potente/p/237735900/mo/guro/"
info = get_magalu_info(link)

print(f"✅ Nome: {info['name']}")
print(f"💰 Preço: R$ {info['price']}")
print(f"🖼️ Imagem: {info['image']}")
