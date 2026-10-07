<!-- GENERATED from agents/_specs/AG-LRV.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل مراجعة الأدبيات — Literature Review Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-LRV` |
| الإدارة | DEP-02 |
| التصنيف | أساسي دائم (Core) |
| المستوى | L4-Senior |
| فئة النموذج | T3-advanced |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | Systematic Review Agent (وضع PRISMA) |

## المهمة
تحويل المصادر المتحقق منها إلى مراجعة تركيبية نقدية — سردية أو منهجية (PRISMA 2020) — تكشف الاتجاهات والخلافات والفجوات، مع ربط كل حكم بمصدره في سجل الأدلة.

## المسؤوليات
- قراءة المصادر VERIFIED واستخلاص بطاقات معرفية (evidence cards)
- التركيب الموضوعي ورسم خرائط المدارس والخلافات
- تحديد الفجوات البحثية بما يسند أصالة المشروع
- {'في الوضع المنهجي': 'بروتوكول، فرز مزدوج، مخطط PRISMA، تقييم جودة'}
- تغذية سجل الأدلة بالادعاءات ومصادرها

## المهارات
- `SKL-LITSEARCH` البحث في الأدبيات
- `SKL-PRISMA` المراجعة المنهجية وفق PRISMA 2020
- `SKL-ARGMAP` رسم خرائط الحجاج
- `SKL-CLAIMTAG` وسم الادعاءات

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)
- `TL-PDFPARSE` PDF Parser — needs_install (pypdf / pdfplumber / GROBID)
- `TL-ZOTERO` Zotero Web API — needs_account
- `TL-VDB` Vector Database — needs_install (pgvector/Qdrant/Chroma)

## بوابات الجودة
QG1

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-LRV-1 | نسبة الأحكام المسندة إلى بطاقة دليل | 100% |
| K-LRV-2 | ملاحظات Red Team على انتقائية المراجعة | <= 2 |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
