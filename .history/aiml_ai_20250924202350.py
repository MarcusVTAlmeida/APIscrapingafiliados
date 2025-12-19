import requests

# 🔑 Coloque sua chave da AIML API aqui
AIML_API_KEY = "2f2e19b9f82b41f98d33ce4ada84af58"

def gerar_legenda_divertida(nome, preco, loja):
    prompt = f"Crie uma legenda divertida e curta para um produto de venda online. Produto: {nome}, Preço: {preco}, Loja: {loja}. Use emojis, sem hashtags, estilo social media, única para este produto."

    try:
        response = requests.post(
            "https://api.aimlapi.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {AIML_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 120,
                "temperature": 0.9,
                "top_p": 0.9
            }
        )

        data = response.json()
        print("🔍 DEBUG AIML:", data)  # veja exatamente onde está o texto

        # busca o texto retornado
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"].strip()
            elif "text" in choice:
                return choice["text"].strip()

        return "🌟 Oferta imperdível esperando por você!"

    except Exception as e:
        print("Erro ao gerar legenda com AIML API:", e, response.text if 'response' in locals() else "")
        return "🔥 Promoção que vai te surpreender!"
