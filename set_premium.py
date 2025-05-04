# set_premium.py
import firebase_admin
from firebase_admin import credentials, auth

# Firebase kimlik bilgilerini yükle
cred = credentials.Certificate("firebase_admin.json")
firebase_admin.initialize_app(cred)

def set_premium(uid, is_premium=True):
    # Mevcut custom claims'i al
    user = auth.get_user(uid)
    custom_claims = user.custom_claims or {}
    
    # Premium özelliğini ekle/güncelle
    custom_claims['admin'] = is_premium
    
    # Custom claims'i kaydet
    auth.set_custom_user_claims(uid, custom_claims)
    print(f"User {uid} premium status set to {is_premium}")

# Kullanım:
user_id = "RlX67akH2FQZavtjEamc4ZDehng2"  # Değiştirin
set_premium(user_id, True)