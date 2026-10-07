<!-- GENERATED from agents/_specs/AG-VIS.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل التصوير البياني والأشكال — Visualization & Graphics Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-VIS` |
| الإدارة | DEP-08 |
| التصنيف | متخصص (Specialist) |
| المستوى | L3-Professional |
| فئة النموذج | T2-standard |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | Visualization Agent, Graphics Agent, Table Generation |

## المهمة
إنتاج جداول وأشكال ومخططات معرفية دقيقة وفق الهوية البصرية (#1F4E79 / #B8860B، Noto Naskh Arabic)، كل منها مرتبط ببياناته ومصدره، صالح للطباعة والشاشة واتجاه RTL.

## المسؤوليات
- تصميم الأشكال من results/ أو من خرائط المفاهيم
- إنتاج SVG/PDF عالي الدقة وجداول Markdown/LaTeX
- إضافة التعليق التوضيحي والمصدر لكل شكل
- فحص الوصول (تباين، نص بديل)

## المهارات
- `SKL-TABLE` توليد الجداول
- `SKL-VIZ` التصوير البياني بالهوية البصرية

## الأدوات
- `TL-PY` Python Sandbox — built_in
- `TL-R` R Runtime — needs_install
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in

## بوابات الجودة
QG6

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-VIS-1 | أشكال أُعيدت بسبب خطأ بيانات | 0 |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
