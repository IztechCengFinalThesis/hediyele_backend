## Geliştirme Bilgileri

### Başlatma
1. Proje kökünde bir .env dosyası oluşturun, ortam değişkenlerine aşağıda "Ortam Değişkenleri" bölümünde örnekler verilmiştir.
2. Projeyi başlatmak için - ```make up```

### Migrasyonlar
1. Migrasyon oluşturmak için (proje make up ile çalışır durumda olmalı) - ```MIGR_NAME=examplename make migration``` burada ```MIGR_NAME``` migrasyon adıdır (Opsiyonel parametre).
2. Migrasyonları uygulamak için (proje make up ile çalışır durumda olmalı) - ```make migrate```

### Testler
Testleri çalıştırmak için (proje make up ile çalışır durumda olmalı) - ```make tests```

### URL'ler:

- DOCS Swagger - ```http://127.0.0.1:8002/docs```
- SAQ görev izleme - ```http://127.0.0.1:8002/saq_monitor```

### Tüm Make Komutları:
- ```make up``` - Projeyi başlatır
- ```make down``` - Projeyi durdurur
- ```make migration``` - Migrasyon oluşturur
- ```make migrate``` - Migrasyonları uygular
- ```make check``` - Kodu lint + testlerle kontrol eder
- ```make logs | C_NAME=examplename make logs``` - Logları gösterir. C_NAME - konteyner adı
- ```make bash | C_NAME=examplename make bash``` - Konteyner konsoluna girer. C_NAME - konteyner adı
- ```make tests``` - Testleri çalıştırır

## Ortam Değişkenleri

### POSTGRES Veritabanı
| Değişken          | Tür  | Açıklama                                                                             | Örnek                          |
|------------------|------|--------------------------------------------------------------------------------------|-------------------------------|
| POSTGRES_USER    | str  | PostgreSQL kullanıcısı                                                               | postgres                      |
| POSTGRES_PASSWORD| str  | Veritabanı şifresi                                                                   | postgres                      |
| POSTGRES_DB      | str  | Veritabanı adı                                                                       | user_example                  |
| POSTGRES_HOST    | str  | host/konteyner adı                                                                   | user_postgis                  |
| POSTGRES_PORT    | int  | port, varsayılan 5432                                                                | 5432                          |
| POSTGRES_ECHO    | bool | Tüm sorguların loglanması için bayrak, yalnızca yerel makinelerde geliştirme sırasında kullanılır | True veya False               |
| POSTGRES_MAX_OVERFLOW| int  | Havuzun maksimum büyüklüğü                                                           | 20                            |
| POSTGRES_POOL_SIZE  | int  | Desteklenen havuz büyüklüğü                                                          | 10                            |

### CORS
| Değişken      | Tür  | Açıklama                                                         | Örnek                                      |
|---------------|------|------------------------------------------------------------------|-------------------------------------------|
| CORS_ORIGINS  | list | Kaynak listesi (istemci adresleri), kaynaklara erişim izni için. "*" sembolü varsa veya belirtilmemişse tüm kaynaklara erişim izinlidir | ["127.0.0.1", "testdomain.com"] veya ["*"]|

### SENTRY Hata İzleme
| Değişken            | Tür | Açıklama                            | Örnek                                                           |
|---------------------|-----|-------------------------------------|-----------------------------------------------------------------|
| SENTRY_DSN          | str | Sentry proje ayarlarından alınan DSN. Hataları izlememek için bu değişken projeye geçirilmeyebilir | ```https://exampledsn.sentry.io/1234567```                      |
| SENTRY_ENVIRONMENT  | str | Proje ortamı                        | dev, test, prod                                                 |

### Redis
| Değişken   | Tür | Açıklama               | Örnek                            |
|------------|-----|------------------------|-----------------------------------|
| REDIS_DSN  | str | Redis'e bağlantı adresi| redis://user_redis veya redis://localhost |
