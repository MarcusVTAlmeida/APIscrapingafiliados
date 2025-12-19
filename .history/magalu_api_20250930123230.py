import re
import requests
from bs4 import BeautifulSoup

MAGALU_STORE = "in_603815"

def format_magalu_store(store_id: str) -> str:
    if not store_id.startswith("in_"):
        return store_id[:2] + "_" + store_id[2:]
    return store_id

def _parse_money_to_float(s: str):
    """Converte 'R$ 1.299,00' -> 1299.00 (float)."""
    if not s:
        return None
    s = re.sub(r"[^\d,\.]", "", s)  # remove tudo que não é número, vírgula ou ponto
    s = s.replace(".", "").replace(",", ".")  # transforma 1.299,00 -> 1299.00
    try:
        return float(s)
    except:
        return None

def _format_money(v: float):
    """Formata float -> 'R$ 1.299,00' (estilo BR)."""
    if v is None:
        return None
    s = f"R$ {v:,.2f}"
    # ajustar separadores para BR (., -> .,)
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def get_magalu_product_info(product_url):
    try:
        loja_corrigida = format_magalu_store(MAGALU_STORE)
        # sempre usar/retornar link afiliado
        if "magazinevoce.com.br" in product_url:
            affiliate_link = product_url
        else:
            path = re.sub(r"https?://www\.magazineluiza\.com\.br", "", product_url)
            affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja_corrigida}{path}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }

        # requests no link afiliado (renderizado no servidor)
        resp = requests.get(affiliate_link, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # -------------------
        # Nome e imagem
        # -------------------
        tag = soup.find("meta", property="og:title")
        name = tag.get("content") if tag else "Produto Magalu"

        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # -------------------
        # PIX: busca robusta dentro do painel pix-panel
        # -------------------
        pix_text = None
        pix_panel = soup.find("div", {"data-testid": "pix-panel"})
        if pix_panel:
            # procura primeiro qualquer tag dentro do painel que contenha 'R$'
            price_elem = None
            for t in pix_panel.find_all(['span', 'p', 'div'], recursive=True):
                txt = t.get_text(" ", strip=True)
                if "R$" in txt:
                    price_elem = t
                    break
            price_pix = price_elem.get_text(" ", strip=True) if price_elem else None
            # remove possíveis prefixos "ou" colados (ex: "ouR$" ou "ou R$")
            if price_pix:
                price_pix = re.sub(r'^\s*ou\s*', '', price_pix, flags=re.I)
                price_pix = price_pix.replace("ou", "", 1) if price_pix.startswith("ouR$") else price_pix
                price_pix = price_pix.strip()

            # desconto (texto contendo 'desconto')
            discount_elem = pix_panel.find(string=re.compile(r"desconto", re.I))
            discount = discount_elem.strip() if discount_elem else None

            # método (in-cash) opcional
            pix_method_tag = pix_panel.find(attrs={"data-testid": "in-cash"})
            pix_method = pix_method_tag.get_text(strip=True) if pix_method_tag else "no Pix"

            if price_pix:
                pix_text = f"{price_pix} ({pix_method})"
                if discount:
                    # formatar "com 10% de desconto" ou similar
                    # se discount já contém "%", mantemos
                    pix_text += f" com {discount}"

        # -------------------
        # CARTÃO: busca total e parcelas dentro do painel mod-bestinstallment (robusto)
        # -------------------
        card_text = None
        card_panel = soup.find("div", {"data-testid": "mod-bestinstallment"})
        if card_panel:
            total_candidate = None
            installment_candidate = None

            # procurar por p/span com R$
            for t in card_panel.find_all(['p', 'span', 'div'], recursive=True):
                txt = t.get_text(" ", strip=True)
                if not txt:
                    continue
                # ignorar rótulos do tipo "Cartão de crédito" ou "sem juros" isoladamente
                if re.search(r"Cartão de crédito", txt, re.I):
                    continue

                # se contém 'R$' e não parece ser parcelas, pode ser total
                if "R$" in txt:
                    # se tem padrão de parcela '3x' antes ou depois -> é parcela
                    if re.search(r"\d+\s*[xX]\s*(?:de\s*)?R\$|\d+\s*[xX]\s*R\$", txt):
                        # parcela (ex: '3xR$ 79,30' ou '3x de R$ 79,30')
                        installment_candidate = txt
                    else:
                        # candidata a valor total (ex: 'R$ 237,90')
                        # preferir pegar primeiros R$ com formato monetário curto
                        if not total_candidate:
                            total_candidate = txt

            # se só tem parcelas, calcular total
            if not total_candidate and installment_candidate:
                # extrair parcelas e valor por parcela
                m = re.search(r"(\d+)\s*[xX]\s*(?:de\s*)?R\$\s*([\d\.,]+)", installment_candidate)
                if not m:
                    # tentar outro formato como '3xR$ 79,30' (sem 'de')
                    m = re.search(r"(\d+)\s*[xX]\s*R\$\s*([\d\.,]+)", installment_candidate)
                if m:
                    parcelas = int(m.group(1))
                    valor_parcela = float(m.group(2).replace(".", "").replace(",", "."))
                    total = parcelas * valor_parcela
                    total_str = _format_money(total)
                    # manter o texto original de parcelas entre parênteses
                    card_text = f"{total_str} ({installment_candidate})"
                else:
                    # não conseguimos parsear, usa o texto bruto das parcelas
                    card_text = installment_candidate
            else:
                # se temos total_candidate, montar com parcelas se existir
                if total_candidate:
                    if installment_candidate:
                        card_text = f"{total_candidate} ({installment_candidate})"
                    else:
                        card_text = total_candidate

        # -------------------
        # Monta o texto final (sem priorizar o cartão)
        # -------------------
        if pix_text and card_text:
            price_text = f"💰 {pix_text} | 💳 {card_text} no cartão"
        elif pix_text:
            price_text = f"💰 {pix_text}"
        elif card_text:
            price_text = f"💳 {card_text} no cartão"
        else:
            price_text = "Preço indisponível"

        return name, price_text, affiliate_link, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None
