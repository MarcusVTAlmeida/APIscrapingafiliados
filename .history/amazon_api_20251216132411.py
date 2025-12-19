import requests
from bs4 import BeautifulSoup
import re
import random

# Lista de User-Agents para rotacionar
useragents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    # ... adicione os demais User-Agents que você listou
]

def get_amazon_product_info(product_url):
    headers = {
        "User-Agent": random.choice(useragents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }

    resp = requests.get(product_url, headers=headers, timeout=15)
    print(f"[Amazon] Status code: {resp.status_code}")
    if resp.status_code != 200 or "Robot Check" in resp.text or "CAPTCHA" in resp.text:
        headers["User-Agent"] = random.choice(useragents)
        headers["Referer"] = "https://www.amazon.com.br/"
        resp = requests.get(product_url, headers=headers, timeout=15)
        print(f"[Amazon] Retentativa status: {resp.status_code}")

        if resp.status_code != 200 or "Robot Check" in resp.text:
            return {"caption": "Produto indisponível (bloqueado pela Amazon)", "image": None, "url": product_url}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Título
    title_tag = soup.select_one("span#productTitle")
    title = title_tag.get_text(strip=True) if title_tag else "Título não encontrado"

    # Imagem principal
    img_tag = soup.select_one("img#landingImage, img.a-dynamic-image, img.btf-sub-nav-desktop-product-info-image")
    image = img_tag.get("src") if img_tag else None

    # Preço atual
    price_tag = soup.select_one("span.priceToPay, span.a-price .a-offscreen, span.savingPriceOverride")
    price = price_tag.get_text(strip=True) if price_tag else None

    # Preço antigo (riscado)
    old_price_tag = soup.select_one("span.a-text-price .a-offscreen")
    old_price = old_price_tag.get_text(strip=True) if old_price_tag else None

    # Percentual de desconto
    discount_tag = soup.select_one("span.savingsPercentage, span.savingPriceOverride")
    discount = discount_tag.get_text(strip=True).replace("-", "") if discount_tag else None

    # Parcelas
    installments = []
    rows = soup.select("table#InstallmentCalculatorTableCredit tr.a-text-left")
    for row in rows[1:]:  # Ignora cabeçalho
        cols = row.find_all("td")
        if len(cols) == 2:
            parcelas = cols[0].get_text(strip=True)
            total = cols[1].get_text(strip=True)
            installments.append(f"{parcelas} => {total}")

    # Monta legenda
    caption = f"📦 {title}\n💰 De: {old_price or 'N/A'} | Por: {price or 'N/A'}"
    if discount:
        caption += f" | {discount} de desconto"
    caption += f"\n🔗 {product_url}"
    if installments:
        caption += "\n📅 Parcelas:\n" + "\n".join(installments)

    return {
        "caption": caption,
        "image": image,
        "url": product_url,
        "installments": installments
    }

# Exemplo de uso
url = "https://www.amazon.com.br/MONDIAL-Liquidificador-220V-Easy-Power/dp/B09HHMQ1SG/ref=pd_dp_d_dp_dealz_etdr_d_sccl_1_2/142-5324000-1475666"
info = get_amazon_product_info(url)
print(info["caption"])
print(info["image"])
