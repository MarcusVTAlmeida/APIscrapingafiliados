import re
import requests
from bs4 import BeautifulSoup

# Substitua pelo seu ID de afiliado (exemplo fictício)
AFILIADO_ID = "seu_id_afiliado"

def transformar_link_afiliado(url):
    """
    Recebe um link normal e transforma em link de afiliado.
    """
    # Exemplo Magazine Luiza
    if "magazineluiza.com.br" in url:
        return f"https://www.magazinevoce.com.br/magazine{AFILIADO_ID}/p/{url.split('/p/')[1]}"

    # Exemplo Mercado Livre
    if "mercadolivre.com" in url or "mercadolivre.com.br" in url:
        return f"{url}?matt_tool=123456&pp={AFILIADO_ID}"  # exemplo fictício

    return url  # fallback se não bater em nenhum caso conhecido

def get_magalu_product_info(product_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(product_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return "Produto indisponível", "Preço indisponível", product_url, None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Nome do produto
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Nome não encontrado"

        # Preço à vista (Pix geralmente tem desconto)
        price_tag = soup.find("p", {"data-testid": "price-value"})
        price = price_tag.get_text(strip=True) if price_tag else "Preço não encontrado"

        # Imagem principal
        image_tag = soup.find("img", {"data-testid": "image-selected-thumbnail"})
        image = image_tag["src"] if image_tag else None

        return title, price, product_url, image

    except Exception as e:
        return "Erro", str(e), product_url, None


if __name__ == "__main__":
    link_usuario = "https://www.magazineluiza.com.br/maleta-para-ferramentas-l-boxx-102-compact-professional-bosch/p/686317200/fs/mafe/?seller_id=palaciodasferramentas"

    # Sempre transformar em link de afiliado
    link_afiliado = transformar_link_afiliado(link_usuario)

    titulo, preco, url, imagem = get_magalu_product_info(link_afiliado)

    print("Produto:", titulo)
    print("Preço:", preco)
    print("Link afiliado:", link_afiliado)
    print("Imagem:", imagem)
