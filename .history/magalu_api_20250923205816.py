import requests
from bs4 import BeautifulSoup

def get_magalu_product_info(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return "❌ Erro ao acessar página Magalu"

    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "Produto Magalu"

    price_tag = soup.find("p", {"class": "price-template__text"})
    price = price_tag.get_text(strip=True) if price_tag else "Preço indisponível"

    img_tag = soup.find("img")
    image = img_tag["src"] if img_tag else ""

    message = (
        f"📦 {title}\n"
        f"💰 {price}\n"
        f"🔗 {url}\n"
    )
    if image:
        message += f"🖼️ {image}"
    return message
