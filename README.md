# 👑 Royal Agent Tool — Internal Web App

🧰 Cheat sheet سريع لفريق خدمة عملاء **Royal Chaussures** بجانب Meta Business Suite.

## ✨ الميزات (v1.1)
- ⏰ **الشريط العلوي**: أوقات العمل + رقم الهاتف + عطلة الجمعة
- 🚚 **حاسبة التوصيل ZR Express**: 58 ولاية بأسعار دقيقة
- 🏠 **حاسبة تلمسان المحلي**: 13 بلدية (منزل/مكتب)
- 📝 **تسجيل الطلبات**: حفظ في SQLite (دائم) + localStorage (offline)
- ⚡ **بنك الردود السريعة**: 9 ردود مع نسخ بنقرة واحدة + بحث
- ⏱️ **مؤقت وقت الرد** + عداد الطلبات
- 🔐 **لوحة Admin** محمية: `/admin` — عرض، بحث، حذف، تصدير CSV

## 🛠️ التقنيات
- **Backend**: Flask (Python) + SQLite
- **Frontend**: AlpineJS + Tailwind CSS + Clipboard API
- **Auth**: HTTP Basic Auth (`royal` / `chaussures2024`)
- **Deploy**: Render (Web Service)

## 🚀 النشر
```bash
git push origin main
# Render يكتشف render.yaml تلقائياً
```

## 🔑 بيانات الدخول
- **تطبيق agents**: مفتوح (بدون تسجيل دخول)
- **لوحة Admin**: `/admin` — username: `royal` / password: `chaussures2024`
