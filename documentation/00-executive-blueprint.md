# المخطط التنفيذي — Executive Blueprint

## «مِداد» — وحدة ذكاء البحث والمعرفة والنشر
**MIDAD — Multi-agent Intelligence for Discovery, Authorship & Dissemination**
الرمز التقني: **RKPIU** (الوحدة) ← **RKPOS** (نظام التشغيل) · الإصدار 0.1.0

> **لماذا «مِداد»؟** المِداد هو الحبر الذي يُدوَّن به العلم، وهو في تراث الكتابة العربية رمزٌ للعلم المكتوب الباقي؛ فالاسم يجمع الكتابة والعلم والأمانة في كلمة واحدة، ويصلح علامةً عربية للوحدة، مع اختصار إنجليزي دال على وظيفتها: الاكتشاف والتأليف والنشر. (الاسم مقترح؛ يُعتمد بقرار المؤلف، ويبقى RKPIU معرّفاً تقنياً ثابتاً.)

---

## ١. الأطروحة المعمارية

ليست هذه مجموعة Prompts. إنها **مؤسسة رقمية محكومة** بثلاث طبقات متكاملة:
1. **التعريف** — من يعمل ماذا، وبأي صلاحية وذاكرة وأداة (مواصفات الوكلاء، السجلات، المخططات).
2. **الحوكمة** — من يقرر، وبأي معيار، وكيف يُسجَّل (L1–L4، المجلس، البوابات، الدستور).
3. **التشغيل** — ما يجري فعلاً (طبقة `rkpos`: المشاريع، الخطط، الحالة، الرسائل، التحقق، الكلفة، المحوّل، CI).

والقاعدة الحاكمة: **AI proposes — system verifies — human author decides.**

## ٢. الأرقام الرئيسة

| البند | العدد |
|---|---|
| وكلاء مرشحون في الاستدعاء | 68 |
| وكلاء معتمدون بعد الدمج | **35** (7 إشرافي · 12 أساسي · 8 متخصص · 3 عند الطلب · 5 خدمي) |
| وكلاء MVP | **8** |
| مهارات قابلة لإعادة الاستخدام | 43 (+ 11 مهارة Claude قائمة لدى المؤلف مربوطة) |
| أدوات في السجل | 26 |
| طبقات ذاكرة + مخازن عمل | 6 + 18 |
| سير عمل | 19 (12 متخصصاً + الرئيس + 6 حوكمة/فرعية) |
| بوابات جودة | 8 (QG0–QG7) |
| مخططات JSON | 11 |
| اختبارات آلية | 35 (+ 5 حالات دستورية لكل وكيل + حالات خاصة) |

## ٣. شرط الواقعية — ما الذي يعمل الآن؟

| الفئة | الأمثلة |
|---|---|
| ✅ **يعمل الآن** | فتح المشاريع وتوليد البيان والخطة والحالة · اختيار الوكلاء · حزم البرومبت لكل خطوة (للصق في Claude/ChatGPT) · قرارات DC-xxx ومنع غير المؤلف من L4 · سجل التدقيق · فحص الوسوم والاستشهادات والمصطلحات · التحقق من DOI عبر Crossref (عند توفر الشبكة) · لوحة القيادة · CI · كل المخططات والفحوص |
| 🔧 **يحتاج برمجة إضافية** | خط استيعاب RAG · التحليل الببليومتري · OCR والمقابلة الآلية · الفهارس الآلية · مزامنة Zotero/Drive البرمجية · الأشكال بالهوية البصرية |
| 🔑 **يحتاج API/حساباً** | التشغيل الحي للنماذج (Anthropic/OpenAI/Google) · Zotero · فحص التشابه · Elicit · Notion |
| 💻 **يحتاج تثبيتاً** | Pandoc + XeLaTeX + الخطوط (PDF/EPUB) · EPUBCheck · R · قاعدة متجهات · Tesseract (عربي) · نموذج محلي |
| 👤 **يحتاج موافقتك** | كل قرارات L4 · تفعيل المزودين والميزانيات · ترقية المعرفة · اعتماد البصمة الأسلوبية والمسرد |

