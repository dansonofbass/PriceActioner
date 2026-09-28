# راهنمای صفر تا صد PRICEACTIONER: GitHub و Vercel

نسخه فعلی SQL ندارد: روی کامپیوتر رکوردها JSON هستند و روی سرور در MongoDB Atlas، یک سرویس NoSQL، ذخیره می‌شوند. فایل SQL، ساخت جدول یا اجرای دستور SQL لازم نیست. حساب GitHub، Vercel و Atlas را خودت ایجاد می‌کنی؛ هنوز هیچ انتشار خارجی از طرف تو انجام نشده است.

## ۱. معماری و فایل‌های لازم

یک مخزن GitHub و دو پروژه Vercel خواهی داشت:

```text
GitHub: priceactioner
  ├── Vercel: priceactioner-web / Root Directory: frontend
  └── Vercel: priceactioner-api / Root Directory: backend
                                      └── MongoDB Atlas: رکوردهای دائمی
مرورگر → frontend → /api → backend → MongoDB و داده عمومی Binance
```

GitHub سورس را نگه می‌دارد؛ خودش برنامه را اجرا نمی‌کند. GitHub Pages برای اجرای کامل این پروژه کافی نیست. JSON محلی نیز محل ذخیره دائمی مناسبی برای Vercel نیست؛ برنامه این تنظیم را در Production رد می‌کند.

این ساختار باید در ریشه مخزن باشد؛ همه فایل‌های سورس داخل پوشه‌ها را نگه دار، درخت زیر خلاصه است:

```text
priceactioner/
├── .gitignore
├── README.md
├── PROJECT_STATUS.md
├── backend/
│   ├── .env.example
│   ├── .python-version
│   ├── .vercelignore
│   ├── vercel.json
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── setup_admin.py
│   ├── upload_records.py
│   ├── app/                 ← همه فایل‌ها، از جمله main.py و storage/
│   └── tests/
├── frontend/
│   ├── .env.example
│   ├── package.json
│   ├── package-lock.json
│   ├── next.config.ts
│   ├── next-env.d.ts
│   ├── tsconfig.json
│   ├── postcss.config.mjs
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── public/              ← لوگو و تصویر مرجع هم اینجا هستند
├── docs/
└── scripts/
```

این موارد نباید به GitHub یا ZIP همکارت بروند:

```text
.venv/  node_modules/  .next/  __pycache__/  .pytest_cache/
.env  .env.local  و سایر فایل‌های خصوصی .env
backend/data/      ← رکوردها، هش رمزها و نشست‌های محلی
artifacts/        ← خروجی آزمایش و نسخه پشتیبان قدیمی
releases/  .vercel/  فایل‌های ZIP، DB، log و کلید خصوصی
```

`.env.example` باید بماند؛ فقط نمونه بدون راز است. `.gitignore` این حذف‌ها را تنظیم کرده است. سرور پوشه‌های نصب و خروجی build را دوباره می‌سازد. `backend/data` و هیچ فایل SQL برای انتشار لازم نیستند.

## ۲. ZIP سالم برای همکارت

عکس تو خطای `0x80070005: Access is denied` برای پوشه `bin` بود. مسیر کامل در عکس نیست، پس علت دقیق مجوز مشخص نیست. برای ارسال سورس لازم نیست پوشه‌های نصب را کپی کنی یا مجوز ویندوز را تغییر بدهی.

در PowerShell اجرا کن:

```powershell
cd C:\Users\EliteBook\Desktop\PriceActioner
python scripts/make_source_zip.py
```

جدیدترین ZIP تاریخ‌دار در `releases` ساخته و بررسی می‌شود. همان را بفرست. همکارت ابتدا Extract کند و سپس دستورهای README را برای نصب و ساخت ادمین خودش انجام بدهد. کلیدها، رمز ادمین و رکوردهای خصوصی تو داخل ZIP نیستند.

## ۳. بارگذاری در GitHub

۱. وارد GitHub شو؛ New repository را بزن. نام `priceactioner` و ترجیحاً Private را انتخاب کن. README، gitignore و License اولیه نساز، چون سورس آماده است.

۲. Git باید نصب باشد. PowerShell را در ریشه‌ای که backend و frontend کنار هم هستند باز کن:

```powershell
cd C:\Users\EliteBook\Desktop\PriceActioner
git init
git branch -M main
git add .
git status --short
```

۳. فهرست را بررسی کن؛ `.env`، `backend/data`، `.venv` و `node_modules` نباید دیده شوند. اگر فایل خصوصی قبلاً track شده، gitignore به‌تنهایی آن را از تاریخچه حذف نمی‌کند؛ قبل از انتشار مشکل را حل کن و کلید افشاشده را عوض کن.

