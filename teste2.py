import requests

AIML_API_KEY = "2f2e19b9f82b41f98d33ce4ada84af58"  # 🔑 substitua pela sua chave da AIML API

url = "https://api.aimlapi.com/v1/chat/completions"

prompt = """
Crie uma legenda divertida e criativa para o seguinte produto:
Nome: Camiseta Tech Pro
Preço: R$ 59,90
Loja: Shopee
Use emojis, humor leve e estilo social media (máx. 2 frases).
"""

payload = {
    "model": "gpt-4",
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "max_tokens": 80,
    "temperature": 0.9
}

headers = {
    "Authorization": f"Bearer {AIML_API_KEY}",
    "Content-Type": "application/json"
}

print("🔄 Enviando requisição...")
response = requests.post(url, json=payload, headers=headers)

print("📥 Status:", response.status_code)
print("📥 Resposta completa:", response.text)

try:
    data = response.json()
    if "choices" in data:
        choice = data["choices"][0]
        if "message" in choice and "content" in choice["message"]:
            legenda = choice["message"]["content"].strip()
            print("\n✅ Legenda gerada:", legenda)
        elif "text" in choice:
            legenda = choice["text"].strip()
            print("\n✅ Legenda gerada:", legenda)
        else:
            print("\n⚠️ Não encontrei legenda no retorno.")
except Exception as e:
    print("❌ Erro ao processar:", e)
