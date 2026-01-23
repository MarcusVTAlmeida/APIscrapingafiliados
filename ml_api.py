import re
import json
import requests
from bs4 import BeautifulSoup


def normalize_price(value):
    """
    Recebe '48.9', '48.90', '48,90', '4899' e retorna '48,90'
    """
    if not value:
        return value

    value = value.strip()

    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    else:
        value = value.replace(" ", "")

    try:
        return f"{float(value):.2f}".replace(".", ",")
    except:
        return value


def resolve_url(url: str) -> str:
    """
    Resolve URLs encurtadas (amzn.to, bit.ly, /sec/, etc)
    """
    try:
        resp = requests.get(
            url,
            allow_redirects=True,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
        )
        return resp.url
    except Exception as e:
        print("Erro ao resolver URL:", e)
        return url


def extract_prices_from_affiliate_json(html):
    """
    Extrai preço atual e preço original de páginas afiliadas (/sec/)
    """
    try:
        matches = re.findall(
            r'\{[^{}]*"previous_price"[^{}]*\}',
            html,
            re.DOTALL
        )

        for m in matches:
            try:
                data = json.loads(m)

                prev = data.get("previous_price", {}).get("value")
                curr = data.get("current_price", {}).get("value")

                if curr:
                    price = f"R$ {normalize_price(str(curr))}"
                    original = (
                        f"R$ {normalize_price(str(prev))}"
                        if prev else None
                    )
                    return price, original
            except:
                continue

    except Exception as e:
        print("Erro JSON afiliado:", e)

    return None, None


def get_ml_product_info(product_url, original_url=None):
    """
    original_url: URL que o usuário enviou (encurtada ou não)
    product_url: URL resolvida para scraping
    """
    try:
        # ✅ Resolver URL encurtada
        resolved_url = resolve_url(product_url)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        resp = requests.get(resolved_url, headers=headers, timeout=15)
        resp.raise_for_status()

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # ===============================
        # TÍTULO
        # ===============================
        title_tag = soup.find("meta", property="og:title")
        title = (
            title_tag["content"]
            if title_tag and title_tag.get("content")
            else "Produto Mercado Livre"
        )

        # ===============================
        # IMAGEM
        # ===============================
        image_tag = soup.find("meta", property="og:image")
        image = (
            image_tag["content"]
            if image_tag and image_tag.get("content")
            else None
        )

        # ===============================
        # PREÇOS (CASO /sec/)
        # ===============================
        price = None
        original_value = None

        if "/sec/" in resolved_url:
            price, original_value = extract_prices_from_affiliate_json(html)

        # ===============================
        # PREÇO ATUAL (HTML fallback)
        # ===============================
        if not price:
            price_meta = soup.find("meta", itemprop="price")

            if price_meta and price_meta.get("content"):
                price = f"R$ {normalize_price(price_meta['content'])}"
            else:
                frac = soup.find(
                    "span",
                    class_=re.compile("andes-money-amount__fraction")
                )
                cents = soup.find(
                    "span",
                    class_=re.compile("andes-money-amount__cents")
                )
                if frac:
                    v = frac.text
                    if cents:
                        v += f".{cents.text}"
                    price = f"R$ {normalize_price(v)}"

        # ===============================
        # PREÇO ORIGINAL (HTML fallback)
        # ===============================
        if not original_value:
            original_tag = (
                soup.find("span", class_=re.compile("andes-money-amount--previous"))
                or soup.find("span", class_=re.compile("ui-pdp-price__original-value"))
                or soup.find("s")
            )

            if original_tag:
                txt = original_tag.get_text().strip()
                if txt.startswith("R$"):
                    txt = txt.replace("R$", "").strip()
                original_value = f"R$ {normalize_price(txt)}"

        # ===============================
        # JSON-LD (fallback final)
        # ===============================
        if not original_value:
            ld_tag = soup.find("script", type="application/ld+json")
            if ld_tag and ld_tag.string:
                try:
                    data_ld = json.loads(ld_tag.string)
                    offers = data_ld.get("offers", {})
                    high_price = offers.get("highPrice")
                    if high_price:
                        original_value = f"R$ {normalize_price(str(high_price))}"
                except Exception as e:
                    print("Erro JSON-LD:", e)

        # ✅ Retornar sempre a URL ORIGINAL
        url_para_retornar = original_url if original_url else product_url

        # ===============================
        # CAPTION
        # ===============================
        if original_value and price:
            caption = (
                f"🔥 OFERTA IMPERDÍVEL 🔥\n\n"
                f"{title}\n\n"
                f"De {original_value} por {price}\n\n"
                f"👉 Compre agora:\n{url_para_retornar}"
            )
        else:
            caption = (
                f"🔥 OFERTA IMPERDÍVEL 🔥\n\n"
                f"{title}\n\n"
                f"💰 {price or 'Preço indisponível'}\n\n"
                f"👉 Compre agora:\n{url_para_retornar}"
            )

        return {
            "title": title,
            "price": price,
            "original_value": original_value,
            "url": url_para_retornar,
            "image": image,
            "caption": caption,
        }

    except Exception as e:
        print("Erro ML:", e)
        url_para_retornar = original_url if original_url else product_url
        return {
            "title": "Produto Mercado Livre",
            "price": None,
            "original_value": None,
            "url": url_para_retornar,
            "image": None,
            "caption": "Erro ao obter produto",
        }



# if __name__ == "__main__":
#     # Teste com uma URL válida do Mercado Livre.
#     url = "https://www.mercadolivre.com.br/tomada-inteligente-smart-wi-fi-24-ghz-10a-110v220v-bivolt-branco-cod-291990608-neo-avant/p/MLB37193095#reco_item_pos=2&reco_backend=item_decorator&reco_backend_type=function&reco_client=home_items-decorator-legacy&reco_id=55028c62-c051-4249-a5de-bf2933a8d9da&reco_model=&c_id=/home/second-best-navigation-trend-recommendations/element&c_uid=3bfbc2a8-8cfd-4726-b14a-9537c59e68d0&da_id=second_best_navigation_trend&da_position=2&id_origin=/home/dynamic_access&da_sort_algorithm=ranker"
#     info = get_ml_product_info(url)
#     print(info)
