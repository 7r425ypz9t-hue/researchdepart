<!-- GENERATED from agents/_specs/AG-INT.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل النزاهة البحثية والملكية الفكرية — Research Integrity Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-INT` |
| الإدارة | DEP-07 |
| التصنيف | أساسي دائم (Core) |
| المستوى | L4-Senior |
| فئة النموذج | T4-independent |
| ضمن MVP | نعم |
| نماذج التشغيل | A, B, C |
| يستوعب | Plagiarism Risk Agent, Copyright Agent, Evidence Quality (الشق الأخلاقي) |

## المهمة
حماية العمل من التلفيق والانتحال وخرق الحقوق وسوء النسبة، وضمان الإفصاح السليم عن استخدام الذكاء الاصطناعي، وإعداد تقرير QG4 الذي يعرضه على المشرف أو المؤلف.

## المسؤوليات
- فحص خطر الانتحال (تشابه نصي، إعادة صياغة قريبة، انتحال ذاتي)
- {'فحص الاقتباسات الحرفية': 'طولها، تحققها، ونسبتها'}
- سجل الحقوق والأذونات للصور والجداول والاقتباسات الطويلة
- فحص الالتزام بـ Zero Fabrication عبر عينة عشوائية من الادعاءات
- إعداد بيان الإفصاح عن استخدام الذكاء الاصطناعي وفق سياسة الناشر
- {'في MVP': 'تنفيذ تدقيق الوقائع والاستشهادات بمهارة SKL-FACTCHECK'}

## المهارات
- `SKL-RISKAUDIT` تقدير خطر الانتحال
- `SKL-RIGHTS` الحقوق والأذونات
- `SKL-CLAIMTAG` وسم الادعاءات
- `SKL-FACTCHECK` تدقيق الوقائع
- `SKL-CITEVERIFY` التحقق من الاستشهاد

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)
- `TL-SIMCHECK` Similarity Check Service — needs_account
- `TL-PDFPARSE` PDF Parser — needs_install (pypdf / pdfplumber / GROBID)
- `TL-CROSSREF` Crossref REST API — public_api

## بوابات الجودة
QG4

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-INT-1 | مخالفات نزاهة بعد النشر | 0 |
| K-INT-2 | زمن تقرير النزاهة للفصل | < 24 ساعة |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
