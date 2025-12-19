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
    """Retorna uma legenda aleatória da lista."""
    return random.choice(LEGENDAS)

def format_magalu_store(store_id: str) -> str:
    """Formata o ID da loja para o padrão 'in_XXXXXX'."""
    if not store_id.startswith("in_"):
        return store_id[:2] + "_" + store_id[2:]
    return store_id

def encurtar_link(url: str) -> str:
    """Encurta o link usando a API gratuita encurtador.dev."""
    try:
        api_url = "https://api.encurtador.dev/encurtamentos"
        headers = {"Content-Type": "application/json"}
        data = {"url": url}

        resp = requests.post(api_url, json=data, headers=headers, timeout=10)

        if resp.status_code in [200, 201]:
            result = resp.json()
            if "urlEncurtada" in result:
                return result["urlEncurtada"]

        print(f"⚠️ Erro ao encurtar link: {resp.status_code} -> {resp.text}")
    except Exception as e:
        print(f"⚠️ Erro ao encurtar link: {e}")

    return url  # fallback: retorna o link original se der erro


def get_magalu_product_info(product_url):
    """Busca informações de um produto no Magazine Luiza e retorna um dicionário estruturado."""
    try:
        loja_corrigida = format_magalu_store(MAGALU_STORE)
        
        # Corrige link para afiliado
        if "magazinevoce.com.br" in product_url:
            affiliate_link = product_url
        else:
            path = re.sub(r"https?://www\.magazineluiza\.com\.br", "", product_url)
            affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja_corrigida}{path}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }
        resp = requests.get(affiliate_link, headers=headers, timeout=15)
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
        }

        # -------------------
        # NOME E IMAGEM
        # -------------------
        tag_title = soup.find("meta", property="og:title")
        if tag_title:
            name = tag_title.get("content", "").strip()
            # limpa o final "- Magazine In_603815"
            name = re.sub(r"\s*-\s*Magazine\s+\w+_\d+", "", name, flags=re.I)
            name = re.sub(r"\s*-\s*Magalu.*", "", name, flags=re.I)
            info["name"] = name.strip()

        tag_image = soup.find("meta", property="og:image")
        if tag_image:
            info["image"] = tag_image.get("content")

        # -------------------
        # PREÇOS
        # -------------------
        price_default = soup.find("div", {"data-testid": "price-default"})
        if price_default:
            orig_tag = (
                price_default.find("p", {"data-testid": "price-original"})
                or price_default.find("span", {"data-testid": "price-original"})
                or price_default.find("s")
            )
            if orig_tag:
                info["price_original"] = orig_tag.get_text(strip=True)

        pix_panel = soup.find("div", {"data-testid": "pix-panel"})
        if pix_panel:
            price_elem = pix_panel.find(lambda t: t.name in ["p", "span"] and "R$" in t.get_text())
            if price_elem:
                info["price_pix"] = re.sub(r"^\s*ou\s*", "", price_elem.get_text(" ", strip=True), flags=re.I)
            discount_text = pix_panel.get_text(" ", strip=True)
            perc = re.search(r"(\d+\s*%)", discount_text)
            if perc:
                info["pix_discount"] = f"{perc.group(1)} de desconto no PIX"

        card_panel = (
            soup.find("div", {"data-testid": "mod-bestinstallment"})
            or soup.find("div", {"data-testid": "best-installment"})
            or soup.find("div", {"data-testid": "credit-card-panel"})
        )
        if card_panel:
            total = card_panel.find(string=re.compile(r"R\$"))
            parc = card_panel.find(string=re.compile(r"\d+x"))
            if total:
                info["card_total"] = total.strip()
            if parc:
                info["card_installments"] = parc.strip()

        # -------------------
        # MONTA MENSAGEM FORMATADA
        # -------------------
        short_link = encurtar_link(info["link"])
        legenda = info["legend"]
        caption = f"{legenda}\n\n📦 {info['name']}"

        if info["price_pix"]:
            if info["price_original"]:
                caption += f"\n💰 De: {info['price_original']} | Por: {info['price_pix']}"
            else:
                caption += f"\n💰 {info['price_pix']}"
            if info["pix_discount"]:
                caption += f" | {info['pix_discount']}"

        if info["card_total"] or info["card_installments"]:
            caption += f"\n💳 {info['card_total'] or ''} ({info['card_installments'] or ''}) no cartão".strip()

        caption += f"\n🔗 {short_link}"

        info["caption"] = caption.strip()
        info["link"] = short_link
        return info

    except Exception as e:
        print(f"Erro ao processar link da Magalu: {e}")
        return None
