from fastapi import FastAPI
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore
import traceback

from shopee_api import get_shopee_product_info  # ✅ OK

# ===============================
# FIREBASE INIT (SEGURO)
# ===============================
cred = credentials.Certificate("serviceAccount.json")

if not firebase_admin._apps:
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
# ENDPOINT PRINCIPAL
# ===============================
@app.post("/scrape")
def scrape(data: ScrapeRequest):
    if not data.url or not data.uid:
        return {
            "error": True,
            "message": "URL ou UID não informados"
        }

    app_id, secret = get_user_shopee_config(data.uid)

    if not app_id or not secret:
        return {
            "error": True,
            "message": "Configuração Shopee não encontrada para este usuário"
        }

    try:
        result = get_shopee_product_info(
            product_url=data.url,
            app_id=app_id,
            secret=secret
        )

        if not result or not isinstance(result, dict):
            return {
                "error": True,
                "message": "Resposta inválida da Shopee"
            }

        return result

    except Exception as e:
        print("🔥 Erro no scrape:", e)
        traceback.print_exc()

        return {
            "error": True,
            "message": "Erro interno ao processar o produto"
        }
