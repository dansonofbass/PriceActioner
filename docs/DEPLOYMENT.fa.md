# انتشار نسخه ساده Redis روی GitHub و Vercel

این نسخه MongoDB یا SQL نمی‌خواهد. روی کامپیوتر، JSON محلی حفظ شده است؛ روی Vercel، Upstash Redis از طریق HTTPS شمارنده سهمیه، ورود ادمین و تاریخچه کوتاه را نگه می‌دارد. Redis همچنان یک سرویس ذخیره‌سازی است، اما تنظیم شبکه Atlas و ساخت collection لازم نیست.

## ۱. فقط یک بار Redis بساز

در https://console.upstash.com حساب بساز و یک Redis database برای priceactioner ایجاد کن. پلن و هزینه/محدودیت آن را قبل از انتخاب بررسی کن. به تنظیمات MongoDB دست نزن؛ این نسخه به آن وصل نمی‌شود و داده Atlas خودکار حذف نمی‌شود.

در صفحه Redis، بخش REST API، این دو مقدار را کپی کن:

- `UPSTASH_REDIS_REST_URL`: آدرس HTTPS، مثلاً `https://YOUR-ENDPOINT.upstash.io`.
- `UPSTASH_REDIS_REST_TOKEN`: توکن استاندارد دارای دسترسی خواندن و نوشتن؛ Read-only Token مناسب نیست.

