import re
import json
import requests
from bs4 import BeautifulSoup

def normalize_price(value):
    """
    Recebe '48.9', '4899', '48,90' e retorna '48,90'
    """
    value = value.strip().replace(".", "").replace(",", ".")
    try:
        return f"{float(value):.2f}".replace(".", ",")
    except:
        return value

def get_ml_product_info(product_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        resp = requests.get(product_url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Título
        title_tag = soup.find("meta", property="og:title")
        title = title_tag["content"] if (title_tag and title_tag.get("content")) else "Produto Mercado Livre"

        # Imagem
        image_tag = soup.find("meta", property="og:image")
        image = image_tag["content"] if (image_tag and image_tag.get("content")) else None

        # Preço atual
        price = None
        price_meta = soup.find("meta", itemprop="price")
        if price_meta and price_meta.get("content"):
            price = f"R$ {normalize_price(price_meta['content'])}"
        else:
            frac = soup.find("span", class_=re.compile("andes-money-amount__fraction"))
            cents = soup.find("span", class_=re.compile("andes-money-amount__cents"))
            if frac:
                v = frac.text
                if cents:
                    v += f".{cents.text}"
                price = f"R$ {normalize_price(v)}"

        # Preço original (riscado)
        original_value = None
        original_tag = (
            soup.find("span", class_=re.compile("andes-money-amount--previous"))
            or soup.find("span", class_=re.compile("ui-pdp-price__original-value"))
            or soup.find("s")
        )
        if original_tag:
            txt = original_tag.get_text().strip()
            if txt:
                # Remover eventual duplicata do "R$"
                if txt.startswith("R$"):
                    txt = txt.replace("R$", "").strip()
                original_value = f"R$ {normalize_price(txt)}"

        # Tentativa via JSON-LD (caso o método anterior não encontre)
        if not original_value:
            ld_tag = soup.find("script", type="application/ld+json")
            if ld_tag and ld_tag.string:
                try:
                    data_ld = json.loads(ld_tag.string)
                    offers = data_ld.get("offers", {})
                    high_price = offers.get("highPrice")
                    if high_price:
                        original_value = f"R$ {normalize_price(str(high_price))}"
                except Exception as e_json:
                    print("Erro ao analisar JSON-LD:", e_json)

        # Montagem da legenda utilizando o campo original_value (quando disponível)
        if original_value and price:
            caption = (
                f"🔥 OFERTA IMPERDÍVEL 🔥\n\n"
                f"{title}\n\n"
                f"De {original_value} por {price}\n\n"
                f"👉 Compre agora:\n{product_url}"
            )
        else:
            caption = (
                f"🔥 OFERTA IMPERDÍVEL 🔥\n\n"
                f"{title}\n\n"
                f"💰 {price or 'Preço indisponível'}\n\n"
                f"👉 Compre agora:\n{product_url}"
            )

        return {
            "title": title,
            "price": price,
            "original_value": original_value,
            "url": product_url,
            "image": image,
            "caption": caption,
        }

    except Exception as e:
        print("Erro ML:", e)
        return {
            "title": "Produto Mercado Livre",
            "price": None,
            "original_value": None,
            "url": product_url,
            "image": None,
            "caption": "Erro ao obter produto",
        }

# if __name__ == "__main__":
#     # Teste com uma URL válida do Mercado Livre.
#     url = "https://www.mercadolivre.com.br/tomada-inteligente-smart-wi-fi-24-ghz-10a-110v220v-bivolt-branco-cod-291990608-neo-avant/p/MLB37193095#reco_item_pos=2&reco_backend=item_decorator&reco_backend_type=function&reco_client=home_items-decorator-legacy&reco_id=55028c62-c051-4249-a5de-bf2933a8d9da&reco_model=&c_id=/home/second-best-navigation-trend-recommendations/element&c_uid=3bfbc2a8-8cfd-4726-b14a-9537c59e68d0&da_id=second_best_navigation_trend&da_position=2&id_origin=/home/dynamic_access&da_sort_algorithm=ranker"
#     info = get_ml_product_info(url)
#     print(info)
