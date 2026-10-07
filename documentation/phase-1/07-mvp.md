# المرحلة الأولى — ٧. النسخة الدنيا القابلة للتشغيل (MVP)

## ٧.١ الفريق الأساس — ثمانية وكلاء فقط

| # | الوكيل | الدور في MVP | المهارات المستوعَبة من وكلاء غير مفعّلين |
|---|---|---|---|
| 1 | `AG-ORC` المنسق | تشغيل كل شيء + أمانة القرار | RQA (الإشكالية) · SUP-MTH · CST · BKA جزئياً |
| 2 | `AG-DSC` الاستكشاف (Research Agent) | الاكتشاف + المراجعة الأولية | LRV (SKL-LITSEARCH, SKL-ARGMAP) |
| 3 | `AG-SRC` التحقق من المصادر | حارس MEM-SOURCE + Zotero | — |
| 4 | `AG-WRT` الكتابة | المسودات بصوت المؤلف | BKA (SKL-OUTLINE) |
| 5 | `AG-SED` المحرر | تحرير علمي + لغوي + مراجعة نقدية مخففة | ARE (SKL-AREDIT) · RED · PRV · SUP-EDT |
| 6 | `AG-INT` النزاهة | تدقيق الوقائع والاستشهاد + النزاهة | EVA (SKL-FACTCHECK) · SUP-INT · SUP-EVD |
| 7 | `AG-PUB` النشر | الإخراج | SUP-PUB |
| 8 | `AG-KNW` المعرفة | الأرشفة والاستخلاص | VCS |

**المجلس في MVP:** يقوم المؤلف بدوره مباشرة (L3 ← L4)، ويعدّ المنسق الملف بتقارير المحرر والنزاهة.

## ٧.٢ ما يعمل الآن فعلاً (بلا أي حساب خارجي)

| القدرة | الحالة | كيف |
|---|---|---|
| فتح مشروع بمعرّف وبيان وخطة وحالة ومجلدات | ✅ يعمل | `rkpos new-project` |
| الاختيار الديناميكي للوكلاء | ✅ يعمل | `rkpos select` / تلقائي عند الفتح |
| حزمة برومبت كاملة لكل خطوة (System + الدستور + TASK + HANDOFF) | ✅ يعمل | `rkpos run-step` ← لصق في Claude أو ChatGPT |
| تسجيل المخرج وإغلاق الخطوة وقرارات DC-xxx | ✅ يعمل | `rkpos record-output` / `rkpos complete` |
| منع غير المؤلف من اعتماد L4 | ✅ مفروض | `runner.complete` |
| فحص الوسوم والاستشهادات والمصطلحات في المسودات | ✅ يعمل | `rkpos check-manuscript` |
| التحقق من DOI عبر Crossref | ✅ يعمل عند توفر الشبكة | `rkpos verify-doi` |
| سجل التدقيق والقرارات والحالة | ✅ يعمل | `logs/audit.jsonl` · `decisions.yaml` · `state.yaml` |
| لوحة القيادة | ✅ يعمل | `rkpos dashboard` |
| فحوص CI (البنية، السلامة، الاختبارات، الأسرار) | ✅ جاهز | `.github/workflows/validate.yml` |

## ٧.٣ ما يحتاج تفعيلاً (بالترتيب المقترح)

| الحاجة | النوع | الأثر |
|---|---|---|
| `ANTHROPIC_API_KEY` | حساب | التشغيل الحي `--live` بدل اللصق اليدوي |
| `OPENAI_API_KEY` أو `GOOGLE_API_KEY` | حساب | استقلال المراجعة (T4) عن نموذج الكتابة |
| Zotero API | حساب | مزامنة المراجع (الآن: `sources.jsonl` محلي) |
| Pandoc + XeLaTeX + خط Noto Naskh Arabic | تثبيت | بناء PDF/EPUB (`scripts/build_publication.sh`) |
| خدمة فحص تشابه | اشتراك | فحص الانتحال الكامل (الآن: فحص داخلي محدود مُصرَّح بقصوره) |
| قاعدة متجهات | تثبيت | RAG (الآن: بحث نصي) |

## ٧.٤ دورة العمل في MVP (مثال حقيقي)

```bash
rkpos new-project "حوكمة الذكاء الاصطناعي في القطاع الثقافي" --type intellectual_book --domain cultural_governance
rkpos run-step RKP-2026-0001            # ← projects/RKP-2026-0001/runs/S02/prompt.md
# الصق prompt.md في محادثة Claude، احفظ الرد في ملف
rkpos record-output RKP-2026-0001 S02 out.md
rkpos complete RKP-2026-0001 S02 --actor HUMAN-AUTHOR --decision "اعتماد الإشكالية والسؤال الرئيس"   # DC-001
rkpos status RKP-2026-0001              # NEXT_ACTION جاهز للجلسة القادمة
```

## ٧.٥ معيار الخروج من MVP إلى النموذج B
- إنجاز مشروعين كاملين (مقال محكّم + مقال رأي) عبر الخط.
- صفر مراجع مختلقة بعد QG4 في المشروعين.
- تفعيل مزودين مختلفين للنماذج.
- اعتماد المؤلف لمسرد مصطلحات ≥ 50 مدخلاً، وبصمة أسلوبية في MEM-AUTHOR.
