from fastapi import FastAPI
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import traceback

from product_info_router import get_product_info

# ===============================
# FIREBASE INIT (RENDER SAFE)
# ===============================
if not firebase_admin._apps:
    firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")

    if not firebase_json:
        raise Exception("FIREBASE_SERVICE_ACCOUNT não configurado")

    cred_dict = json.loads(firebase_json)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

app = FastAPI()

# ===============================
# MODELS
# ===============================
class ScrapeRequest(BaseModel):
    url: str
    uid: str

# ===============================
# FIRESTORE - CONFIG SHOPEE
# ===============================
def get_user_shopee_config(uid: str):
    try:
        ref = (
            db.collection("users")
            .document(uid)
            .collection("shopee")
            .document("config")
        )

        doc = ref.get()

        if not doc.exists:
            return None, None

        data = doc.to_dict()
        return data.get("app_id"), data.get("secret")

    except Exception as e:
        print("🔥 Erro ao buscar config Shopee:", e)
        traceback.print_exc()
        return None, None

# ===============================
# ENDPOINT
# ===============================
@app.post("/scrape")
def scrape(data: ScrapeRequest):
    if not data.url or not data.uid:
        return {
            "error": True,
            "message": "URL ou UID não informados"
        }

    try:
        url_lower = data.url.lower()

        # 🔐 Shopee precisa de credenciais
        if "shopee" in url_lower:
            app_id, secret = get_user_shopee_config(data.uid)

            if not app_id or not secret:
                return {
                    "error": True,
                    "message": "Configuração Shopee não encontrada"
                }

            return get_product_info(
                url=data.url,
                app_id=app_id,
                secret=secret
            )

        # 🟢 Mercado Livre / Amazon / Magalu
        return get_product_info(url=data.url)

    except Exception as e:
        print("🔥 Erro no scrape:", e)
        traceback.print_exc()
        return {
            "error": True,
            "message": "Erro interno ao processar produto"
        }