آدرس `redis://` یا `rediss://` را وارد نکن. توکن را فقط در backend قرار بده. نیازی به بازکردن IP Access List یا انتخاب 0.0.0.0/0 نیست؛ اتصال این برنامه REST روی HTTPS است. [راهنمای رسمی REST API](https://upstash.com/docs/redis/features/restapi).

Eviction را فعال نکن؛ حذف خودکار کلیدها به علت کمبود حافظه می‌تواند شمارنده‌ها و نشست‌ها را از بین ببرد. برنامه خودش برای اطلاعات موقت زمان انقضا دارد.

## ۲. فایل env آماده backend

فایل خصوصی زیر روی همین کامپیوتر آماده شده و رمز ادمین و secret قبلی سرور در آن حفظ شده است:

```text
backend/.env.production
```

فقط دو مقدار Redis در آن خالی‌اند؛ از مرحله ۱ پرشان کن. مقادیر دیگر این شکل‌اند:

```dotenv
APP_ENV=production
STORAGE_BACKEND=redis
PUBLIC_ORIGIN=https://price-actioner.vercel.app
ADMIN_USERNAME=admin
ADMIN_PASSWORD=YOUR_ADMIN_PASSWORD
ADMIN_SECRET_KEY=YOUR_EXISTING_SECRET
JEV_MODE=disabled
UPSTASH_REDIS_REST_URL=https://YOUR-ENDPOINT.upstash.io
UPSTASH_REDIS_REST_TOKEN=YOUR_STANDARD_REST_TOKEN
```

فایل واقعی محلی رمز و secret را دارد؛ نمونه بالا را جایگزین آن نکن. رمز ادمین با توکن Redis فرق دارد. `.env.production` و `.env` را به GitHub نفرست. هیچ‌کدام خودکار از کامپیوتر به تنظیمات Vercel منتقل نمی‌شوند.

## ۳. تغییرات را push کن

در PowerShell ریشه پروژه:

```powershell
cd C:\Users\EliteBook\Desktop\PriceActioner
git add backend frontend docs README.md PROJECT_STATUS.md scripts
git status --short
```

فهرست را نگاه کن: فایل‌های خصوصی `.env`، پوشه `backend/data`، `.venv`، `node_modules`، `.next` و `artifacts` نباید staged باشند. سپس:

```powershell
git commit -m "Replace MongoDB with Redis and add form prompt inspection"
git push origin main
```

مخزن و دو پروژه Vercel فعلی را نگه دار؛ لازم نیست مخزن یا پروژه جدیدی بسازی. اگر auto-deploy قبل از تغییر env اجرا شد، بعد از مرحله بعد دوباره Redeploy کن.

## ۴. تنظیمات پروژه backend در Vercel

پروژه `price-actioner-api` را باز کن. در Settings → Build and Deployment:

| گزینه | مقدار |
|---|---|
| Root Directory | backend |
| Framework Preset | FastAPI |
| Build / Install / Output overrides | خاموش؛ پیش‌فرض |

فایل backend/vercel.json باید این باشد:

```json
{"$schema":"https://openapi.vercel.sh/vercel.json","framework":"fastapi"}
```

در Settings → Environment Variables برای Production:

۱. `MONGODB_URI` و `MONGODB_DATABASE` قدیمی را حذف کن.

۲. `STORAGE_BACKEND` را از mongodb به `redis` تغییر بده.

۳. `UPSTASH_REDIS_REST_URL` و `UPSTASH_REDIS_REST_TOKEN` واقعی را اضافه کن.

۴. سایر مقادیر را از فایل خصوصی `.env.production` وارد کن. PUBLIC_ORIGIN باید دقیقاً `https://price-actioner.vercel.app` و بدون اسلش آخر باشد. secret قبلی را حفظ کن.

۵. آخرین commit را Deploy / Redeploy کن. [پشتیبانی FastAPI در Vercel](https://vercel.com/docs/frameworks/backend/fastapi).

سپس باز کن:

https://price-actioner-api.vercel.app/api/health

انتظار داریم backend و database برابر ONLINE و storage برابر redis باشد. نام database در پاسخ برای سازگاری رابط قبلی مانده و منظور وضعیت Redis است. اگر OFFLINE بود، storage_error را بخوان؛ توکن و REST URL را بررسی کن. نبود Redis دیگر باعث crash در startup نمی‌شود، اما ورود و تحلیل وابسته به سهمیه بدون آن کار نمی‌کنند.

## ۵. تنظیمات پروژه frontend

در پروژه `price-actioner`، Root Directory برابر frontend و Framework برابر Next.js باشد.

در Settings → Environment Variables برای Production:

```dotenv
BACKEND_URL=https://price-actioner-api.vercel.app
NEXT_PUBLIC_SHOW_ADMIN=false
```

BACKEND_URL نباید localhost، دامنه frontend یا آدرس دارای /api باشد. سپس frontend را Redeploy کن؛ متغیر rewrite هنگام build خوانده می‌شود. [متغیرهای محیطی Vercel](https://vercel.com/docs/environment-variables).

اگر backend به جای JSON صفحه ورود Vercel می‌دهد، تنظیمات Deployment Protection و دسترسی سرویس‌به‌سرویس را بررسی کن. از دامنه ثابت Production استفاده کن.

## ۶. تست و استفاده از ادمین

۱. https://price-actioner.vercel.app/api/health باید Redis را ONLINE نشان دهد.

۲. در صفحه اصلی یک فرم ارسال کن: BUY BTC، NOW، 7 DAYS، BALANCED. نتیجه و REQUEST.PREVIEW نمایش داده می‌شود.

۳. از https://price-actioner.vercel.app/admin/login وارد شو. نام admin و رمز همان ADMIN_PASSWORD فایل خصوصی است. Redis تازه ادمین قبلی Atlas را ندارد؛ در اولین ورود، هش ادمین از تنظیمات ساخته می‌شود. بعد از اولین ورود موفق می‌توانی ADMIN_PASSWORD را از env سرور حذف و Redeploy کنی؛ hash در Redis می‌ماند. ADMIN_SECRET_KEY را حذف یا تعویض نکن. تغییر env رمز حساب موجود را reset نمی‌کند.

۴. در HISTORY یک تحلیل را انتخاب کن. FORM.PROMPT این موارد را نشان می‌دهد:

- فرم اولیه کاربر؛
- متن محاسبه‌شده و زمینه بازار؛
- state و questions درخواست؛
- JSON دقیق سریال‌شده برای Jev.

۵. در LOGS دکمه SHOW SELECTED ANALYSIS LOGS فقط رویدادهای تحلیل انتخابی را نمایش می‌دهد؛ با FILTER / REFRESH می‌توانی فیلترهای دیگر را اعمال کنی.

۶. در OVERVIEW و SYSTEM وضعیت ذخیره‌ساز و سیاست نگهداری را ببین. یک Redeploy انجام بده و باقی‌ماندن رکورد تازه و سهمیه همان مرورگر را بررسی کن.

## ۷. نگهداری و محدودیت‌ها

- حداکثر ۱۰۰ تحلیل اخیر و ۲۰۰۰ رویداد اخیر، هرکدام حداکثر ۷ روز. رسیدن به حد تعداد می‌تواند رکورد را زودتر حذف کند.
- نشست ادمین حداکثر ۸ ساعت؛ شمارنده روزانه ۲ روز نگه داشته می‌شود اما سهمیه با کلید روز جدید در نیمه‌شب UTC صفر می‌شود.
- سه تحلیل موفق برای هر مرورگر؛ تغییر مرورگر یا پاک کردن کوکی قابل دور زدن است. این محدودیت هویت واقعی افراد نیست.
- اگر Redis قطع شود، ورود و تحلیل جدید با خطای مشخص رد می‌شوند؛ شمارنده موقت و غیرقابل‌اعتماد جایگزین نمی‌شود. در قطع ارتباط ممکن است لاگ یا بازپرداخت سهمیه شکست‌خورده ثبت نشود؛ crash حین درخواست هم می‌تواند سهمیه رزروشده را تا پایان روز مصرف‌شده باقی بگذارد.
- کلید ادمین و هش رمز تاریخ انقضای خودکار ندارند. این نسخه آرشیو دائمی تحلیل نیست.
- Jev هنوز درخواست زنده نمی‌فرستد؛ FORM.PROMPT پیش‌نویس دقیق تولیدشده را نشان می‌دهد. JEV_API_KEY آینده فقط در backend وارد می‌شود.
- لاگ‌های اجرایی خود Vercel جدا از لاگ‌های داخل برنامه‌اند.

## ۸. اجرای محلی و ارسال ZIP

روی کامپیوتر تنظیم STORAGE_BACKEND=json در backend/.env حفظ شده و به Redis نیاز نیست. حساب محلی و رکوردهای JSON قبلی دست‌نخورده‌اند. برای نصب وابستگی‌های جدید:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

اجرای backend از پوشه backend و frontend طبق README است. برای ساخت ZIP تازه از ریشه:

```powershell
python scripts/make_source_zip.py
```

فایل ZIP در releases ساخته می‌شود و رمزها، فایل env خصوصی، رکوردهای محلی و نصب‌ها داخلش نیستند. پوشه‌های backend، frontend، docs، scripts و فایل‌های README، PROJECT_STATUS و .gitignore باید در سورس باشند. تمام فایل‌های داخل این پوشه‌ها را حفظ کن، به‌جز مواردی که gitignore و اسکریپت ZIP کنار می‌گذارند.

در صورت تمایل به انتقال تاریخچه محلی، URL و توکن Redis را در backend/.env قرار بده؛ upload_records.py ابتدا فقط تعداد را نمایش می‌دهد و فقط با --confirm تحلیل‌ها و لاگ‌ها را منتقل می‌کند. رمز و نشست محلی منتقل نمی‌شوند. محدودیت تعداد و مدت Redis روی رکوردهای واردشده هم اعمال می‌شود.

اتصال واقعی Upstash پس از ارائه دو مقدار خصوصی قابل تست است؛ تست‌های فعلی محلی، شبیه‌ساز Redis با اجرای Lua و بررسی قرارداد REST هستند، نه گواه انتشار موفق در حساب تو.
