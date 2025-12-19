from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from product_info_router import get_product_info

TELEGRAM_TOKEN = "7835836746:AAGh264mO96_f7nvkkm2N365fhjk979hydU"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    lojas_suportadas = ["magazineluiza", "magazinevoce", "shopee", "mercadolivre", "mercado-livre", "amazon"]
    if not any(loja in text.lower() for loja in lojas_suportadas):
        await update.message.reply_text("🚫 Envie um link válido da Shopee, Magalu, Mercado Livre ou Amazon.")
        return

    product = await get_product_info(text)

    if not product:
        await update.message.reply_text("😕 Não consegui obter as informações do produto.")
        return

    try:
        # 🧩 Verifica o tipo de retorno
        if isinstance(product, dict):
            caption = product.get("caption", "")
            image = product.get("image")
        else:
            # Shopee, ML ou Amazon já retornam texto formatado pronto
            caption, _, _, image = product

        # 📸 Envia com imagem se disponível
        if image:
            await update.message.reply_photo(photo=image, caption=caption)
        else:
            await update.message.reply_text(caption, disable_web_page_preview=False)

    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
        await update.message.reply_text("⚠️ Ocorreu um erro ao tentar enviar a mensagem.")


# 🚀 Inicialização
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Bot universal com formatação Magalu aprimorada iniciado!")
app.run_polling()
