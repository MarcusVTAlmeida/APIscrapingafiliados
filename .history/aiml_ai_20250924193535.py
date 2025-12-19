import requests

# 🔑 Coloque sua chave da AIML API aqui
AIML_API_KEY = "SUA_CHAVE_AIMLAPI_AQUI"

def gerar_legenda_divertida(nome, preco, loja):
    prompt = f"""
    Crie uma legenda divertida e criativa para o seguinte produto:
    Nome: {nome}
    Preço: {preco}
    Loja: {loja}
    Use emojis, humor leve e estilo social media (máx. 2 frases).
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
                "max_tokens": 80,
                "temperature": 0.9
            }
        )

        data = response.json()
        # ⚠️ A resposta vem nesse caminho:
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("Erro ao gerar legenda com AIML API:", e, response.text if 'response' in locals() else "")
        return None
