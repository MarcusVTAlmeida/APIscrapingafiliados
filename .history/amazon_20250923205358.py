import requests
from bs4 import BeautifulSoup

def get_amazon_product_info(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("❌ Erro ao acessar a página")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Nome do produto
    title = soup.find("span", {"id": "productTitle"})
    title = title.get_text(strip=True) if title else "Produto Amazon"

    # Preço
    price = None
    selectors = ["priceblock_ourprice", "priceblock_dealprice", "priceblock_saleprice"]
    for sel in selectors:
        elem = soup.find("span", {"id": sel})
        if elem:
            price = elem.get_text(strip=True)
            break
    if not price:
        price = "Preço indisponível"

    # Imagem
    image = None
    img_tag = soup.find("img", {"id": "landingImage"})
    if img_tag and img_tag.get("src"):
        image = img_tag["src"]

    # Mensagem final para WhatsApp/Telegram
    message = (
        f"📦 {title}\n"
        f"💰 {price}\n"
        f"🔗 {url}\n"
    )
    if image:
        message += f"🖼️ {image}"

    return message


if __name__ == "__main__":
    link = "https://www.amazon.com.br?&linkCode=ll2&tag=marcusvtalmei-20&linkId=98173d148d26f37fc15e31e6e7bea258&language=pt_BR&ref_=as_li_ss_tl"
    result = get_amazon_product_info(link)
    print(result)
