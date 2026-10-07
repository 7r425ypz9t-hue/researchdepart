# المرحلة الخامسة — لوحة القيادة وإطار المؤشرات

## ٥.١ مواصفة لوحة القيادة

يولّدها `rkpos dashboard` إلى `publishing/dashboard/index.html` (RTL، الأزرق #1F4E79 والذهبي #B8860B، Noto Naskh Arabic، الوضع الداكن).

| العنصر المطلوب (القسم ٤٧) | المصدر | الحالة |
|---|---|---|
| Active Projects | `projects/RKP-*/manifest.yaml` | ✅ |
| Stage | `state.yaml → STATE, STAGE_ID` | ✅ |
| Completion % | `state.yaml → COMPLETION_PCT` (من الخطة) | ✅ |
| Current Agent | `state.yaml → CURRENT_AGENT` | ✅ |
| Quality Gate | `state.yaml → QUALITY_GATE` | ✅ |
| Open Issues / Blockers | `OPEN_ISSUES`, `BLOCKERS` | ✅ |
| Sources Verified | `research/sources.jsonl` | ✅ |
| Citations / Claims | `evidence/claims.jsonl` | ✅ |
| Cost | `logs/cost_events.jsonl` | ✅ |
| Deadlines | `DEADLINE` | ✅ |
| Human Decisions Pending | `PENDING_HUMAN_DECISIONS` | ✅ |

تطوير لاحق (النموذج C): لوحة حية متصلة بقاعدة البيانات، أو صفحة Artifact مشتركة.

## ٥.٢ إطار مؤشرات الأداء (KPI Framework)

| المؤشر | التعريف | الهدف | المصدر | المالك |
|---|---|---|---|---|
| نسبة المصادر المتحقق منها | VERIFIED ÷ القابلة للتحقق | ≥ 95% | sources.jsonl | AG-SRC |
| Citation Accuracy | الاستشهادات الصحيحة ÷ الكل | ≥ 99% | citation_audit | AG-EVA |
| Fact Error Rate | أخطاء وقائعية بعد QG4 ÷ الادعاءات | < 0.5% | fact_audit | AG-EVA |
| Reference Error Rate | أخطاء بيانات وصفية ÷ المراجع | < 1% | verification_report | AG-SRC |
| المراجع المختلقة | العدد بعد QG4 | **0** | integrity_report | AG-INT |
| نسبة إعادة العمل | خطوات أعيدت ÷ الخطوات | ≤ 25% | plan.yaml | AG-ORC |
| زمن الفصل | من C1 إلى C10 | حسب الخطة | audit.jsonl | AG-ORC |
| زمن المشروع | من S01 إلى QG7 | حسب الخطة | audit.jsonl | AG-ORC |
| ملاحظات Red Team | العدد/الفصل، ونسبة الحرجة المغلقة | 100% مغلقة | red_team_*.yaml | AG-RED |
| نسبة المشكلات المغلقة | المغلقة ÷ المفتوحة | 100% قبل QG5 | review_log | AG-SED |
| جودة المحكمين | الملاحظات الكبرى المعتمدة من المؤلف | ≥ 60% | peer_review | AG-PRV |
| الالتزام بالمواعيد | المهام في موعدها | ≥ 90% | state/audit | AG-ORC |
| تكلفة الكتاب | USD لكل مشروع/فصل | ضمن السقف | cost-report | AG-CST |
| نسبة الأتمتة | خطوات بلا تدخل يدوي ÷ الكل | ≥ 60% (B) | audit (dispatch_manual vs run_step) | AG-AUT |
| زمن الاستئناف | من الأمر «واصل» إلى أول فعل | < 2 دقيقة | state.yaml | AG-ORC |
| اعتماد من الجولة الأولى | قرارات L4 معتمدة دون إعادة | ≥ 70% | decisions.yaml | AG-ORC |
| Recall@10 للاسترجاع | على مجموعة ذهبية | ≥ 0.8 | eval RAG | AG-KNW |

مؤشرات كل وكيل بعينه في `agents/*/*/README.md` (حقل KPIs).
