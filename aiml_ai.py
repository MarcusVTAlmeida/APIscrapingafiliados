import requests
import random

# 🔑 Sua chave AIML API
AIML_API_KEY = "2f2e19b9f82b41f98d33ce4ada84af58"

# ⚙️ Controle: False = legenda fake (teste) | True = AIML API
USE_AIML = False  

def gerar_legenda_divertida(nome, preco, loja):
    """
    Gera uma legenda divertida.
    Se USE_AIML=False, retorna legenda fake sem chamar API.
    """
    if not USE_AIML:
        # 🔹 Legenda fake para não gastar créditos durante os testes
        return f"🛒 {nome} na {loja} por {preco}! Aproveite essa oferta 😍"
    
    # Se USE_AIML=True, usa a API normalmente
    unique_id = random.randint(1000, 9999)  # garante unicidade por produto
    prompt = (
        f"Você é um social media criativo. Crie uma legenda divertida e curta (1-2 frases) "
        f"para um produto de venda online, única para este produto.\n\n"
        f"Produto: {nome}\nPreço: {preco}\nLoja: {loja}\nID: {unique_id}\n\n"
        f"Regras: Use emojis, estilo social media, sem hashtags, leve e engraçado."
    )

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
        print("🔍 DEBUG AIML:", data)

        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            content = None

            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]
            elif "text" in choice:
                content = choice["text"]

            if content:
                return content.strip()

        return f"Não perca este incrível {nome} da {loja}!"

    except Exception as e:
        print("Erro ao gerar legenda com AIML API:", e, response.text if 'response' in locals() else "")
        return f"🔥 Promoção incrível de {nome} esperando por você!"
