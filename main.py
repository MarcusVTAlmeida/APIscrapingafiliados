from shopee_api import get_shopee_product_info
from amazon_api import get_amazon_product_info
from ml_api import get_ml_product_info
from magalu_api import get_magalu_product_info

def get_product_info(url):
    if "shopee" in url:
        return get_shopee_product_info(url)
    elif "amazon" in url:
        return get_amazon_product_info(url)
    elif "mercadolivre" in url:
        return get_ml_product_info(url)
    elif "magazineluiza" in url or "magalu" in url:
        return get_magalu_product_info(url)
    else:
        return "❌ Loja não suportada"

if __name__ == "__main__":
    link = input("Cole o link do produto: ").strip()
    print(get_product_info(link))
