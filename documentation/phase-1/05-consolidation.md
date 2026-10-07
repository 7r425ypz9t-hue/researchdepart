# المرحلة الأولى — ٥. كشف الوظائف المتكررة ودمجها (Agent Consolidation)

> الحصيلة: **٦٨ وكيلاً مرشحاً** في الاستدعاء ← **٣٤ وكيلاً عاملاً + قالب مؤقت واحد**، و**٤٣ مهارة** قابلة لإعادة الاستخدام، و**٥ وظائف حتمية** نُقلت إلى سكربتات.
> معيار الإبقاء وكيلاً مستقلاً: (أ) ذاكرة أو صلاحيات مختلفة جوهرياً، أو (ب) شرط استقلال رقابي، أو (ج) KPI ومستهلك مخرجات مختلفان.

## ٥.١ جدول القرار لكل وكيل مرشح

| المرشح | القرار | يصبح | التعليل |
|---|---|---|---|
| Research Director Agent | **يبقى** | AG-DIR | البرامج والمحفظة وأمانة المجلس (B/C) |
| Chief Knowledge Officer Agent | دمج | AG-DIR (استراتيجي) + AG-KNW (تشغيلي) | لا يستحق وكيلاً ثالثاً |
| Research Program Manager | دمج | AG-DIR | البرامج وظيفة مديرية |
| Project Management Agent | دمج → مهارة | AG-ORC + SKL-PROJMGMT | المنسق يملك الخطة والحالة |
| Research Question Architect | **يبقى** | AG-RQA | بوابة QG0 تستحق دوراً مستقلاً |
| Scientific Discovery Agent | **يبقى** | AG-DSC | — |
| Literature Review Agent | **يبقى** | AG-LRV | — |
| Systematic Review Agent | دمج → وضع | AG-LRV + SKL-PRISMA | الذاكرة والأدوات نفسها |
| Bibliometric Agent | دمج → مهارة | AG-DSC + SKL-BIBLIOMETRIC | — |
| Source Verification Agent | **يبقى** | AG-SRC | حارس MEM-SOURCE الوحيد |
| Research Librarian Agent | دمج | AG-DSC (الاكتشاف) + AG-SRC (الفهرسة) | — |
| Theoretical Framework Agent | **يبقى** | AG-THR | — |
| Conceptual Model Agent | دمج | AG-THR + SKL-CONCEPTMAP | — |
| Quantitative / Qualitative / Mixed / Causal Methods | دمج → أوضاع | AG-MTH | صلاحيات وذاكرة متطابقة |
| Statistical / Data Science / Python-R / Network / Simulation | دمج → أوضاع | AG-DAT | بيئة تحليل واحدة |
| Visualization Agent | **يبقى** | AG-VIS (+ Graphics + Tables) | مخرج إنتاجي ذو هوية بصرية |
| Public Policy / Foresight / Systems / Scenario / Economic | دمج → أوضاع | AG-POL + SKL-SCENARIO + SKL-SYSTEMS | — |
| Cultural Policy Agent | **يبقى** | AG-CUL | مجال المؤلف الأساس؛ عضو المجلس بصفة Domain Expert |
| Book Architect Agent | **يبقى** | AG-BKA | — |
| Academic / Intellectual Writing / Chapter Development / Argumentation | دمج → أوضاع | AG-WRT + SKL-ARGMAP | كاتب واحد بصوت واحد يمنع تشظي الأسلوب |
| Scientific Editor Agent | **يبقى** | AG-SED | — |
| Peer Reviewer Agent | **يبقى** | AG-PRV | استقلال (نموذج مختلف) |
| Devil's Advocate / Red Team / Logical Consistency | دمج | AG-RED | وظيفة عدائية واحدة |
| Fact Checker / Citation Auditor / Statistics Auditor / Evidence Quality | دمج | AG-EVA | تدقيق مستقل واحد على مستوى الادعاء |
| Arabic Language / Stylistic / Copy Editor / Terminology | دمج | AG-ARE + SKL-TERMS | — |
| Research Integrity / Plagiarism Risk / Copyright | دمج | AG-INT + SKL-RISKAUDIT + SKL-RIGHTS | — |
| Manuscript Manager | دمج | AG-PUB (التجميع) + AG-VCS (الإصدارات) | — |
| Version Control / GitHub / Backup | دمج | AG-VCS (سكربتات في MVP) | — |
| Indexing / Bibliography / Layout / EPUB / PDF / Prepress / Cover Coordinator | دمج | AG-PUB + مهارات | خط إنتاج واحد بأدوات حتمية |
| Graphics Agent | دمج | AG-VIS | — |
| Knowledge Base Architect | دمج | AG-KNW (تشغيل) + مهندس بشري (تصميم) | التصميم مرة واحدة لا وظيفة دائمة |
| RAG Engineer Agent | دمج | AG-AUT (تشغيل الخط) | — |
| Metadata Agent | دمج → مهارة | SKL-META داخل SRC/KNW/AUT | — |
| Archive Agent | دمج | AG-KNW | — |
| Automation Agent | **يبقى** | AG-AUT (B/C) | — |
| Security & Permissions Agent | **يبقى** | AG-SEC (B/C)؛ سكربت في MVP | استقلال رقابي تقني |
| — (جديد) Cost Agent | **يُضاف** | AG-CST | مطلوب في القسم ٤٦ |
| — (جديد) Research Watch Agent | **يُضاف** | AG-WCH | مطلوب في القسم ٤٠ |
| — (جديد) Translation Agent | **يُضاف** | AG-TRN (On-Demand) | سير عمل الإصدار المترجم |
| — (جديد) Critical Edition Agent | **يُضاف** | AG-TAH (On-Demand) | سير عمل تحقيق المخطوط |
| — (جديد) Supervisors ×5 | **يُضاف** | AG-SUP-* | القسم ١٨ |
| — (جديد) Temporary Specialist | **قالب** | AG-TMP | بروتوكول الوكيل المفقود |

## ٥.٢ ما نُقل إلى سكربتات حتمية (لا LLM)

| الوظيفة | التنفيذ | لماذا ليس وكيلاً |
|---|---|---|
| فحص الوسوم | `runtime/rkpos/verify/claims.py` | قاعدة صريحة |
| فحص الاستشهادات | `runtime/rkpos/verify/citations.py` | مطابقة معرّفات |
| حل DOI | `runtime/rkpos/verify/doi.py` | استجابة Crossref هي الحكم |
| كشف التكرار | `runtime/rkpos/verify/bibclean.py` | تطبيع نصي |
| حساب الكلفة | `runtime/rkpos/cost.py` | حساب |

## ٥.٣ الحصيلة الرقمية

| الفئة | العدد | الأعضاء |
|---|---|---|
| D إشرافي | 7 | ORC · DIR · SUP-MTH · SUP-EVD · SUP-EDT · SUP-INT · SUP-PUB |
| A أساسي | 12 | RQA · DSC · SRC · LRV · BKA · WRT · EVA · SED · ARE · INT · PUB · KNW |
| B متخصص | 8 | THR · MTH · DAT · VIS · POL · CUL · PRV · RED |
| C عند الطلب | 3 | TRN · TAH · TMP (قالب) |
| E خدمي | 5 | VCS · AUT · SEC · CST · WCH |
| **المجموع** | **35** | منها **8** في MVP |
