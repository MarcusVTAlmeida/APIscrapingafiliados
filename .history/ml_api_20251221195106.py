import re, requests
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

        # Nome
        tag = soup.find("meta", property="og:title") or soup.find("title")
        name = tag.get("content") if tag and tag.has_attr("content") else tag.text if tag else "Produto Mercado Livre"

        # Imagem
        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # Preço atual (prioriza o meta itemProp price)
        current_price = "Preço indisponível"
        meta_price = soup.find("meta", attrs={"itemprop": "price"})
        if meta_price and meta_price.get("content"):
            current_price = meta_price["content"].strip()
            current_price = f"R$ {current_price}"
        else:
            # fallback: tenta achar o preço visível
            price_frac = soup.find("span", class_=re.compile("andes-money-amount__fraction"))
            price_cents = soup.find("span", class_=re.compile("andes-money-amount__cents"))
            if price_frac:
                p = price_frac.get_text(strip=True)
                if price_cents:
                    p += "," + price_cents.get_text(strip=True)
                current_price = f"R$ {p}"

        # Preço original (riscado), quando existir
        original_value = None
        original_tag = soup.find("s", class_=re.compile("ui-pdp-price__original-value"))
        if original_tag:
            orig_frac = original_tag.find("span", class_=re.compile("andes-money-amount__fraction"))
            orig_cents = original_tag.find("span", class_=re.compile("andes-money-amount__cents"))
            if orig_frac:
                o = orig_frac.get_text(strip=True)
                if orig_cents:
                    o += "," + orig_cents.get_text(strip=True)
                original_value = f"R$ {o}"

        # Caption (opcional, mas ajuda)
        if original_value and current_price != "Preço indisponível":
            caption = f"🔥 OFERTA IMPERDÍVEL 🔥\n\n{name}\n\nDe {original_value} por {current_price}\n\n👉 Compre agora:\n{product_url}"
        else:
            caption = f"🔥 OFERTA IMPERDÍVEL 🔥\n\n{name}\n\n💰 {current_price}\n\n👉 Compre agora:\n{product_url}"

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