import requests
from bs4 import BeautifulSoup
import json

url = "https://www.magazinevoce.com.br/magazinein_603815/carrinho-para-ferramentas-fechado-6-gavetas-n-08-fercar/p/bdceajbed7/fs/krin/?ads=patrocinado&sellerid=universodosparafusosecommerce"

r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(r.text, "html.parser")

# Pega o JSON do produto
script = soup.find("script", {"type": "application/ld+json"})
data = json.loads(script.text)

nome = data.get("name")
preco = data["offers"].get("price")

print("Nome:", nome)
print("Preço:", preco)
