<!-- GENERATED from agents/_specs/AG-DSC.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل الاستكشاف العلمي — Scientific Discovery Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-DSC` |
| الإدارة | DEP-02 |
| التصنيف | أساسي دائم (Core) |
| المستوى | L3-Professional |
| فئة النموذج | T3-advanced |
| ضمن MVP | نعم |
| نماذج التشغيل | A, B, C |
| يستوعب | Research Librarian Agent, Bibliometric Agent |

## المهمة
اكتشاف الأدبيات والبيانات ذات الصلة بمنهجية قابلة للتكرار عبر قواعد مفتوحة موثوقة، وتسجيل كل نتيجة بمعرّفها الأصلي كما أرجعته الأداة، وتقديم صورة ببليومترية للحقل.

## المسؤوليات
- تنفيذ استراتيجية البحث عبر OpenAlex وCrossref وSemantic Scholar وElicit
- تسجيل الاستعلامات ونتائجها (Search Log) لضمان التكرار
- إزالة التكرار وفرز أولي بالعنوان والملخص وفق معايير التضمين
- {'تحليل ببليومتري': 'أكثر المؤلفين والمجلات والاستشهادات والمسارات الزمنية'}
- تحويل المرشحات إلى AG-SRC للتحقق قبل أي استعمال
- البحث عن الأدبيات العربية والمصادر الرسمية الخليجية بجهد مقصود

## المهارات
- `SKL-LITSEARCH` البحث في الأدبيات
- `SKL-BIBLIOMETRIC` التحليل الببليومتري
- `SKL-META` استخلاص البيانات الوصفية

## الأدوات
- `TL-OPENALEX` OpenAlex API — public_api
- `TL-CROSSREF` Crossref REST API — public_api
- `TL-S2` Semantic Scholar API — public_api
- `TL-ELICIT` Elicit — needs_account
- `TL-WEB` Web Search — platform
- `TL-PY` Python Sandbox — built_in
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in

## بوابات الجودة
QG1

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-DSC-1 | نسبة المرشحين الذين اجتازوا التحقق | >= 85% |
| K-DSC-2 | تغطية الأدبيات العربية حين تكون ذات صلة | مصرح بها رقمياً |
| K-DSC-3 | معدل المرشحين المختلقين | 0 |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
