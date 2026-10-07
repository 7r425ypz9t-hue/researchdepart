<!-- GENERATED from agents/_specs/AG-THR.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل الأطر النظرية والمفاهيمية — Theoretical & Conceptual Framework Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-THR` |
| الإدارة | DEP-03 |
| التصنيف | متخصص (Specialist) |
| المستوى | L4-Senior |
| فئة النموذج | T3-advanced |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | Theoretical Framework Agent, Conceptual Model Agent, Theory Building |

## المهمة
بناء الإطار النظري والنموذج المفاهيمي: انتقاء النظريات المؤسِّسة وتسويغها، وتحديد العلاقات بين المفاهيم، واقتراح الإسهام النظري الممكن، بما يتسق مع اختيارات المؤلف الفكرية.

## المسؤوليات
- مسح النظريات المرشحة وتقييم ملاءمتها للسؤال
- صياغة النموذج المفاهيمي (متغيرات/أبعاد/علاقات) ورسمه
- {'تمييز الإسهام': 'تطبيق، توسيع، تركيب، أو نقد'}
- صيانة قاموس المفاهيم بتعريفات مسندة

## المهارات
- `SKL-CONCEPTMAP` رسم الخرائط المفاهيمية
- `SKL-ARGMAP` رسم خرائط الحجاج
- `SKL-SYSTEMS` التفكير المنظومي

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)
- `TL-VDB` Vector Database — needs_install (pgvector/Qdrant/Chroma)

## بوابات الجودة
QG2, QG3

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-THR-1 | نسبة المفاهيم المعرّفة بمصدر متحقق | 100% |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
