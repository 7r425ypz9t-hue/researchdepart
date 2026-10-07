# مِداد — وحدة ذكاء البحث والمعرفة والنشر

**MIDAD — Research, Knowledge & Publishing Intelligence Unit (RKPIU) → Research & Knowledge Production Operating System (RKPOS)**

إدارة بحوث ودراسات ونشر رقمية متعددة الوكلاء، محكومة ومُختبَرة وقابلة للتشغيل: من الفكرة إلى النشر والأرشفة والتعلم، مع بقاء **الفكر والأطروحة والقرار العلمي النهائي والاعتماد للنشر** تحت سلطة المؤلف.

```
Idea → Research → Evidence → Analysis → Writing → Verification → Review → Editing → Design → Publishing → Archiving → Learning
```

## ابدأ من هنا
- 📘 [المخطط التنفيذي وفهرس المخرجات الأربعين](documentation/00-executive-blueprint.md)
- 🛠 [دليل تشغيل الإدارة](documentation/phase-5/operations-manual.md)
- 👥 [سجل الوكلاء](documentation/phase-1/04-agent-registry.md)

## تشغيل سريع
```bash
pip install -e ".[dev]"
rkpos validate                     # سلامة المنظومة كاملة
pytest -q                          # الاختبارات
rkpos new-project "حوكمة الذكاء الاصطناعي في القطاع الثقافي" --type intellectual_book --domain cultural_governance
rkpos run-step RKP-2026-0001       # حزمة البرومبت للخطوة التالية
rkpos status RKP-2026-0001         # STATE · NEXT_ACTION · CURRENT_AGENT · WAITING_FOR · BLOCKERS · VERSION · QUALITY_GATE
rkpos dashboard
```

## البنية
| المجلد | المحتوى |
|---|---|
| `agents/_specs/` | **المصدر**: مواصفة لكل وكيل (35) |
| `agents/{core,specialists,supervisors,utilities,on-demand}/` | مولَّد: 8 ملفات لكل وكيل |
| `prompts/` | الدستور المشترك |
| `governance/` | حقوق القرار · البوابات · المجلس · هرم المصادر · التصنيف · البروتوكولات |
| `skills/` · `tools/` · `connectors/` | السجلات المركزية |
| `workflows/` | 19 سير عمل YAML |
| `schemas/` | 11 مخطط JSON |
| `memory/` · `knowledge-base/` | الذاكرة بطبقاتها الست |
| `projects/` | المشاريع (RKP-YYYY-NNNN) |
| `runtime/rkpos/` | طبقة التشغيل (Python) |
| `templates/` · `publishing/` · `validation/` · `logs/` · `tests/` · `scripts/` | القوالب والنشر والتحقق والسجلات |
| `documentation/` | المراحل 1–5 |

## المبادئ غير القابلة للتفاوض
1. **صفر تلفيق** — مفروض سلوكياً (الدستور) وبنيوياً (المخططات) وآلياً (الفحوص).
2. **أقل الامتيازات** — لا وكيل يرى أو يكتب إلا ما يلزمه؛ مفروض في `rkpos validate`.
3. **سيادة المؤلف** — قرارات L4 لا يعتمدها إلا `HUMAN-AUTHOR`؛ مفروض في طبقة التشغيل.
4. **الاستقلال** — المراجعة بنموذج غير نموذج الكتابة متى أمكن.
5. **الواقعية** — لا ادعاء لأداة أو تنفيذ لم يحدث؛ كل موصل موسوم بحالته الفعلية.
