def get_shopee_product_info(product_url):
    try:
        item_id = extract_item_id(product_url)
        if not item_id:
            return {"error": "Produto inválido"}

        timestamp = int(time.time())

        # ===============================
        # LINK AFILIADO
        # ===============================
        payload_shortlink = {
            "query": f"""
            mutation {{
                generateShortLink(input: {{
                    originUrl: "{product_url}",
                    subIds: ["s1"]
                }}) {{
                    shortLink
                }}
            }}
            """
        }

        payload_json = json.dumps(payload_shortlink, separators=(",", ":"))
        signature = generate_signature(payload_json, timestamp)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature}",
        }

        response = requests.post(API_URL, data=payload_json, headers=headers, timeout=10)

        try:
            data = response.json()
        except Exception:
            return {"error": "Resposta inválida da Shopee (link afiliado)"}

        short_link = data.get("data", {}).get("generateShortLink", {}).get("shortLink")
        if not short_link:
            return {"error": "Erro ao gerar link afiliado"}

        # ===============================
        # PRODUTO
        # ===============================
        payload_product = {
            "query": f"""
            query {{
                productOfferV2(itemId:{item_id}) {{
                    nodes {{
                        productName
                        priceMin
                        priceMax
                        imageUrl
                    }}
                }}
            }}
            """
        }

        payload_json_product = json.dumps(payload_product, separators=(",", ":"))
        signature_product = generate_signature(payload_json_product, timestamp)

        headers_product = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature_product}",
        }

        response2 = requests.post(API_URL, data=payload_json_product, headers=headers_product, timeout=10)

        try:
            info_data = response2.json()
        except Exception:
            return {"error": "Resposta inválida da Shopee (produto)"}

        nodes = info_data.get("data", {}).get("productOfferV2", {}).get("nodes") or []
        if not nodes:
            return {"error": "Produto sem oferta afiliada"}

        node = nodes[0]

        productname = node.get("productName")
        image_url = node.get("imageUrl")

        min_price = node.get("priceMin")
        max_price = node.get("priceMax")

        price_text = None
        original_value = None

        def safe_price(v):
            try:
                return f"R$ {float(v)/100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except:
                return None

        price_text = safe_price(min_price)
        if max_price and max_price != min_price:
            original_value = safe_price(max_price)

        caption = (
            f"📦 {productname}\n💰 {price_text}\n🔗 {short_link}"
            if not original_value
            else f"📦 {productname}\n💰 De {original_value} por {price_text}\n🔗 {short_link}"
        )

        return {
            "title": productname,
            "price": price_text,
            "original_value": original_value,
            "caption": caption,
            "image": image_url,
            "url": short_link,
        }

    except Exception as e:
        # isso evita o "erro interno" genérico
        return {"error": f"Falha inesperada: {str(e)}"}