**لا يوجد Multi-Agent Runtime مستقل يعمل ذاتياً في الخلفية.** طبقة `rkpos` تنسّق الخطوات وتولّد المهام وتستدعي النماذج عند الطلب؛ «الوكلاء» هم تهيئات (برومبت + صلاحيات + ذاكرة + أدوات) يُشغّلها المنسق خطوةً خطوة، يدوياً أو عبر API.

## ٤. فهرس المخرجات الأربعين (القسم ٥٢)

| # | المخرج | الموضع |
|---|---|---|
| 1 | Executive Blueprint | هذه الوثيقة |
| 2 | Capability Map | [phase-1/01-capability-map.md](phase-1/01-capability-map.md) |
| 3 | Organizational Structure | [phase-1/02-organizational-structure.md](phase-1/02-organizational-structure.md) · [governance/departments.yaml](../governance/departments.yaml) |
| 4 | Complete Agent Registry | [phase-1/04-agent-registry.md](phase-1/04-agent-registry.md) |
| 5 | Agent Consolidation Recommendations | [phase-1/05-consolidation.md](phase-1/05-consolidation.md) |
| 6 | Agent Specifications | [agents/_specs/](../agents/_specs/) ← `agents/<type>/<slug>/agent.yaml` |
| 7 | System Prompt لكل Agent | `agents/<type>/<slug>/system_prompt.md` + [prompts/constitution.md](../prompts/constitution.md) |
| 8 | Skills Registry | [skills/registry.yaml](../skills/registry.yaml) · [phase-2/skills-registry.md](phase-2/skills-registry.md) |
| 9 | Tools Registry | [tools/registry.yaml](../tools/registry.yaml) · [phase-2/tools-registry.md](phase-2/tools-registry.md) |
| 10 | Permissions Matrix | [phase-2/permissions-matrix.md](phase-2/permissions-matrix.md) |
| 11 | Memory Matrix | [phase-2/memory-matrix.md](phase-2/memory-matrix.md) |
| 12 | Handoff Matrix | [phase-2/handoff-matrix.md](phase-2/handoff-matrix.md) |
| 13 | Agent Council | [governance/council.yaml](../governance/council.yaml) · [templates/council_minutes.template.md](../templates/council_minutes.template.md) |
| 14 | Governance Model | [phase-3/governance-model.md](phase-3/governance-model.md) |
| 15 | Decision Rights | [governance/decision_rights.yaml](../governance/decision_rights.yaml) |
| 16 | Workflows | [phase-3/governance-model.md §٣.٧](phase-3/governance-model.md) |
| 17 | Workflow YAML | [workflows/](../workflows/) |
| 18 | Agent YAML Templates | [schemas/agent_spec.schema.json](../schemas/agent_spec.schema.json) · [agents/on-demand/temporary-specialist-template/agent.yaml](../agents/on-demand/temporary-specialist-template/agent.yaml) |
| 19 | Project Manifest | [templates/project_manifest.template.yaml](../templates/project_manifest.template.yaml) · [schemas/project_manifest.schema.json](../schemas/project_manifest.schema.json) |
| 20 | Source Schema | [schemas/source.schema.json](../schemas/source.schema.json) |
| 21 | Memory Schema | [schemas/memory_item.schema.json](../schemas/memory_item.schema.json) · [memory/layers.yaml](../memory/layers.yaml) |
| 22 | Audit Schema | [schemas/audit.schema.json](../schemas/audit.schema.json) |
| 23 | Quality Gates | [governance/quality_gates.yaml](../governance/quality_gates.yaml) |
| 24 | Testing Framework | [phase-5/automation-security-models.md §٥.٤](phase-5/automation-security-models.md) · [tests/](../tests/) |
| 25 | Security Architecture | [phase-5/automation-security-models.md §٥.٢](phase-5/automation-security-models.md) |
| 26 | GitHub Repository Architecture | [phase-4/github-architecture.md](phase-4/github-architecture.md) |
| 27 | Google Drive Architecture | [phase-4/drive-zotero-architecture.md](phase-4/drive-zotero-architecture.md) |
| 28 | Zotero Architecture | [phase-4/drive-zotero-architecture.md §٤.٢](phase-4/drive-zotero-architecture.md) |
| 29 | Knowledge Base Architecture | [phase-4/knowledge-rag-architecture.md](phase-4/knowledge-rag-architecture.md) |
| 30 | RAG Architecture | [phase-4/knowledge-rag-architecture.md §٤.٤](phase-4/knowledge-rag-architecture.md) |
| 31 | Automation Architecture | [phase-5/automation-security-models.md §٥.١](phase-5/automation-security-models.md) |
| 32 | Dashboard Specification | [phase-5/dashboard-kpis.md](phase-5/dashboard-kpis.md) |
| 33 | KPI Framework | [phase-5/dashboard-kpis.md §٥.٢](phase-5/dashboard-kpis.md) |
| 34 | MVP | [phase-1/07-mvp.md](phase-1/07-mvp.md) |
| 35 | Target Operating Model | [phase-1/08-target-operating-model.md](phase-1/08-target-operating-model.md) |
| 36 | Cost Model | [phase-5/cost-model.md](phase-5/cost-model.md) |
| 37 | Risk Register | [phase-5/risk-roadmap-deployment.md §٥.١](phase-5/risk-roadmap-deployment.md) |
| 38 | Implementation Roadmap | [phase-5/risk-roadmap-deployment.md §٥.٢](phase-5/risk-roadmap-deployment.md) |
| 39 | Deployment Checklist | [phase-5/risk-roadmap-deployment.md §٥.٣](phase-5/risk-roadmap-deployment.md) |
| 40 | دليل تشغيل الإدارة | [phase-5/operations-manual.md](phase-5/operations-manual.md) |

