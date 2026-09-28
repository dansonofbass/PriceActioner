# اجرای موقت فقط frontend؛ بدون backend و Redis

نسخه پیش‌فرض اکنون standalone است. نمودار کندل و حجم BTC/USDT از مرورگر مستقیماً به داده عمومی Binance وصل می‌شود. هیچ درخواست health، usage، login یا analyze به بک‌اند فرستاده نمی‌شود. فرم فقط ورودی را به‌صورت JSON پیش‌نمایش می‌کند. تحلیل Python، ادمین، تاریخچه، سهمیه و Jev در این حالت فعال نیستند؛ کد کامل برای بعد حفظ شده است.

## انتشار همین نسخه

از ریشه پروژه:

```powershell
git add frontend docs/FRONTEND_ONLY.fa.md README.md PROJECT_STATUS.md
git commit -m "Run frontend independently with public BTC chart"
git push origin main
```

در Vercel فقط پروژه frontend با دامنه price-actioner.vercel.app را باز کن:

- Root Directory: frontend
- Framework Preset: Next.js
- Environment Variables / Production: NEXT_PUBLIC_APP_MODE=standalone
- BACKEND_URL را حذف کن؛ در حالت standalone حتی اگر باقی بماند استفاده نمی‌شود.
- آخرین commit را Deploy کن؛ Redeploy روی commit قدیمی این اصلاح را ندارد.

هیچ کلید API، MongoDB یا Redis برای این حالت لازم نیست. پروژه backend لازم نیست Deploy یا حذف شود. به تنظیمات رمزها دست نزن.

## بررسی

صفحه اصلی باید BTC MARKET VIEW و PREVIEW MY FORM نشان دهد، نه شمارنده سهمیه یا Python unavailable. پنج تایم‌فریم و Refresh فعال‌اند. کندل و حجم از Binance دریافت می‌شوند؛ دسترسی مرورگر به data-api.binance.vision لازم است. اگر شبکه کاربر Binance را مسدود کند، خطای همان منبع و دکمه Retry نمایش داده می‌شود؛ داده ساختگی جایگزین نمی‌شود.

در این نسخه /api/health وجود ندارد و معیار تست نیست. صفحه اصلی و نمودار را بررسی کن. /admin و /admin/login صفحه توضیح غیرفعال بودن ادمین دارند و هیچ درخواست ورود ارسال نمی‌کنند.

برای بازگشت آینده به نسخه کامل، NEXT_PUBLIC_APP_MODE=full و BACKEND_URL معتبر لازم است؛ آن زمان backend و Redis باید جداگانه آماده باشند. فعلاً این حالت را فعال نکن.
