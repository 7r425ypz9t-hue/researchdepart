# المرحلة الرابعة — معمارية مستودع GitHub

المستودع هو **المصدر الوحيد للحقيقة** للمنظومة: التعريفات، والحوكمة، والمشاريع، والسجلات. Google Drive للتعاون والمراجعة البشرية، لا للحقيقة.

```
/research-unit  (جذر هذا المستودع)
├── governance/            حقوق القرار · البوابات · المجلس · هرم المصادر · التصنيف · البروتوكولات
├── agents/
│   ├── _specs/            ← المصدر: مواصفة واحدة لكل وكيل (تُحرَّر يدوياً)
│   ├── core/              ← مولّد: 12 وكيلاً × 8 ملفات
│   ├── specialists/       ← مولّد: 8
│   ├── supervisors/       ← مولّد: 7
│   ├── utilities/         ← مولّد: 5
│   └── on-demand/         ← مولّد: 3
├── prompts/               constitution.md (الدستور المشترك)
├── skills/                registry.yaml (43 مهارة)
├── workflows/             19 سير عمل YAML
├── schemas/               11 مخطط JSON Schema
├── tools/                 registry.yaml (26 أداة)
├── connectors/            connectors.yaml (المتطلبات الفعلية لكل موصل)
├── config/                model_routing · pricing · cost_limits · brand
├── memory/                layers.yaml + author/ (AUTHOR_ONLY)
├── knowledge-base/        sources · research · editorial · institutional · candidates
├── projects/              RKP-YYYY-NNNN/ لكل مشروع
├── templates/             قوالب ونماذج مطابقة للمخططات (مختبرة)
├── validation/            agent_selection_rules.yaml · reports/
├── publishing/            templates (LaTeX/CSS) · csl/ · <PID>/ · dashboard/
├── logs/                  audit.jsonl · cost_events.jsonl · agent_improvement_log.jsonl
├── runtime/rkpos/         طبقة التشغيل (Python)
├── scripts/               فحوص CI وبناء النشر
├── tests/                 pytest (سلامة · بروتوكول · تحقق · طرف لطرف)
├── documentation/         phase-1 … phase-5 + 00-executive-blueprint.md
└── .github/workflows/     validate · agent-regression · release · backup-and-watch
```

## ملفات كل وكيل (القسم ٢٦)
`agent.yaml · system_prompt.md · tools.yaml · permissions.yaml · memory.yaml · handoffs.yaml · tests.yaml · README.md`
يفحص `scripts/check_structure.py` اكتمالها لكل وكيل.

## سياسة الفروع والإصدارات
| العنصر | السياسة |
|---|---|
| `main` | محمي؛ الدمج عبر PR فقط بعد CI أخضر |
| فروع العمل | `project/<PID>-<topic>` للمشاريع · `agent/<ID>-<change>` لتعديل الوكلاء |
| وسوم المشاريع | `RKP-YYYY-NNNN-v0.1 … -v1.0` (v0.9/v1.0 بموافقة المؤلف) |
| وسوم المنظومة | `rkpos-vX.Y.Z` (SemVer) |
| ممنوع | force-push · حذف فرع محمي · أسرار في git |

## GitHub Actions (القسم ٣٩)

| Workflow | المشغّل | ما يفعله |
|---|---|---|
| `validate.yml` | كل دفع/PR | فحص البنية · `rkpos validate` (المخططات + الإحالات + أقل الامتيازات + تزامن المولّد) · `rkpos eval` البنيوي · pytest · فحص الأسرار · صلاحية بيانات المشاريع · الروابط الداخلية |
| `agent-regression.yml` | يدوي أو PR يمس المواصفات/البرومبتات/التوجيه — **مشروط بمتغير `RKPOS_LIVE_EVALS`** | اختبارات انحدار حية بمحكّم مستقل؛ رفع التقارير |
| `release.yml` | وسم `RKP-*-v*` | بناء PDF/EPUB من `manuscript/approved` · إنشاء Release |
| `backup-and-watch.yml` | أسبوعي | لوحة القيادة · لقطة أرشيفية (artifact 90 يوماً) |

> تنبيه واقعي: `release.yml` يثبّت Pandoc وXeLaTeX على مشغّل GitHub؛ نجاح الإخراج العربي يعتمد على توفر حزم اللغة والخطوط في المشغّل وقد يحتاج ضبطاً أول مرة.
