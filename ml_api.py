import re, requests
from bs4 import BeautifulSoup

def get_ml_product_info(product_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(product_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return "Produto indisponível", "Preço indisponível", product_url, None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Nome
        tag = soup.find("meta", property="og:title") or soup.find("title")
        name = tag.get("content") if tag and tag.has_attr("content") else tag.text if tag else "Produto Mercado Livre"

        # Imagem
        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # Preço
        price = "Preço indisponível"
        price_frac = soup.find("span", class_=re.compile("andes-money-amount__fraction"))
        price_cents = soup.find("span", class_=re.compile("andes-money-amount__cents"))
        if price_frac:
            price = price_frac.get_text(strip=True)
            if price_cents:
                price += "," + price_cents.get_text(strip=True)
            price = f"R$ {price}"

        return name, price, product_url, image
    except Exception as e:
        print("Erro ML:", e)
        return "Produto ML", "Preço indisponível", product_url, None
