import requests

# 🔑 Coloque sua chave da AIML API aqui
AIML_API_KEY = "2f2e19b9f82b41f98d33ce4ada84af58"

def gerar_legenda_divertida(nome, preco, loja):
    prompt = f"""
    Você é um social media criativo. Crie uma legenda divertida e única para um post de venda de produto.
    
    Produto: {nome}
    Preço: {preco}
    Loja: {loja}
    
    Regras:
    - A legenda deve ter no máximo 2 frases.
    - Deve ser diferente para cada produto, sem repetir textos genéricos.
    - Pode usar emojis, mas sem hashtags.
    - Estilo leve, engraçado e que desperte interesse de compra.
    - NÃO inclua o nome do produto, preço ou link na legenda (isso será adicionado depois).
    """

    try:
        response = requests.post(
            "https://api.aimlapi.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {AIML_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 60,
                "temperature": 0.95,  # mais criatividade
                "top_p": 0.9
            }
        )

        data = response.json()
        print("🔍 DEBUG AIML:", data)

        if "choices" in data and len(data["choices"]) > 0:
            content = None

            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]
            elif "messages" in choice and len(choice["messages"]) > 0:
                content = choice["messages"][0].get("content")
            elif "text" in choice:
                content = choice["text"]
            elif "delta" in choice and "content" in choice["delta"]:
                content = choice["delta"]["content"]

            if content:
                return content.strip()

        return "🌟 Oferta imperdível esperando por você!"

    except Exception as e:
        print("Erro ao gerar legenda com AIML API:", e, response.text if 'response' in locals() else "")
        return "🔥 Promoção que vai te surpreender!"

