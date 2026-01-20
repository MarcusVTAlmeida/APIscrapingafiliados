import re
import json
import requests
from bs4 import BeautifulSoup

def normalize_price(value):
    """
    Recebe '48.9', '48.90', '48,90', '4899' e retorna '48,90'
    """
    if not value:
        return value

    value = value.strip()

    # Se vier no formato brasileiro
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    else:
        # Formato internacional (48.9, 48.90)
        value = value.replace(" ", "")

    try:
        return f"{float(value):.2f}".replace(".", ",")
    except:
        return value


def get_ml_product_info(product_url):
    try:
        original_url = product_url  # 👈 guarda o link como o usuário mandou

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        resp = requests.get(
            product_url,
            headers=headers,
            timeout=15,
            allow_redirects=True
        )
        resp.raise_for_status()

        final_url = resp.url  # 👈 usado só para scraping

        soup = BeautifulSoup(resp.text, "html.parser")

        # TÍTULO
        title_tag = soup.find("meta", property="og:title")
        title = title_tag["content"] if title_tag else "Produto Mercado Livre"

        # IMAGEM
        image_tag = soup.find("meta", property="og:image")
        image = image_tag["content"] if image_tag else None

        # PREÇO
        price = None
        price_meta = soup.find("meta", itemprop="price")
        if price_meta and price_meta.get("content"):
            price = f"R$ {normalize_price(price_meta['content'])}"

        # PREÇO ORIGINAL
        original_value = None
        original_tag = soup.find("span", class_=re.compile("previous"))
        if original_tag:
            txt = original_tag.get_text(strip=True).replace("R$", "")
            original_value = f"R$ {normalize_price(txt)}"

        # LEGENDA
        caption = (
            f"🔥 OFERTA IMPERDÍVEL 🔥\n\n"
            f"{title}\n\n"
            f"{f'De {original_value}\n' if original_value else ''}"
            f"💰 {price or 'Preço indisponível'}\n\n"
            f"👉 Compre agora:\n{original_url}"
        )

        return {
            "title": title,
            "price": price,
            "original_value": original_value,
            "url": original_url,  # ✅ SEMPRE o encurtado
            "image": image,
            "caption": caption,
        }

    except Exception as e:
        print("Erro ML:", e)
        return {
            "error": True,
            "message": "Erro ao obter produto",
            "url": product_url
        }


# if __name__ == "__main__":
#     # Teste com uma URL válida do Mercado Livre.
#     url = "https://www.mercadolivre.com.br/tomada-inteligente-smart-wi-fi-24-ghz-10a-110v220v-bivolt-branco-cod-291990608-neo-avant/p/MLB37193095#reco_item_pos=2&reco_backend=item_decorator&reco_backend_type=function&reco_client=home_items-decorator-legacy&reco_id=55028c62-c051-4249-a5de-bf2933a8d9da&reco_model=&c_id=/home/second-best-navigation-trend-recommendations/element&c_uid=3bfbc2a8-8cfd-4726-b14a-9537c59e68d0&da_id=second_best_navigation_trend&da_position=2&id_origin=/home/dynamic_access&da_sort_algorithm=ranker"
#     info = get_ml_product_info(url)
#     print(info)
