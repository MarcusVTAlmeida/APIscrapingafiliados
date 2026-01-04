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
    """
    Retorna dict:
      {
        "title": str,
        "price": "R$ xx,xx" ou None,
        "original_value": "R$ yy,yy" ou None,
        "url": product_url,
        "image": url_img ou None,
        "caption": mensagem formatada
      }
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        resp = requests.get(product_url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # ——————————————————————————————————————————————
        # Nome / Título
        # ——————————————————————————————————————————————
        title = (
            soup.find("meta", property="og:title")["content"]
            if soup.find("meta", property="og:title")
            else "Produto Mercado Livre"
        )

        # ——————————————————————————————————————————————
        # Imagem
        # ——————————————————————————————————————————————
        image = (
            soup.find("meta", property="og:image")["content"]
            if soup.find("meta", property="og:image")
            else None
        )

        # ——————————————————————————————————————————————
        # Preço atual (price)
        # ——————————————————————————————————————————————
        price = None
        # tenta meta price
        price_meta = soup.find("meta", itemprop="price")
        if price_meta and price_meta.get("content"):
            price = f"R$ {normalize_price(price_meta['content'])}"
        else:
            # fallback pelos spans
            frac = soup.find("span", class_=re.compile("andes-money-amount__fraction"))
            cents = soup.find("span", class_=re.compile("andes-money-amount__cents"))
            if frac:
                v = frac.text
                if cents:
                    v += f".{cents.text}"
                price = f"R$ {normalize_price(v)}"

        # ——————————————————————————————————————————————
        # Preço antigo (original_value)
        # ——————————————————————————————————————————————
        original_value = None

        # 1) Seletores “riscado”
        original_tag = (
            soup.find("span", class_=re.compile("andes-money-amount--previous"))  or
            soup.find("span", class_=re.compile("ui-pdp-price__original-value")) or
            soup.find("s")
        )
        if original_tag:
            txt = original_tag.get_text()
            original_value = f"R$ {normalize_price(txt)}"

        # 2) Fallback JSON-LD (alguns PDPS expõem no ld+json)
        if not original_value:
            ld = soup.find("script", type="application/ld+json")
            if ld:
                try:
                    data_ld = json.loads(ld.string or "{}")
                    offers = data_ld.get("offers", {})
                    # highPrice = valor antes do desconto
                    hp = offers.get("highPrice")
                    if hp:
                        original_value = f"R$ {normalize_price(str(hp))}"
                except Exception:
                    pass

        # ——————————————————————————————————————————————
        # Monta legenda
        # ——————————————————————————————————————————————
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
