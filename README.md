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
