import re
import requests
from bs4 import BeautifulSoup
import random

MAGALU_STORE = "in_603815"

# -------------------
# Legendas prontas
# -------------------
LEGENDAS = [
    "🔥 Aproveite essa oferta incrível!",
    "✨ Promoção imperdível no Magalu!",
    "🛍️ Garanta já o seu com desconto!",
    "💯 Oferta válida por tempo limitado!",
    "🚀 Não perca essa oportunidade!",
    "😍 Olha só esse preço especial!",
    "⚡ Corre antes que acabe!",
]

def gerar_legenda():
    return random.choice(LEGENDAS)

def format_magalu_store(store_id: str) -> str:
    if not store_id.startswith("in_"):
        return store_id[:2] + "_" + store_id[2:]
    return store_id

def encurtar_link(url: str) -> str:
    try:
        resp = requests.post(
            "https://api.encurtador.dev/encurtamentos",
            json={"url": url},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code in (200, 201):
            return resp.json().get("urlEncurtada", url)
    except Exception:
        pass
    return url


def get_magalu_product_info(product_url: str) -> dict:
    try:
        loja_corrigida = format_magalu_store(MAGALU_STORE)

        if "magazinevoce.com.br" in product_url:
            affiliate_link = product_url
        else:
            path = re.sub(r"https?://www\.magazineluiza\.com\.br", "", product_url)
            affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja_corrigida}{path}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "pt-BR,pt;q=0.9",
        }

        resp = requests.get(affiliate_link, headers=headers, timeout=25)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        info = {
            "name": "Produto Magalu",
            "image": None,
            "link": affiliate_link,
            "legend": gerar_legenda(),
            "price_original": None,
            "price_pix": None,
            "pix_discount": None,
            "pix_method": None,
            "card_total": None,
            "card_installments": None,
            "caption": None,
        }

        # -------------------
        # NOME E IMAGEM
        # -------------------
        if (t := soup.find("meta", property="og:title")):
            info["name"] = re.sub(
                r"\s*-\s*(Magazine|Magalu).*",
                "",
                t.get("content", "").strip(),
                flags=re.I,
            )

        if (img := soup.find("meta", property="og:image")):
            info["image"] = img.get("content")

        # -------------------
        # BLOCO DE PREÇO REAL
        # -------------------
        price_default = soup.find("div", {"data-testid": "price-default"})

        if price_default:
            # Preço original riscado
            if (orig := price_default.find("p", {"data-testid": "price-original"})):
                info["price_original"] = orig.get_text(strip=True)

            # Preço Pix (principal)
            if (pix := price_default.find("p", {"data-testid": "price-value"})):
                info["price_pix"] = pix.get_text(" ", strip=True).replace("ou ", "")

            # Texto "no Pix"
            if (pix_m := price_default.find("span", {"data-testid": "in-cash"})):
                info["pix_method"] = pix_m.get_text(strip=True)

            # Desconto Pix
            if (disc := price_default.find("span", class_=re.compile("sc-faUjhM"))):
                info["pix_discount"] = disc.get_text(strip=True)

            # Parcelamento
            if (inst := price_default.find("p", {"data-testid": "installment"})):
                info["card_installments"] = inst.get_text(strip=True)

        # -------------------
        # TOTAL CARTÃO (fallback)
        # -------------------
        if not info["card_total"]:
            if (card := soup.find("div", {"data-testid": "mod-bestinstallment"})):
                valores = card.find_all(string=re.compile(r"R\$\s*\d+[\.,]\d{2}"))
                if valores:
                    info["card_total"] = valores[0].strip()

        # -------------------
        # CAPTION FINAL
        # -------------------
        short_link = encurtar_link(info["link"])
        info["link"] = short_link

        caption = f"📦 {info['name']}\n"

        if info["price_original"] and info["price_pix"]:
            caption += f"💰 De: {info['price_original']} | Por: {info['price_pix']}"
            if info["pix_discount"]:
                caption += f" {info['pix_discount']}"
        elif info["price_pix"]:
            caption += f"💰 {info['price_pix']}"

        if info["card_installments"]:
            caption += f"\n💳 {info['card_installments']}"

        caption += f"\n🔗 {short_link}"

        info["caption"] = caption.strip()

        return info

    except Exception as e:
        print("❌ Erro Magalu:", e)
        return None
