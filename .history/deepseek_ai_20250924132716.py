import os
import requests

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sua_chave_aqui")

def gerar_legenda_divertida(nome, preco, loja):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Você é um social media criativo, divertido e cheio de humor leve."},
            {"role": "user", "content": f"Crie uma legenda divertida e criativa para produto:\nNome: {nome}\nPreço: {preco}\nLoja: {loja}\nUse emojis, humor leve, até 2 frases."}
        ],
        "max_tokens": 60,
        "temperature": 0.8
    }

    try:
        resp = requests.post(url, headers=headers, json=data)
        resp.raise_for_status()
        resposta = resp.json()

        # DEBUG: imprimir saída completa da API
        print("🔍 Resposta DeepSeek:", resposta)

        # Tenta capturar conteúdo da resposta
        if "choices" in resposta:
            choice = resposta["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"].strip()
            elif "text" in choice:  # fallback se vier no formato "text"
                return choice["text"].strip()

        return None

    except Exception as e:
        print("❌ Erro ao gerar legenda com DeepSeek:", e)
        return None
