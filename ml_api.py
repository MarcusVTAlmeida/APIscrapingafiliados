import re
import json
import requests
from bs4 import BeautifulSoup

def normalize_price(value):
    """
    Normaliza preços de diferentes formatos para 'R$ X.XXX,XX'
    
    Exemplos:
    - "1745.03" (API/JSON decimal inglês) → "1.745,03"
    - "1.745,03" (formato BR) → "1.745,03"
    - "1745" → "1.745,00"
    - "48.9" (decimal inglês) → "48,90"
    - "48,90" (BR) → "48,90"
    """
    if not value:
        return value

    value = str(value).strip()
    
    # Remove espaços e símbolos de moeda
    value = value.replace("R$", "").replace(" ", "")
    
    # Conta quantos pontos e vírgulas tem
    dot_count = value.count(".")
    comma_count = value.count(",")
    
    # Caso 1: Tem vírgula E ponto → formato brasileiro "1.745,03"
    if comma_count > 0 and dot_count > 0:
        # Remove pontos (milhares) e troca vírgula por ponto
        value = value.replace(".", "").replace(",", ".")
    
    # Caso 2: Só tem vírgula → formato brasileiro "1745,03" ou "48,90"
    elif comma_count > 0:
        value = value.replace(",", ".")
    
    # Caso 3: Só tem ponto → pode ser milhar OU decimal
    elif dot_count > 0:
        # Se tem mais de um ponto, é separador de milhar: "1.745.320"
        if dot_count > 1:
            value = value.replace(".", "")
        else:
            # Um único ponto: verificar posição
            parts = value.split(".")
            
            # Se a parte decimal tem exatamente 2 dígitos → decimal inglês "1745.03"
            if len(parts) == 2 and len(parts[1]) == 2:
                pass  # já está correto (ponto = decimal)
            
            # Se parte decimal tem 3 dígitos → é separador de milhar "1.745"
            elif len(parts) == 2 and len(parts[1]) == 3:
                value = value.replace(".", "")
            
            # Se número muito grande com ponto → provavelmente milhar
            elif len(parts[0]) <= 3:
                pass  # decimal "48.9"
            else:
                value = value.replace(".", "")
    
    # Caso 4: Só números → pode ser centavos "4899" ou inteiro "1745"
    # Vamos assumir que se >= 100, não tem centavos embutidos
    # (se necessário ajustar essa lógica)
    
    try:
        num = float(value)
        
        # Formata com separador de milhares e vírgula decimal (padrão BR)
        formatted = f"{num:,.2f}"
        
        # Troca vírgula (milhar) por ponto e ponto (decimal) por vírgula
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        
        return formatted
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
    usando regex segura (sem json.loads em bloco quebrado)
    """
    try:
        # Preço atual
        curr_match = re.search(
            r'"current_price"\s*:\s*\{[^}]*"value"\s*:\s*([\d.]+)',
            html
        )

        # Preço anterior
        prev_match = re.search(
            r'"previous_price"\s*:\s*\{[^}]*"value"\s*:\s*([\d.]+)',
            html
        )

        curr = curr_match.group(1) if curr_match else None
        prev = prev_match.group(1) if prev_match else None

        if curr:
            price = f"R$ {normalize_price(curr)}"
            original = f"R$ {normalize_price(prev)}" if prev else None
            return price, original

    except Exception as e:
        print("Erro afiliado ML:", e)

    return None, None


def get_ml_product_info(product_url, original_url=None):
    """
    original_url: URL que o usuário enviou (encurtada ou não)
    product_url: URL resolvida para scraping
    """
    try:
        original_url = original_url or product_url
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
        # PREÇOS
        # ===============================
        price = None
        original_value = None

        # ✅ PRIORIDADE TOTAL PARA /sec/
        if "/sec/" in resolved_url:
            price, original_value = extract_prices_from_affiliate_json(html)

        # ===============================
        # PREÇO ATUAL (HTML fallback CORRIGIDO)
        # ===============================
        if not price:
            price_meta = soup.find("meta", itemprop="price")

            if price_meta and price_meta.get("content"):
                price = f"R$ {normalize_price(price_meta['content'])}"
            else:
                current_container = soup.find(
                    "div", class_=re.compile("poly-price__current")
                )

                if current_container:
                    frac = current_container.find(
                        "span", class_=re.compile("andes-money-amount__fraction")
                    )
                    cents = current_container.find(
                        "span", class_=re.compile("andes-money-amount__cents")
                    )

                    if frac:
                        v = frac.text.strip()
                        if cents:
                            v += f".{cents.text.strip()}"
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

        # ===============================
        # CAPTION
        # ===============================
        if original_value and price:
            caption = (
                f"🔥 OFERTA IMPERDÍVEL 🔥\n\n"
                f"{title}\n\n"
                f"De {original_value} por {price}\n\n"
                f"👉 Compre agora:\n{original_url}"
            )
        else:
            caption = (
                f"🔥 OFERTA IMPERDÍVEL 🔥\n\n"
                f"{title}\n\n"
                f"💰 {price or 'Preço indisponível'}\n\n"
                f"👉 Compre agora:\n{original_url}"
            )

        return {
            "title": title,
            "price": price,
            "original_value": original_value,
            "url": original_url,
            "image": image,
            "caption": caption,
        }

    except Exception as e:
        print("Erro ML:", e)
        return {
            "title": "Produto Mercado Livre",
            "price": None,
            "original_value": None,
            "url": original_url or product_url,
            "image": None,
            "caption": "Erro ao obter produto",
        }


if __name__ == "__main__":
    # Testes
    print("Teste 1 (link completo):")
    url1 = "https://www.mercadolivre.com.br/bicicleta-ergometrica-para-spinning-mecanica-roda-de-inercia-18kg-pace6000-odin-fit/p/MLB53188187"
    print(get_ml_product_info(url1))
    
    print("\n\nTeste 2 (link /sec/):")
    url2 = "https://mercadolivre.com/sec/2DeMaJG"
    print(get_ml_product_info(url2))
