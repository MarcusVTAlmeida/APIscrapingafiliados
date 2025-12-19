import requests

# 🔑 Coloque sua chave da AIML API aqui
AIML_API_KEY = "2f2e19b9f82b41f98d33ce4ada84af58"

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
        print("🔍 DEBUG AIML:", data)  # 👈 para ver a estrutura exata

        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]

            # Formato OpenAI-like
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"].strip()

            # Alguns retornam "messages" (lista)
            if "messages" in choice and len(choice["messages"]) > 0:
                return choice["messages"][0].get("content", "").strip()

            # Alguns retornam "text"
            if "text" in choice:
                return choice["text"].strip()

            # Alguns retornam "delta"
            if "delta" in choice and "content" in choice["delta"]:
                return choice["delta"]["content"].strip()

        return None

    except Exception as e:
        print("Erro ao gerar legenda com AIML API:", e, response.text if 'response' in locals() else "")
        return None


# 🔎 Teste rápido
if __name__ == "__main__":
    legenda = gerar_legenda_divertida("Fone Bluetooth", "R$99,90", "Amazon")
    print("🎉 Legenda final:", legenda)
