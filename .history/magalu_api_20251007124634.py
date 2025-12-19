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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
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
            "caption": None
        }

        # Nome e imagem
        tag_title = soup.find("meta", property="og:title")
        if tag_title:
            info["name"] = tag_title.get("content")

        tag_image = soup.find("meta", property="og:image")
        if tag_image:
            info["image"] = tag_image.get("content")

                # -------------------
        # PREÇO ORIGINAL (riscado)
        # -------------------
        price_default = soup.find("div", {"data-testid": "price-default"})
        if price_default:
            orig_tag = (
                price_default.find("p", {"data-testid": "price-original"})
                or price_default.find("span", {"data-testid": "price-original"})
                or price_default.find("p", {"data-testid": "price-strikethrough"})
                or price_default.find("span", {"data-testid": "price-strikethrough"})
                or price_default.find("p", {"data-testid": "price-before"})
                or price_default.find("span", {"data-testid": "price-before"})
                or price_default.find("s")  # preço riscado puro
                or price_default.find("span", string=re.compile(r"De:\s*R\$"))
            )
            if orig_tag:
                info["price_original"] = orig_tag.get_text(strip=True)

        # Caso ainda não tenha encontrado, busca globalmente por "De: R$"
        if not info["price_original"]:
            riscado = soup.find(string=re.compile(r"De:\s*R\$"))
            if riscado:
                info["price_original"] = riscado.strip()

        # -------------------
        # PIX
        # -------------------
        pix_panel = soup.find("div", {"data-testid": "pix-panel"})
        if pix_panel:
            price_elem = pix_panel.find(lambda tag: tag.name in ['p', 'span'] and 'R$' in tag.get_text())
            if price_elem:
                info["price_pix"] = re.sub(r'^\s*ou\s*', '', price_elem.get_text(" ", strip=True), flags=re.I)

            discount_text = pix_panel.get_text(" ", strip=True)
            match = re.search(r'(\d+\s*%[^R$]{0,40}PIX)', discount_text, re.I)
            if match:
                info["pix_discount"] = match.group(1).strip()
            else:
                perc = re.search(r'(\d+\s*%)', discount_text)
                if perc:
                    info["pix_discount"] = f"{perc.group(1)} de desconto No PIX"

            pix_method_tag = pix_panel.find(attrs={"data-testid": "in-cash"})
            if pix_method_tag:
                info["pix_method"] = pix_method_tag.get_text(strip=True)

           # -------------------
        # CARTÃO
        # -------------------
        card_panel = (
            soup.find("div", {"data-testid": "mod-bestinstallment"})
            or soup.find("div", {"data-testid": "best-installment"})
            or soup.find("div", {"data-testid": "credit-card-panel"})
            or soup.find("div", {"data-testid": "card-panel"})
        )

        if card_panel:
            # Preço total no cartão
            total_price_tag = (
                card_panel.find("p", {"data-testid": "price-value"})
                or card_panel.find("span", {"data-testid": "price-value"})
                or card_panel.find("p", string=re.compile(r"R\$"))
                or card_panel.find("span", string=re.compile(r"R\$"))
            )
            if total_price_tag:
                info["card_total"] = total_price_tag.get_text(strip=True)

            # Parcelamento
            installment_tag = (
                card_panel.find("p", {"data-testid": "installment"})
                or card_panel.find("span", {"data-testid": "installment"})
                or card_panel.find(string=re.compile(r"x R\$"))
            )
            if installment_tag:
                info["card_installments"] = (
                    installment_tag.get_text(strip=True)
                    if hasattr(installment_tag, "get_text")
                    else installment_tag.strip()
                )

        # Se ainda não encontrou, tenta uma busca global
        if not info["card_installments"]:
            global_installment = soup.find(string=re.compile(r"\d+x\s*de\s*R\$"))
            if global_installment:
                info["card_installments"] = global_installment.strip()

        if not info["card_total"]:
            global_total = soup.find(string=re.compile(r"R\$\s*\d+,\d{2}"))
            if global_total:
                info["card_total"] = global_total.strip()
                # -------------------
# CAPTION FINAL
# -------------------
legenda = info["legend"]
nome = info["name"]
preco_de = info["price_original"] or ""
preco_pix = info["price_pix"] or ""
desconto = info["pix_discount"] or ""
preco_cartao = info["card_total"] or ""
parcelas = info["card_installments"] or ""
link = info["link"]

caption = f"{legenda}\n\n📦 {nome}\n"

# Lógica modificada para o preço
if preco_de:  # Tem preço riscado
    caption += f"💰 De: {preco_de} | Por: {preco_pix}"
    if desconto:
        caption += f" | {desconto}"
else:  # Não tem preço riscado
    if preco_pix:
        caption += f"💰 {preco_pix}"
        if desconto:
            caption += f" | {desconto}"

if preco_cartao or parcelas:
    caption += f"\n💳 {preco_cartao} {parcelas}"
caption += f"\n🔗 {link}"

info["caption"] = caption


    except Exception as e:
        print(f"Erro ao processar link da Magalu: {e}")
        return {
            "name": "Produto Magalu",
            "price_text": "Preço indisponível",
            "link": product_url,
            "image": None,
            "legend": "😕 Ops, não consegui ver os detalhes.",
        }


