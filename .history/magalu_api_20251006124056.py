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

def get_magalu_product_info(product_url):
    """
    Busca informações de um produto no Magazine Luiza e retorna um dicionário estruturado.
    """
    try:
        loja_corrigida = format_magalu_store(MAGALU_STORE)
        
        # Corrige link para afiliado
        if "magazinevoce.com.br" in product_url:
            affiliate_link = product_url
        else:
            path = re.sub(r"https?://www\.magazineluiza\.com\.br", "", product_url)
            affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja_corrigida}{path}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }
        resp = requests.get(affiliate_link, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        product_info = {
            "name": "Produto Magalu",
            "image": None,
            "link": affiliate_link,
            "legend": gerar_legenda(),
            "price_original": None,
            "price_pix": None,
            "pix_discount": None,
            "pix_method": None,
            "card_total": None,
            "card_installments": None
        }

        # Nome e imagem
        tag_title = soup.find("meta", property="og:title")
        if tag_title:
            product_info["name"] = tag_title.get("content")

        tag_image = soup.find("meta", property="og:image")
        if tag_image:
            product_info["image"] = tag_image.get("content")

        # Preço Original (riscado)
        price_default = soup.find("div", {"data-testid": "price-default"})
        if price_default:
            orig_tag = price_default.find("p", {"data-testid": "price-original"})
            if orig_tag:
                product_info["price_original"] = orig_tag.get_text(strip=True)

        # PIX
        pix_panel = soup.find("div", {"data-testid": "pix-panel"})
        if pix_panel:
            price_elem = pix_panel.find(lambda tag: tag.name in ['p', 'span'] and 'R$' in tag.get_text())
            if price_elem:
                price_pix_text = price_elem.get_text(" ", strip=True)
                # Remove "ou" ou textos iniciais para pegar só o preço
                price_pix_text = re.sub(r'^\s*ou\s*', '', price_pix_text, flags=re.I).strip()
                product_info["price_pix"] = price_pix_text

            discount_elem = pix_panel.find(string=re.compile(r"desconto", re.I))
            if discount_elem:
                product_info["pix_discount"] = discount_elem.strip()

            pix_method_tag = pix_panel.find(attrs={"data-testid": "in-cash"})
            if pix_method_tag:
                product_info["pix_method"] = pix_method_tag.get_text(strip=True)

        # CARTÃO
        card_panel = soup.find("div", {"data-testid": "mod-bestinstallment"})
        if card_panel:
            total_price_tag = card_panel.find("p", {"data-testid": "price-value"})
            if total_price_tag:
                product_info["card_total"] = total_price_tag.get_text(strip=True)
                
            installment_tag = card_panel.find("p", {"data-testid": "installment"})
            if installment_tag:
                 product_info["card_installments"] = installment_tag.get_text(strip=True)
        
        return product_info

    except Exception as e:
        print(f"Erro ao processar link da Magalu: {e}")
        return {
            "name": "Produto Magalu",
            "price_text": "Preço indisponível",
            "link": product_url,
            "image": None,
            "legend": "😕 Ops, não consegui ver os detalhes.",
        }