۴. ادامه بده؛ YOUR_USERNAME را با نام حساب خودت عوض کن:

```powershell
git commit -m "Initial priceactioner project"
git remote add origin https://github.com/YOUR_USERNAME/priceactioner.git
git push -u origin main
```

اگر Git نام و ایمیل خواست، برای همین مخزن تنظیم کن و commit را دوباره بزن:

```powershell
git config user.name "YOUR NAME"
git config user.email "YOUR EMAIL"
```

از پنجره احراز هویت مرورگر Git وارد شو؛ رمز یا توکن را در remote ننویس. پس از push صفحه GitHub را Refresh کن. backend و frontend باید مستقیماً در ریشه مخزن باشند. همکار را از Settings مخزن، بخش Collaborators دعوت کن. [راهنمای GitHub](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).

## ۴. ساخت محل ثبت رکوردها در MongoDB Atlas

۱. در [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) حساب بساز. یک Project و سپس Cluster ایجاد کن. اگر Free برای حسابت موجود بود برای شروع قابل انتخاب است؛ محدودیت‌ها و هزینه را همان‌جا بررسی کن.

۲. در Database Access یک Database User، مثلاً `priceactioner_app` با رمز قوی مستقل بساز. نقش `readWrite` فقط برای دیتابیس `priceactioner` بده؛ دسترسی مدیر کل لازم نیست. این رمز با رمز سایت Atlas و ادمین برنامه فرق دارد.

