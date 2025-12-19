import requests

# 🔑 Coloque sua chave da AIML API aqui
AIML_API_KEY = "2f2e19b9f82b41f98d33ce4ada84af58"

def gerar_legenda_divertida(nome, preco, loja):
    prompt = f"""
    Crie apenas uma legenda divertida e criativa para um produto.
    - Use no máximo 2 linhas.
    - Estilo social media, leve, com emojis.
    - NÃO use hashtags.
    - NÃO coloque nome do produto ou preço, isso será mostrado depois.
    - Seja curto, chamativo e engraçado.
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
                "max_tokens": 50,
                "temperature": 0.9
            }
        )

        data = response.json()
        print("🔍 DEBUG AIML:", data)

        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]

            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"].strip()

            if "text" in choice:
                return choice["text"].strip()

        return None

    except Exception as e:
        print("Erro ao gerar legenda com AIML API:", e, response.text if 'response' in locals() else "")
        return None
