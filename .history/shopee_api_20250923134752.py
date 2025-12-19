import requests
from bs4 import BeautifulSoup
import re

def get_products_from_ml_affiliate(affiliate_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(affiliate_url, headers=headers, timeout=15)
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    products = []

    # Procura por cada produto na listagem
    # ML usa <li> com link <a> para cada produto em social/afiliado
    for item in soup.find_all("li", {"class": re.compile(r"ui-search-layout__item")}):
        link_tag = item.find("a", href=True)
        img_tag = item.find("img", {"class": re.compile(r"ui-search-result-image__element")})
        price_tag = item.find("span", {"class": re.compile(r"price-tag-text")})
        title_tag = item.find("h2", {"class": re.compile(r"ui-search-item__title")})

        link = link_tag["href"] if link_tag else None
        image = img_tag["data-src"] if img_tag and img_tag.has_attr("data-src") else (img_tag["src"] if img_tag else None)
        name = title_tag.text.strip() if title_tag else "Produto ML"
        price = price_tag.text.strip() if price_tag else "Preço indisponível"

        if link:
            products.append({
                "name": name,
                "price": price,
                "image": image,
                "link": link
            })

    return products

# Exemplo de uso
affiliate_link = "https://www.mercadolivre.com.br/social/marcusvinicusalmeida?matt_word=marcusvinicusalmeida&matt_tool=97558468"
produtos = get_products_from_ml_affiliate(affiliate_link)

for p in produtos:
    print(f"📦 {p['name']}")
    print(f"💰 {p['price']}")
    print(f"🖼️ {p['image']}")
    print(f"🔗 {p['link']}\n")
