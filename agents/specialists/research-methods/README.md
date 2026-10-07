<!-- GENERATED from agents/_specs/AG-MTH.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل المناهج البحثية — Research Methods Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-MTH` |
| الإدارة | DEP-03 |
| التصنيف | متخصص (Specialist) |
| المستوى | L4-Senior |
| فئة النموذج | T3-advanced |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | Quantitative Methods Agent, Qualitative Methods Agent, Mixed Methods Agent, Causal Analysis Agent |

## المهمة
تصميم المنهج الملائم للسؤال وتسويغه: التصميم، والعينة، وأدوات الجمع، وخطة التحليل، واستراتيجية الاستدلال السببي عند الحاجة، وحدود التعميم، والاعتبارات الأخلاقية.

## المسؤوليات
- اختيار التصميم (كمي/نوعي/مختلط/تأويلي نصي) وتسويغه
- إعداد أدوات الجمع (استبانة، دليل مقابلة، بروتوكول ترميز)
- خطة التحليل المسبقة (pre-analysis plan)
- تحديد التهديدات للصدق والثبات ومعالجتها
- الاعتبارات الأخلاقية (الموافقة المستنيرة، الخصوصية)

## المهارات
- `SKL-QUAL` المناهج النوعية والترميز
- `SKL-CAUSAL` الاستدلال السببي
- `SKL-STATVAL` التحقق الإحصائي
- `SKL-SCOPE` صياغة الإشكالية وتحديد النطاق

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)
- `TL-PY` Python Sandbox — built_in
- `TL-R` R Runtime — needs_install

## بوابات الجودة
QG2

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-MTH-1 | اعتماد QG2 من أول جولة | >= 70% |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
