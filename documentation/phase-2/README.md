# المرحلة الثانية — هندسة الوكلاء (Agent Engineering)

## ٢.١ مبدأ «المصدر الوحيد للحقيقة»

لكل وكيل ملف مواصفة واحد يُحرَّر يدوياً: `agents/_specs/AG-XXX.yaml` (مخططه `schemas/agent_spec.schema.json`).
يولّد منه الأمر `rkpos generate` الملفات الثمانية المطلوبة في القسم ٢٦ داخل `agents/<type>/<slug>/`:

| الملف | المحتوى | المصدر في المواصفة |
|---|---|---|
| `agent.yaml` | نموذج القسم ٢٧ حرفياً + حقول الدمج والأوضاع | الحقول الرئيسة |
| `system_prompt.md` | البرومبت الخاص (القسم ٨) ببنيته الإلزامية | كل الحقول |
| `tools.yaml` | الأدوات المصرح بها مع الوصول والمخاطر والبدائل | `tools` + سجل الأدوات |
| `permissions.yaml` | المسموح/الممنوع/الموافقات/مسارات الكتابة/فئات البيانات | `permissions`, `human_approval`, `memory` |
| `memory.yaml` | القراءة/الكتابة بالمسارات والتصنيف | `memory` + `memory/layers.yaml` |
| `handoffs.yaml` | الاستقبال/الإرسال/الاستشارة/التصعيد/البديل | `handoffs`, `consult`, `escalation` |
| `tests.yaml` | حالات خاصة + ٥ حالات دستورية عامة | `tests` |
| `README.md` | بطاقة تعريف بشرية | — |

**لماذا التوليد؟** لأن ٣٥ وكيلاً × ٨ ملفات = ٢٨٠ ملفاً؛ تحريرها يدوياً يولّد تناقضات حتمية. CI يرفض أي ملف مولّد لا يطابق مصدره.

## ٢.٢ مطابقة قالب المواصفة (القسم ٧)

| حقل القالب | الحقل في المواصفة |
|---|---|
| Agent_ID · Agent_Name_AR · Agent_Name_EN | `agent_id` · `name_ar` · `name_en` |
| Department · Agent_Type · Seniority_Level | `department` · `type` · `seniority` |
| Primary_Mission | `mission` |
| Responsibilities · Inputs · Outputs | `responsibilities` · `inputs` · `outputs` |
| Required Skills · Tools · Connectors | `skills` · `tools` · `connectors` |
| Memory Access · Write Permissions | `memory.read` · `memory.write` |
| Restricted Actions | `permissions.prohibited` |
| Human Approval Required | `human_approval` |
| Incoming / Outgoing Handoffs | `handoffs.receives_from` / `handoffs.sends_to` |
| Quality Checks · KPIs | `quality_checks` · `kpis` |
| Failure Handling · Escalation | `failure_handling` · `escalation` |
| (إضافات) | `consult` · `stop_conditions` · `source_rules` · `output_contract` · `model_tier` · `tests` · `absorbs` · `modes` |

## ٢.٣ بنية System Prompt (القسم ٨)

كل برومبت يحوي بالترتيب: `SYSTEM ROLE · MISSION · AUTHORIZED TASKS · PROHIBITED TASKS · INPUTS · TOOLS · SKILLS · MEMORY POLICY · SOURCE POLICY · INTEGRITY RULES · QUALITY STANDARD · CONSULTATION · HANDOFF RULES · STOP CONDITIONS · ESCALATION RULES · FAILURE HANDLING · DECISION LOGGING · OUTPUT CONTRACT`
ثم يُلحق به **الدستور المشترك** [`prompts/constitution.md`](../../prompts/constitution.md) عند التشغيل (`rkpos prompt AG-XXX`).
اختبار آلي يضمن: لا تطابق بين أي برومبتين، ووجود كل الأقسام في كل برومبت.

| البند المطلوب في القسم ٨ | موضعه في البرومبت |
|---|---|
| ١ الهوية المهنية | SYSTEM ROLE |
| ٢ الهدف | MISSION |
| ٣ الاختصاص | AUTHORIZED TASKS · INPUTS · SKILLS |
| ٤ ما يجوز | AUTHORIZED TASKS · Explicitly allowed |
| ٥ ما لا يجوز | PROHIBITED TASKS |
| ٦ قواعد المصادر | SOURCE POLICY |
| ٧ قواعد النزاهة | INTEGRITY RULES + الدستور C2–C3 |
| ٨ شكل المخرجات | OUTPUT CONTRACT |
| ٩ متى يطلب رأي وكيل آخر | CONSULTATION |
| ١٠ متى يوقف التنفيذ | STOP CONDITIONS |
| ١١ متى يرفع للإنسان | ESCALATION RULES (Human approval REQUIRED) |
| ١٢ تسجيل القرارات | DECISION LOGGING |

## ٢.٤ الفهارس والمصفوفات المولّدة

- [سجل الوكلاء](../phase-1/04-agent-registry.md)
- [سجل المهارات](skills-registry.md) — المصدر: [`skills/registry.yaml`](../../skills/registry.yaml)
- [سجل الأدوات](tools-registry.md) — المصدر: [`tools/registry.yaml`](../../tools/registry.yaml)
- [مصفوفة الصلاحيات](permissions-matrix.md)
- [مصفوفة الذاكرة](memory-matrix.md)
- [مصفوفة التسليم](handoff-matrix.md)
- [منهج البصمة الأسلوبية القابلة للقياس](style-fingerprint-method.md)

## ٢.٥ إضافة وكيل أو تعديله
1. حرّر/أنشئ `agents/_specs/AG-XXX.yaml`.
2. `rkpos generate && rkpos validate && pytest -q`.
3. إن تغيّر البرومبت أو النموذج: سير العمل `WF-AGENT-CHANGE` (اختبارات انحدار حية + موافقة L4).
4. ارفع `version` في المواصفة؛ يُسجَّل في `CHANGELOG.md`.
