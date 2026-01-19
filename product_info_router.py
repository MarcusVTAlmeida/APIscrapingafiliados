from shopee_api import get_shopee_product_info
from ml_api import get_ml_product_info


def get_product_info(
    url: str,
    app_id: str | None = None,
    secret: str | None = None
):
    url_lower = url.lower()

    # ===============================
    # SHOPEE
    # ===============================
    if "shopee" in url_lower:
        if not app_id or not secret:
            return {
                "error": True,
                "message": "Configuração Shopee não encontrada"
            }

        return get_shopee_product_info(
            product_url=url,
            app_id=app_id,
            secret=secret
        )

    # ===============================
    # MERCADO LIVRE
    # ===============================
    if "mercadolivre" in url_lower or "mercado" in url_lower:
        return get_ml_product_info(url)

    return {
        "error": True,
        "message": "Loja não suportada"
    }
