# موقع Marvels — marvels-digital.com

الموقع بيتبني تلقائيًا من الملفات اللي في `content/`. لوحة التحكم على `marvels-digital.com/admin` بتعدّل الملفات دي، وكل حفظ بيحدّث الموقع لوحده في حوالي دقيقة.

## إيه اللي تقدر تعدّله من لوحة التحكم

| القسم | بيتحكم في |
| --- | --- |
| المقالات | إضافة وتعديل وحذف مقالات (عربي + إنجليزي)، صورة غلاف، ومسودات مش بتظهر |
| خبرتنا — العملاء | قايمة العملاء في صفحة "خبرتنا" والرئيسية |
| الباقات والأسعار | أسعار ومميزات باقات الريلز، أسعار البودكاست، سعر ساعة الاستوديو، سعر التجربة، نسبة خصم المؤسسين |
| التواصل والإعدادات | رقم الواتساب، الإيميل، العنوان، المواعيد، لينكات السوشيال، وشريط الافتتاح في الرئيسية |

نصوص صفحات الخدمات والرئيسية نفسها موجودة في `build.py`، ولو عايز تغيّرها كلمني.

## التشغيل لأول مرة (مرة واحدة بس)

### 1. ارفع الملفات على GitHub
1. اعمل حساب على github.com لو معندكش.
2. اعمل repository جديد باسم `marvels-website` (ينفع Private).
3. ارفع كل الملفات اللي في الفولدر ده (Add file ← Upload files، واسحب الملفات والفولدرات).

### 2. اربط الـrepo بـ Cloudflare Pages
1. من Cloudflare: Workers & Pages ← Create ← Pages ← Connect to Git، واختار `marvels-website`.
2. الإعدادات:
   - Framework preset: **None**
   - Build command: **`python3 build.py`**
   - Build output directory: **`dist`**
3. بعد أول نشر، من Custom domains ضيف `marvels-digital.com`، وغيّر الـnameservers عند شركة الدومين للي Cloudflare هيديهولك.

### 3. شغّل لوحة التحكم
1. افتح `admin/config.yml` على GitHub وغيّر `GITHUB-USERNAME` لاسم حسابك.
2. اعمل Personal access token من GitHub:
   Settings ← Developer settings ← Personal access tokens ← Fine-grained tokens ← Generate new token
   - Repository access: `marvels-website` بس
   - Permissions ← Contents: **Read and write**
3. افتح `marvels-digital.com/admin` واختار الدخول بالـtoken، والصق الـtoken.

احتفظ بالـtoken في مكان آمن ومتبعتهوش لحد. لو حد تاني من الفريق هيعدّل، يعمل token من حسابه بعد ما تضيفه للـrepo.

## كتابة المقالات
المحرر بيدعم: عناوين، **تقيل**، لينكات، لستات بنقط أو أرقام، وصور. اسم الملف (ولينك المقال) بيتعمل من العنوان الإنجليزي، فاكتبه بالإنجليزي حتى لو المقال عربي بس. لو سبت النسخة الإنجليزي فاضية، الصفحة الإنجليزي هتعرض العربي.

## تجربة الموقع على جهازك (اختياري)
```
python3 build.py
python3 -m http.server -d dist 8000
```
وافتح http://localhost:8000
