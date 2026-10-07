# المرحلة الأولى — ٣. سلسلة القيمة الكاملة (٣٣ مرحلة)

> لكل مرحلة: المدخلات · المخرجات · الوكيل المسؤول · الوكيل المراجع · الأدوات · معيار الجودة · نقطة التسليم · الموافقة البشرية.
> في النموذج A تُنفَّذ أدوار الوكلاء غير المفعّلين بمهارات داخل وكلاء MVP (انظر `validation/agent_selection_rules.yaml` → `model_substitutions`).

| # | المرحلة | المدخلات | المخرجات | المسؤول | المراجع | الأدوات | معيار الجودة | Handoff إلى | موافقة بشرية |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Idea | طلب المؤلف | manifest · state · plan | AG-ORC | AG-DIR | TL-FS, TL-MSG | manifest صالح وفق المخطط | AG-RQA | فتح المشروع وميزانيته (L4) |
| 2 | Topic Scoping | الفكرة، MEM-AUTHOR | scope.md | AG-RQA | AG-DIR | TL-LLM, TL-OPENALEX | نطاق داخل/خارج صريح | AG-RQA | — |
| 3 | Research Question | scope | research_questions.yaml | AG-RQA | AG-SUP-MTH | TL-LLM | سؤال رئيس + 3–7 فرعية قابلة للإجابة | AG-DSC | **نعم — QG0** |
| 4 | Conceptual Mapping | الأسئلة | concept_map.mmd · تعريفات | AG-RQA (SKL-CONCEPTMAP) | AG-THR | TL-LLM | تعريف عامل لكل مفهوم مركزي | AG-THR | — |
| 5 | Literature Discovery | search_strategy | search_log · candidates.csv | AG-DSC | AG-SRC | TL-OPENALEX, TL-CROSSREF, TL-S2, TL-ELICIT | استعلامات قابلة للتكرار؛ كل مرشح بمعرّف أداة | AG-SRC | — |
| 6 | Evidence Collection | candidates | نصوص كاملة · ملخصات | AG-DSC | AG-LRV | TL-PDFPARSE, TL-ZOTERO | وسم ABSTRACT-ONLY عند تعذر النص | AG-SRC | — |
| 7 | Source Verification | المرشحات | sources.jsonl · Zotero | AG-SRC | AG-SUP-EVD | TL-CROSSREF, TL-OPENALEX, TL-ZOTERO | ≥95% VERIFIED؛ صفر DOI غير متحقق | AG-LRV | مصدر NOT_VERIFIABLE مركزي |
| 8 | Literature Review | المصادر VERIFIED | literature_review · evidence_cards | AG-LRV | AG-SUP-EVD | TL-VDB, TL-PDFPARSE | كل حكم مسند لبطاقة | AG-THR | — |
| 9 | Theory Building | المراجعة | theoretical_framework | AG-THR | AG-SUP-MTH | TL-LLM | المفاهيم منسوبة لمصادر أولية | AG-MTH / AG-BKA | **إضافة نظرية (L4)** |
| 10 | Methodology | الإطار | methods_plan · instruments | AG-MTH | AG-SUP-MTH | TL-PY, TL-R | مواءمة السؤال-التصميم — **QG2** | AG-DAT | جمع بيانات من بشر |
| 11 | Data Collection | الخطة | data/raw | AG-MTH + المؤلف | AG-SUP-MTH | TL-GSHEETS, TL-SQL | مصدر موثق لكل مجموعة بيانات | AG-DAT | **نعم (أخلاقيات)** |
| 12 | Analysis | البيانات | analysis/ · results | AG-DAT | AG-SUP-MTH | TL-PY, TL-R | إعادة إنتاج 100% | AG-POL / AG-WRT | — |
| 13 | Interpretation | النتائج | interpretation notes | AG-DAT + AG-POL | AG-RED | TL-LLM | فصل الدليل عن التقدير (HYP) | AG-BKA | استنتاج مخالف للفرضية |
| 14 | Argument Development | الأدلة والإطار | argument_map.mmd | AG-BKA (SKL-ARGMAP) | AG-RED | TL-LLM | لا قفزات غير مسوغة | AG-BKA | — |
| 15 | Book Architecture | الأطروحة + الخريطة | outline.yaml · chapter_briefs | AG-BKA | AG-COUNCIL | TL-GDOCS | لكل فصل وظيفة وسؤال وأدلة | AG-WRT | **اعتماد الهيكل (L4)** |
| 16 | Drafting | الموجز + البطاقات | drafts/chNN | AG-WRT | AG-SED | TL-LLM, TL-VDB | كل ادعاء موسوم ومسند | AG-EVA | — |
| 17 | Fact Checking | المسودة | fact_audit | AG-EVA | AG-SUP-EVD | TL-PDFPARSE, TL-PY | حكم بمقتطف لكل ادعاء | AG-WRT / AG-INT | — |
| 18 | Citation Checking | المسودة + السجل | citation_audit | AG-EVA (+ `verify/citations.py`) | AG-SUP-INT | TL-CROSSREF, TL-ZOTERO | Citation Accuracy ≥ 99% | AG-INT | — |
| 19 | Peer Review | المحرر | peer_review | AG-PRV (+ محكمون بشريون في B/C) | AG-SUP-EDT | TL-LLM (T4) | ملاحظات بموضع ودليل | AG-SED | توصية رفض ← المجلس |
| 20 | Critical Review (Red Team) | المحرر + الخريطة | red_team | AG-RED | AG-COUNCIL | TL-LLM (T4), TL-S2 | الأنماط الثمانية مغطاة — **QG3** | AG-WRT / AG-SED | تحدٍّ يهدم الأطروحة |
| 21 | Revision | التقارير | drafts vX + revision_response | AG-WRT | AG-SED | TL-LLM | كل ملاحظة مغلقة أو معللة | AG-SED | رفض ملاحظة تحكيم |
| 22 | Language Editing | المحرر | language_edited | AG-ARE | AG-SUP-EDT | TL-LLM, TL-GDOCS | بلا تسطيح للسجل | AG-ARE | — |
| 23 | Copy Editing | النص | النص المضبوط | AG-ARE | AG-SUP-EDT | `verify/terms.py` | ≤3 أخطاء/10آلاف كلمة — **QG5** | AG-INT | — |
| 24 | Indexing | النص المعتمد | index.md | AG-PUB (SKL-INDEX) | AG-SUP-PUB | TL-PY | كل مدخل مرتبط بموضع | AG-PUB | مراجعة بشرية للمدخلات |
| 25 | Bibliography | Zotero/CSL | قائمة المراجع | AG-PUB | AG-EVA | TL-CSL, TL-ZOTERO | مولّدة آلياً لا يدوياً | AG-PUB | — |
| 26 | Graphics & Tables | النتائج + الخطة | figures · tables | AG-VIS | AG-EVA | TL-PY | مصدر وسكربت لكل شكل | AG-PUB | الأشكال المعبرة عن الأطروحة |
| 27 | Layout | المعتمد | PDF/EPUB تجريبي | AG-PUB | AG-SUP-PUB | TL-PANDOC | RTL وخطوط مضمّنة | AG-PUB | — |
| 28 | Cover Design | cover_brief | الغلاف | مصمم بشري (تنسيق AG-PUB) | المؤلف | — | الهوية البصرية والحقوق | AG-PUB | **نعم** |
| 29 | Prepress | الحزمة | book.pdf · book.epub · metadata | AG-PUB | AG-SUP-PUB | TL-EPUBCHECK | checksum مطابق — **QG6** | AG-VCS | **نعم** |
| 30 | Publishing | الحزمة المعتمدة | Release v1.0 | AG-VCS + المؤلف | AG-SUP-PUB | TL-GITHUB | — | AG-KNW | **قرار النشر (L4)** |
| 31 | Archiving | كل المخرجات | archive/ + checksums | AG-KNW + AG-VCS | AG-SUP-PUB | TL-GDRIVE, TL-GITHUB | نسختان في موقعين — **QG7** | AG-KNW | — |
| 32 | Knowledge Extraction | السجلات | kb_candidates · lessons | AG-KNW | المؤلف | TL-VDB | حقول Memory Schema كاملة | المؤلف | **ترقية المعرفة (L4)** |
| 33 | Future Reuse | الذاكرة المعتمدة | فهارس RAG محدثة | AG-KNW + AG-AUT | AG-SEC | TL-VDB | Recall@10 ≥ 0.8 على اختبارات الاسترجاع | المشاريع اللاحقة | — |
