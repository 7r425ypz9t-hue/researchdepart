# دليل تشغيل الإدارة — «مِداد»

> دليل عملي للمؤلف وللمشرف التقني. كل أمر هنا يعمل في هذا الإصدار ما لم يُذكر خلافه.

## ١. التهيئة (مرة واحدة)
```bash
pip install -e ".[dev]"          # أو: pip install -e ".[dev,anthropic,openai]" للتشغيل الحي
cp .env.example .env              # واملأ ما تحتاجه فقط
rkpos validate && pytest -q
```

## ١ب. لوحة التحكم (الطريق الأسهل)
أيقونة **«مداد»** على سطح المكتب تفتح لوحة محلية فيها كل ما في هذا الدليل من أوامر: المشاريع، وتفعيل أي وكيل، والاعتمادات، والذاكرة، والفحوص، والسجل والكلفة.
التثبيت والمحرّكات وضمانات الأمان: [control-panel.md](control-panel.md). من الطرفية: `rkpos panel`.

## ٢. بدء مشروع
```bash
rkpos new-project "حوكمة الذكاء الاصطناعي في القطاع الثقافي" \
  --type intellectual_book --domain cultural_governance --model A [--deadline 2027-03-31] [--grmm path/to/GRMM.md]
```
النتيجة: `RKP-YYYY-NNNN` + بيان + خطة من سير العمل المناسب + وكلاء مختارون بتعليل + حالة + سجل.
أنواع المشاريع: `intellectual_book · academic_book · policy_study · systematic_review · literature_review · foresight_study · critical_edition · journal_article · op_ed · strategic_report · translation · re_edition`.

## ٣. الدورة اليومية

| ما تريد | الأمر |
|---|---|
| «أين وصلنا؟» (واصل) | `rkpos status RKP-…` ← اقرأ `NEXT_ACTION` |
| تنفيذ الخطوة التالية (يدوياً) | `rkpos run-step RKP-…` ← الصق `runs/<step>/prompt.md` في Claude ← احفظ الرد ← `rkpos record-output RKP-… <step> out.md` |
| تنفيذها آلياً | `rkpos run-step RKP-… --engine claude_code` (حسابكم في Claude Code) أو `--live` (مفتاح API) |
| تفعيل وكيل مباشرة | `rkpos activate AG-XXX "التكليف" [--register essay] [--project RKP-…] [--engine claude_code]` |
| اعتماد خطوة/بوابة بصفتك المؤلف | `rkpos complete RKP-… <step> --actor HUMAN-AUTHOR --decision "…"` ← يولّد DC-xxx |
| اعتماد نص نهائي لفصل | `rkpos complete RKP-… <step> --actor HUMAN-AUTHOR --approved-file edited/ch01.md` |
| فحص مسودة | `rkpos check-manuscript RKP-… drafts/ch01.md` (وسوم · استشهادات · مصطلحات) |
| التحقق من DOI | `rkpos verify-doi 10.xxxx/yyyy --title "…" --year 2020` |
| الكلفة | `rkpos cost-report --project RKP-…` |
| اللوحة | `rkpos dashboard` ← `publishing/dashboard/index.html` |

## ٣ب. عقد الأسلوب (بصمتكم في التشغيل)
- عند `run-step` يُضاف إلى برومبت وكلاء الكتابة والتحرير (AG-WRT، AG-ARE، AG-SUP-EDT…) **عقد أسلوب**، وهو الملامح المعتمدة من بصمتكم لسجلّ المشروع: `essay` للمقال والكتاب الفكري، و`academic` للأكاديمي.
- تُختار عناصر العقد من الملامح المعتمدة وحدها؛ والوكلاء الذين لا يملكون قراءة ذاكرتكم لا يرونه.
- حزم البرومبت في `projects/*/runs/` لا تُرفع إلى المستودع، ويرفض الفحص الأمني أي ملف متتبع يحمل العقد.
- لمعاينة العقد: `rkpos prompt AG-WRT --register essay`.
- يقيس `check-manuscript` المسودة بمرجع سجلّها، ويبيّن قربها من صوتكم في المقال والسرد.

## ٤. قواعد الاستشهاد في المسودات
- استشهد بمعرّف المصدر: `[@SRC-000123, p. 45]`؛ لا تكتب مرجعاً حراً.
- لا مصدر يُستشهد به قبل تسجيله في `research/sources.jsonl` (أو السجل المركزي) بحالة VERIFIED/PARTIAL.
- وسوم الادعاءات إلزامية؛ `[NEEDS-EVIDENCE]` بدل التخمين.

## ٥. متى تتدخل أنت (L4)
العنوان · الأطروحة · الاستنتاجات الجوهرية · حذف/إضافة فصل · إضافة نظرية · الهيكل · النشر · ترقية المعرفة · الوكلاء المؤقتون · الصلاحيات · المواد المحمية · أي صياغة جديدة لموقفك.
المنظومة تعدّ لك **موجز قرار** (`templates/decision_brief.template.md`) ولا تتقدم قبل قرارك.

## ٦. إغلاق مشروع
تتبع الخطة `WF-PROJECT-CLOSE`: وسوم ونسخ ← أرشيف بـ checksums ← استخلاص المعرفة ← QG7 ← اعتمادك للعناصر المرشحة ← `rkpos memory-promote <MEM-ID> --layer MEM-INSTITUTIONAL --approved-by HUMAN-AUTHOR`.

## ٧. تعديل وكيل
حرّر `agents/_specs/AG-XXX.yaml` ← `rkpos generate` ← `rkpos validate` ← `pytest` ← (إن تغيّر البرومبت/النموذج) `rkpos eval AG-XXX --live` ← اعتمادك ← دمج.
لا تحرر الملفات المولدة في `agents/<type>/` يدوياً.

## ٨. حين يتعطل شيء
| العرض | الإجراء |
|---|---|
| `rkpos validate` يفشل | اقرأ الرسالة: إحالة مفقودة أو ملف مولد قديم ← `rkpos generate` |
| DOI بحالة PENDING | الشبكة/الخدمة؛ أعد لاحقاً — لا يُعد فشلاً |
| `PermissionError: L4 step requires HUMAN-AUTHOR` | سلوك مقصود: الاعتماد لك |
| `INDEPENDENCE_DEGRADED` | فعّل مزوداً ثانياً للمراجعة |
| `NO_PROVIDER_CONFIGURED` | الوضع اليدوي يعمل؛ أو أضف مفتاحاً |
