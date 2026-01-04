import re
import requests
from bs4 import BeautifulSoup

def get_ml_product_info(product_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(product_url, headers=headers, timeout=15)

        if resp.status_code != 200:
            return {
                "title": "Produto indisponível",
                "price": "Preço indisponível",
                "original_value": None,
                "url": product_url,
                "image": None,
                "caption": "Produto indisponível",
            }

        soup = BeautifulSoup(resp.text, "html.parser")

        # =========================
        # NOME
        # =========================
        tag = soup.find("meta", property="og:title") or soup.find("title")
        name = (
            tag.get("content")
            if tag and tag.has_attr("content")
            else tag.text if tag else "Produto Mercado Livre"
        )

        # =========================
        # IMAGEM
        # =========================
        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # =========================
        # PREÇO ATUAL
        # =========================
        current_price = "Preço indisponível"

        meta_price = soup.find("meta", attrs={"itemprop": "price"})
        if meta_price and meta_price.get("content"):
            current_price = f"R$ {meta_price['content'].strip()}"
        else:
            price_frac = soup.find("span", class_=re.compile("andes-money-amount__fraction"))
            price_cents = soup.find("span", class_=re.compile("andes-money-amount__cents"))

            if price_frac:
                p = price_frac.get_text(strip=True)
                if price_cents:
                    p += "," + price_cents.get_text(strip=True)
                current_price = f"R$ {p}"

        # =========================
        # PREÇO ORIGINAL (RISCADO)
        # =========================
        original_value = None

        # tenta container oficial
        original_container = soup.find(
            "span", class_=re.compile("ui-pdp-price__original-value")
        )

        # fallback: qualquer <s>
        if not original_container:
            original_container = soup.find("s")

        if original_container:
            orig_frac = original_container.find(
                "span", class_=re.compile("andes-money-amount__fraction")
            )
            orig_cents = original_container.find(
                "span", class_=re.compile("andes-money-amount__cents")
            )

            if orig_frac:
                o = orig_frac.get_text(strip=True)
                if orig_cents:
                    o += "," + orig_cents.get_text(strip=True)
                original_value = f"R$ {o}"

        # =========================
        # CAPTION
        # =========================
        if original_value and current_price != "Preço indisponível":
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
                f"💰 {current_price}\n\n"
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
            "title": "Produto ML",
            "price": "Preço indisponível",
            "original_value": None,
            "url": product_url,
            "image": None,
            "caption": "Preço indisponível",
        }
