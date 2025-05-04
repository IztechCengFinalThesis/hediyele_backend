# Hediyele Backend

## Overview

Hediyele, kullanıcıların tercihlerine göre hediye önerileri sunan bir AI destekli öneri sistemidir. Bu repo, Hediyele uygulamasının backend servisini içerir.

## Özellikler

- Basic ve Premium hediye önerileri
- Firebase Authentication ile kullanıcı doğrulama
- Premium üyelik yönetimi (Firebase Custom Claims)
- OpenAI entegrasyonu ile kişiselleştirilmiş öneriler

## Kurulum

### Bağımlılıklar

```bash
pip install -r requirements.txt
```

### Firebase Yapılandırması

1. [Firebase Console](https://console.firebase.google.com/)'dan bir proje oluşturun
2. Authentication > Sign-in method > Email/Password metodunu etkinleştirin
3. Project Settings > Service accounts > Generate new private key
4. İndirilen JSON dosyasını "firebase_admin.json" olarak projenin kök dizinine ekleyin

### .env Dosyası

Proje kök dizininde `config/.env` dosyası oluşturun:

'''
DB_HOST=your_db_host
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_PORT=5432
OPENAI_API_KEY=your_openai_api_key
'''

### Servisi Başlatma

```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Authentication

#### Email/Password Authentication

```http
POST /api/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

#### OAuth2 Token (Swagger için)

```http
POST /api/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password123
```

#### Kullanıcı Durumu Kontrolü

```http
GET /api/user/status
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

### Premium Yönetimi

#### Premium Durumu Ayarlama (Admin)

```http
POST /api/admin/set-premium
Authorization: Bearer ADMIN_FIREBASE_TOKEN
Content-Type: application/json

{
  "user_id": "FIREBASE_USER_ID",
  "is_premium": true
}
```

### Hediye Önerileri

#### Basic Öneri

```http
POST /api/recommendations/basic/
Authorization: Bearer YOUR_FIREBASE_TOKEN
Content-Type: application/json

{
  "age_19_29": true,
  "gender_male": true,
  "special_birthday": true,
  "interest_technology": true
}
```

#### Premium Öneri (Premium kullanıcılar için)

```http
POST /api/recommendations/premium
Authorization: Bearer YOUR_FIREBASE_TOKEN
Content-Type: application/json

{
  "user_input": "35 yaşında teknoloji meraklısı erkek arkadaşım için doğum günü hediyesi arıyorum, bütçem 1000-3000 TL arası"
}
```

## Hediye API Yanıt Formatı

Hediye öneri API'ları şu formatta yanıt döner:

```json
{
  "message": "Öneriler hazır!",
  "filters_used": {
    "age_19_29": true,
    "gender_male": true,
    "special_birthday": true,
    "interest_technology": true
  },
  "recommendations": {
    "products": [
      {
        "id": 4,
        "name": "Acer Aspire 3 15 A315-510P-38X0 Intel Core i3 N305 8GB 256GB SSD",
        "price": 11599.0,
        "site": "HepsiBurada",
        "link": "https://www.hepsiburada.com/acer-aspire-3-intel-core-i3...",
        "score": 45.7
      }
    ]
  }
}
```

## Firebase Authentication Kullanımı

### Token Alma

1. `/api/login` endpoint'ini kullanarak email/password ile giriş yapın
2. Dönen JSON'dan `token` değerini alın
3. Bu token'ı tüm isteklerde Authorization header'ında kullanın:  
   `Authorization: Bearer YOUR_TOKEN`

### Swagger UI ile Test

1. Tarayıcıdan `/docs` adresine gidin
2. Sağ üstteki "Authorize" butonuna tıklayın
3. Email ve şifrenizi girin
4. Artık tüm protected endpoint'leri test edebilirsiniz

## Linkler

- Swagger UI: `http://localhost:8000/docs`
