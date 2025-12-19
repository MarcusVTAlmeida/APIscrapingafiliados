import re, requests
from bs4 import BeautifulSoup

def parse_price(price_str):
    """Converte string 'R$ 1.115,10' para float 1115.10"""
    if not price_str:
        return None
    return float(price_str.replace("R$", "").replace(".", "").replace(",", ".").strip())

def format_price(value):
    """Formata float 1115.10 para 'R$ 1.115,10'"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_magalu_product_info(product_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }

        resp = requests.get(product_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Nome do produto
        tag = soup.find("meta", property="og:title")
        name = tag.get("content") if tag else "Produto Magalu"

        # Imagem
        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # Preço atual
        price_current_tag = soup.find("p", {"data-testid": "price-value"})
        price_current = price_current_tag.text.strip() if price_current_tag else None
        price_current_float = parse_price(price_current)

        # Preço antigo (riscado)
        price_old_tag = soup.find("p", {"data-testid": "price-original"})
        price_old = price_old_tag.text.strip() if price_old_tag else None

        # Desconto / forma de pagamento
        discount_tag = soup.find("div", {"data-testid": "tag"})
        discount_text = discount_tag.text.strip() if discount_tag else None

        # Separar percentual e forma de pagamento
        discount_percent = None
        discount_method = None
        if discount_text:
            parts = discount_text.split("OFF")
            discount_percent = parts[0].strip() + "OFF" if len(parts) > 0 else None
            discount_method = parts[1].strip() if len(parts) > 1 else None

        # Se não existir preço antigo mas houver desconto, calcula aproximado
        if not price_old and price_current_float and discount_percent:
            desconto = float(discount_percent.replace("% OFF","").replace(",","."))
            price_old_float = price_current_float / (1 - desconto/100)
            price_old = format_price(price_old_float)

        # Monta o texto final de preço
        if price_current:
            price_text = f"💰 {price_current}"
            if price_old:
                price_text += f" (de {price_old})"
            if discount_percent and discount_method:
                price_text += f" - {discount_percent} {discount_method}"
        else:
            price_text = "Preço indisponível"

        return name, price_text, product_url, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None
