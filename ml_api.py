import re
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

        if resp.status_code != 200:
            raise Exception("Status code inválido")

        soup = BeautifulSoup(resp.text, "html.parser")

        # =========================
        # NOME
        # =========================
        name = (
            soup.find("meta", property="og:title")["content"]
            if soup.find("meta", property="og:title")
            else "Produto Mercado Livre"
        )

        # =========================
        # IMAGEM
        # =========================
        image = (
            soup.find("meta", property="og:image")["content"]
            if soup.find("meta", property="og:image")
            else None
        )

        # =========================
        # PREÇO ATUAL
        # =========================
        current_price = None

        price_meta = soup.find("meta", itemprop="price")
        if price_meta and price_meta.get("content"):
            current_price = f"R$ {normalize_price(price_meta['content'])}"
        else:
            frac = soup.find("span", class_=re.compile("andes-money-amount__fraction"))
            cents = soup.find("span", class_=re.compile("andes-money-amount__cents"))

            if frac:
                value = frac.text
                if cents:
                    value += f".{cents.text}"
                current_price = f"R$ {normalize_price(value)}"

        # =========================
        # PREÇO ORIGINAL (RISCADO)
        # =========================
        original_value = None

        original_tag = (
            soup.find("span", class_=re.compile("andes-money-amount--previous"))
            or soup.find("span", class_=re.compile("ui-pdp-price__original-value"))
            or soup.find("s")
        )

        if original_tag:
            frac = original_tag.find("span", class_=re.compile("andes-money-amount__fraction"))
            cents = original_tag.find("span", class_=re.compile("andes-money-amount__cents"))

            if frac:
                value = frac.text
                if cents:
                    value += f".{cents.text}"
                original_value = f"R$ {normalize_price(value)}"

        # =========================
        # CAPTION
        # =========================
        if original_value and current_price:
            caption = (
                f"🔥 OFERTA IMPERDÍVEL 🔥\n\n"
                f"{name}\n\n"
                f"De {original_value} por {current_price}\n\n"
                f"👉 Compre agora:\n{product_url}"
            )
        else:
            caption = (
                f"🔥 OFERTA IMPERDÍVEL 🔥\n\n"
                f"{name}\n\n"
                f"💰 {current_price or 'Preço indisponível'}\n\n"
                f"👉 Compre agora:\n{product_url}"
            )

        return {
            "title": name,
            "price": current_price,
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
