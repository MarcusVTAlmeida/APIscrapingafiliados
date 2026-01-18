import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters
)

from product_info_router import get_product_info

TELEGRAM_TOKEN = "7835836746:AAGh264mO96_f7nvkkm2N365fhjk979hydU"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    lojas = ["magazineluiza", "magazinevoce", "shopee", "mercado", "amazon"]
    if not any(l in text.lower() for l in lojas):
        await update.message.reply_text(
            "🚫 Envie um link válido da Shopee, Magalu, Mercado Livre ou Amazon."
        )
        return

    await update.message.reply_text("🔎 Buscando produto...")

    try:
        product = get_product_info(text)
    except Exception as e:
        print("Erro ao buscar produto:", e)
        await update.message.reply_text("⚠️ Erro ao buscar informações do produto.")
        return

    if not product:
        await update.message.reply_text(
            "😕 Não consegui obter as informações do produto."
        )
        return

    try:
        caption = product.get("caption") or "🔥 Oferta imperdível!"
        image = product.get("image")

        if image:
            await update.message.reply_photo(
                photo=image,
                caption=caption
            )
        else:
            await update.message.reply_text(
                caption,
                disable_web_page_preview=False
            )

    except Exception as e:
        print("Erro Telegram:", e)
        await update.message.reply_text(
            "⚠️ Erro ao enviar mensagem."
        )


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

print("🤖 Bot universal iniciado com sucesso!")
app.run_polling()