۳. در Network Access / IP Access List، دسترسی شبکه را تنظیم کن. Add Current IP فقط کامپیوتر فعلی تو را مجاز می‌کند، نه Vercel را. روش محدودتر، Static IP خروجی Vercel و افزودن همان IPها در Atlas است؛ امکانات و هزینه پلن را بررسی کن. برای آزمایش اولیه، Allow Access from Anywhere با `0.0.0.0/0` هم موجود است، ولی یعنی اتصال شبکه از همه اینترنت مجاز است؛ رمز همچنان لازم است. اگر این راه موقت را انتخاب کردی، رمز منحصربه‌فرد و نقش محدود بده و بعد به IPهای مشخص محدود کن. [Atlas IP Access List](https://www.mongodb.com/docs/atlas/security/ip-access-list/)، [Allowlist در Vercel](https://vercel.com/kb/guide/how-to-allowlist-deployment-ip-address).

۴. روی Cluster، Connect → Drivers → Python را انتخاب و Connection String را کپی کن. `<db_password>` را با رمز Database User عوض کن؛ علامت‌های `< >` نباید باقی بمانند. کاراکترهای رزروشده در رمز داخل URI باید URL-encode شوند؛ رمز تصادفی طولانی با حروف و اعداد این مرحله را ساده‌تر می‌کند. شکل نمونه:

```text
mongodb+srv://priceactioner_app:YOUR_DB_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
```

این آدرس خصوصی است؛ در GitHub و frontend نگذار. دیتابیس و collectionها هنگام اولین نوشتن برنامه ایجاد می‌شوند؛ فایل SQL import نمی‌کنی. [راهنمای اتصال Atlas](https://www.mongodb.com/docs/atlas/connect-to-database-deployment/).

## ۵. پروژه frontend در Vercel

۱. در Vercel با GitHub وارد شو؛ Add New → Project؛ مخزن priceactioner را Import کن. اگر دیده نشد، دسترسی GitHub Integration را به همان مخزن Private بده.

۲. تنظیمات:

| گزینه | مقدار |
|---|---|
| Project Name | priceactioner-web یا نام آزاد دلخواه |
| Framework Preset | Next.js |
| Root Directory | frontend |
| Install Command | پیش‌فرض یا npm ci |
| Build Command | پیش‌فرض یا npm run build |
| Output Directory | پیش‌فرض Next.js؛ تغییر نده |

۳. Deploy کن و دامنه ثابت Production را بردار، مثلاً `https://priceactioner-web-abc.vercel.app`. آدرس مثال را استفاده نکن؛ دامنه واقعی خودت را بردار. در این مرحله ظاهر سایت منتشر می‌شود ولی API هنوز وصل نیست.

یک مخزن می‌تواند چند پروژه Vercel با Root Directoryهای جدا داشته باشد. [مستند رسمی](https://vercel.com/docs/monorepos).

## ۶. پروژه backend در همان Vercel

۱. دوباره Add New → Project و همان مخزن GitHub را Import کن.

۲. نام مثلاً priceactioner-api، Root Directory برابر `backend` و Framework برابر FastAPI باشد. Install/Build/Output را روی پیش‌فرض تشخیص فریم‌ورک نگه دار؛ دستور اجرای uvicorn وارد نکن. نقطه ورود `app/main.py` است. requirements.txt وابستگی‌ها و .python-version نسخه Python را تعیین می‌کنند. [FastAPI روی Vercel](https://vercel.com/docs/frameworks/backend/fastapi)، [محیط Python](https://vercel.com/docs/functions/runtimes/python).

۳. پیش از Deploy، این Environment Variables را برای Production وارد کن. هر ردیف یک متغیر جداست؛ مقدار واقعی جای نمونه‌ها بگذار و کوتیشن اضافه وارد نکن:

| Name | Value |
|---|---|
| APP_ENV | production |
| STORAGE_BACKEND | mongodb |
| MONGODB_URI | Connection String خصوصی مرحله ۴ |
| MONGODB_DATABASE | priceactioner |
| PUBLIC_ORIGIN | دامنه frontend مرحله ۵، مثل https://priceactioner-web-abc.vercel.app |
| ADMIN_USERNAME | admin |
| ADMIN_PASSWORD | رمز جدید سرور، حداقل ۱۲ کاراکتر |
| ADMIN_SECRET_KEY | خروجی تصادفی دستور پایین |
| JEV_MODE | disabled |

PUBLIC_ORIGIN نباید اسلش آخر یا مسیر /admin داشته باشد. برای تولید ADMIN_SECRET_KEY روی کامپیوتر خودت اجرا کن و خروجی را فقط در متغیر backend قرار بده:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

این secret رمز ورود نیست؛ برای نشست‌هاست. در هر deploy عوضش نکن. هیچ رمز MongoDB یا ادمین را در پروژه frontend تعریف نکن.

حساب محلی تو با نام admin و رمز انتخابی قبلی حفظ شده است؛ ولی به GitHub یا سرور منتقل نمی‌شود. اولین اجرای سرور حساب جدید را از متغیرهای بالا می‌سازد و فقط هش رمز را در Atlas نگه می‌دارد. پس از اولین ورود موفق، می‌توانی متغیر ADMIN_PASSWORD را حذف و backend را Redeploy کنی؛ حساب در Atlas باقی می‌ماند. ADMIN_SECRET_KEY را نگه دار. تغییر ADMIN_PASSWORD برای حساب موجود رمز را reset نمی‌کند؛ این متغیر فقط حساب غایب را می‌سازد.

JEV_API_KEY برای این نسخه لازم نیست. اگر خواستی نگهش داری، فقط در Environment Variables همین پروژه backend بگذار. ارسال زنده Jev پیاده نشده و گذاشتن کلید آن را فعال نمی‌کند.

۴. Deploy کن. دامنه ثابت Production بک‌اند را بردار و باز کن:

```text
https://YOUR-API.vercel.app/api/health
```

باید backend: ONLINE، database: ONLINE و storage: mongodb ببینی. binance: UNKNOWN قبل از دریافت داده طبیعی است. ریشه / بک‌اند ممکن است 404 بدهد؛ رابط سایت در frontend است.

## ۷. وصل کردن frontend به backend

در پروژه priceactioner-web، Settings → Environment Variables برای Production:

| Name | Value |
|---|---|
| BACKEND_URL | https://YOUR-API.vercel.app با دامنه واقعی backend |
| NEXT_PUBLIC_SHOW_ADMIN | false |

در BACKEND_URL مسیر /api، اسلش آخر یا localhost نگذار. از Deployments آخرین نسخه frontend را Redeploy کن. ذخیره متغیر به‌تنهایی نسخه فعلی را تغییر نمی‌دهد. [مستند متغیرهای Vercel](https://vercel.com/docs/environment-variables).

مرورگر /api دامنه سایت را صدا می‌زند و Next.js آن را به backend می‌فرستد. ورود ادمین را از دامنه frontend انجام بده. مخفی بودن دکمه ادمین جلوی ورود از /admin/login را نمی‌گیرد.

## ۸. تست پایان نصب

۱. آدرس frontend با /api/health باید ONLINE و mongodb نشان دهد.

۲. صفحه اصلی و /docs را باز کن؛ راهنمای فارسی و سهمیه روزانه دیده شوند.

۳. فرم نمونه: BUY BTC، NOW، 7 DAYS، BALANCED. تحلیل بفرست؛ خروجی و REQUEST.PREVIEW → FULL REQUEST را ببین. این پیش‌نویس به Jev ارسال نمی‌شود.

۴. /admin/login روی دامنه frontend را باز کن؛ با ادمین سرور وارد شو و History و Logs را ببین.

۵. backend را یک بار Redeploy کن؛ تاریخچه و ورود باید همچنان کار کنند. اگر رکوردها دیده نمی‌شوند، یکسان بودن MONGODB_URI و MONGODB_DATABASE را بررسی کن.

۶. در Atlas، Browse Collections، دیتابیس priceactioner به‌تدریج collectionهای admins، sessions، analyses، logs، visitors، daily_usage و login_attempts خواهد داشت. نبود بعضی collectionها پیش از اولین استفاده طبیعی است. پشتیبان‌گیری و پاک‌سازی دوره‌ای را مطابق حجم استفاده تنظیم کن؛ حذف خودکار تاریخچه پیاده نشده است.

سهمیه سه تحلیل موفق در روز، بر اساس مرورگر و ساعت UTC است. بدون حساب کاربری عمومی، هر شخص قطعی شناسایی نمی‌شود؛ پاک کردن کوکی یا مرورگر دیگر سهمیه جدا ایجاد می‌کند.

## ۹. انتقال اختیاری تاریخچه محلی

رکوردهای قبلی کامپیوتر در backend/data به JSON تبدیل شده‌اند و در ZIP نیستند. اگر تاریخچه محلی را روی سرور هم می‌خواهی، MONGODB_URI همان Atlas و MONGODB_DATABASE را در فایل خصوصی backend/.env بگذار. STORAGE_BACKEND محلی می‌تواند json بماند. از ریشه پروژه:

```powershell
cd backend
..\.venv\Scripts\python.exe upload_records.py
```

فقط تعداد نمایش داده می‌شود؛ چیزی ارسال نمی‌شود. برای ارسال واقعی:

```powershell
..\.venv\Scripts\python.exe upload_records.py --confirm
```

فقط تحلیل‌ها و لاگ‌ها منتقل می‌شوند؛ شناسه موجود بازنویسی نمی‌شود. ادمین، رمزها، نشست‌ها و سهمیه‌ها منتقل نمی‌شوند. پس از پایان History سرور را بررسی کن. هنگام انتقال تحلیل محلی تازه اجرا نکن تا مجموعه فایل‌ها ثابت بماند.

## ۱۰. تغییرات بعدی و رفع خطا

پس از تغییر کد، در ریشه پروژه:

```powershell
git add .
git status --short
git commit -m "Describe your change"
git push
```

با اتصال Git و انتشار خودکار، Vercel نسخه تازه می‌سازد. برای اولین راه‌اندازی دامنه Production ثابت را تست کن؛ Preview دامنه و تنظیمات محیطی جدا دارد و ممکن است Origin check آن را رد کند. دامنه سفارشی نیز نیاز به اصلاح PUBLIC_ORIGIN و Redeploy بک‌اند دارد.

| مشکل | راه بررسی |
|---|---|
| Origin not allowed | PUBLIC_ORIGIN دقیقاً دامنه frontend باشد، بدون اسلش آخر؛ backend را Redeploy کن. |
| MongoDB authentication failed | Database User، رمز و URL-encoding را بررسی کن؛ رمز سایت Atlas جای رمز DB نیست. |
| MongoDB timeout | IP Access List، وضعیت Cluster و Connection String؛ Add Current IP برای Vercel کافی نیست. |
| خطای نیاز به mongodb | STORAGE_BACKEND در پروژه backend و محیط Production باید mongodb باشد. |
| سایت هست ولی API قطع است | BACKEND_URL و Root Directoryها را بررسی و frontend را Redeploy کن. |
| API پاسخ 401 یا صفحه ورود Vercel می‌دهد | دامنه Production را استفاده کن. اگر Deployment Protection آن را پوشانده، دسترسی سرویس‌به‌سرویس را تنظیم کن؛ نشست مرورگر تو مجوز proxy نیست. کلید bypass را عمومی نکن. |
| ریشه backend خطای 404 دارد | /api/health را باز کن؛ backend صفحه اصلی ندارد. |
| package.json پیدا نمی‌شود | Root Directory پروژه web باید frontend باشد. |
| Python app پیدا نمی‌شود | Root Directory پروژه api باید backend و preset آن FastAPI باشد. |
| ادمین ساخته نمی‌شود | هنگام ساخت اولیه، رمز حداقل ۱۲ و secret حداقل ۳۲ کاراکتر لازم است. |
| MARKET DATA UNAVAILABLE | لاگ و پاسخ Binance روی سرور را بررسی کن؛ دسترسی میزبان با کامپیوتر محلی ممکن است فرق کند. |
| JEV_MODE validation error | فقط disabled فعلاً پیاده شده است. |

کد با JSON واقعی محلی و MongoDB شبیه‌سازی‌شده تست شده است؛ اتصال Atlas واقعی و انتشار در حساب تو هنوز انجام نشده. مرحله ۸ را پس از انتشار در محیط خودت انجام بده.