ملحقات: **لوحة التحكم وأيقونة سطح المكتب** [phase-5/control-panel.md](phase-5/control-panel.md) · سلسلة القيمة الكاملة [phase-1/03-value-chain.md](phase-1/03-value-chain.md) · معمارية الوكلاء [phase-1/06-agent-architecture.md](phase-1/06-agent-architecture.md) · هندسة الوكلاء [phase-2/README.md](phase-2/README.md) · بروتوكول الفريق الأحمر [governance/red_team_protocol.md](../governance/red_team_protocol.md) · حل النزاع [governance/conflict_resolution.md](../governance/conflict_resolution.md).

## ٥. التكامل مع منظومة المؤلف القائمة

| مهارة المؤلف القائمة | الموقع في «مِداد» |
|---|---|
| `council-orchestration-ar` (الأصوات الستة) | مُعيَّنة على وكلاء مسماة في `governance/council.yaml → council_voice_mapping` |
| `source-integrity-ar` | الدستور C2–C4 + AG-SRC/EVA/INT + طبقة الضمان |
| `grmm-master-manifest-ar` | `manifest.governing_manifest` + `rkpos new-project --grmm` |
| `project-runtime-protocol-ar` | `state.yaml` (المرحلة، آخر نقطة عمل، الخطوة التالية، القرارات المثبتة، المعلّق) |
| `style-fingerprint-majed-ar` · `op-ed-column-ar` | SKL-STYLE لدى AG-WRT/ARE · `WF-OPED` |
| `academic-integrity-sunni-sources-ar` | `governance/source_hierarchy.yaml → author_policy_binding` |

السجل الكامل في [`skills/registry.yaml → existing_claude_skills`](../skills/registry.yaml).
