# المرحلة الأولى — ٦. مخطط معمارية الوكلاء (Agent Architecture Diagram) — الإصدار الأول

## ٦.١ المعمارية الطبقية

```mermaid
flowchart TB
  subgraph L0["الطبقة ٠ — السلطة البشرية"]
    AUTH["المؤلف — L4<br/>الأطروحة · العنوان · الاستنتاجات · النشر"]
  end
  subgraph L1["الطبقة ١ — الحوكمة والضمان"]
    COUN["مجلس الوكلاء — L3"]
    SUPS["المشرفون الخمسة — L2<br/>QG1 · QG2 · QG4 · QG5 · QG6/7"]
  end
  subgraph L2["الطبقة ٢ — التنسيق"]
    ORC["AG-ORC المنسق<br/>تصنيف · اختيار · سير عمل · حالة · بوابات · تسليم"]
    DIR["AG-DIR — برامج ومحفظة"]
  end
  subgraph L3["الطبقة ٣ — الإنتاج المعرفي"]
    direction LR
    P1["التأطير والأدلة<br/>RQA · DSC · SRC · LRV"]
    P2["النظرية والمنهج<br/>THR · MTH · DAT · POL · CUL"]
    P3["التأليف<br/>BKA · WRT · TRN · TAH"]
    P4["الضمان العلمي<br/>EVA · PRV · RED · INT"]
    P5["التحرير والإنتاج<br/>SED · ARE · VIS · PUB"]
    P1 --> P2 --> P3 --> P4 --> P5
    P4 -. CHALLENGE / CORRECTION .-> P3
  end
  subgraph L4["الطبقة ٤ — المعرفة والخدمات"]
    KNW["AG-KNW المعرفة"] ; WCH["AG-WCH الرصد"] ; VCS["AG-VCS الإصدارات"] ; AUT["AG-AUT الأتمتة"] ; SEC["AG-SEC الأمن"] ; CST["AG-CST الكلفة"]
  end
  subgraph L5["الطبقة ٥ — البنية التقنية"]
    MEM[("الذاكرة ٦ طبقات + مخازن العمل")] ; TOOLS["سجل الأدوات ٢٦"] ; SK["سجل المهارات ٤٣"] ; MAL["Model Adapter Layer<br/>Anthropic · OpenAI · Google · Local · Manual"] ; LOG[("Audit · Cost · Messages")]
  end
  AUTH --> COUN --> ORC
  AUTH --> SUPS
  ORC --> P1
  SUPS -. APPROVAL / REJECT .-> L3
  P5 --> KNW
  WCH --> P1
  L3 --> MAL
  L3 --> MEM
  L3 --> LOG
  classDef h fill:#B8860B,color:#fff,stroke:#1F4E79,stroke-width:2px;
  class AUTH h;
```

## ٦.٢ تدفق التحكم والبيانات

| القناة | النوع | المخطط | الحامل |
|---|---|---|---|
| المهام | TASK → RESULT | `message.schema.json` | `projects/<PID>/messages/messages.jsonl` |
| التسليم | HANDOFF | `handoff.schema.json` | `messages/handoffs.jsonl` |
| الاعتراض | CHALLENGE / CORRECTION (بدليل إلزامي) | `message.schema.json` | idem |
| الاعتماد | APPROVAL / REJECT | `gate_decision.schema.json` | `reviews/gate_*.yaml` |
| التصعيد | ESCALATION | `message.schema.json` | idem + Decision Brief |
| القرارات | DC-xxx | `decisions.yaml` | المشروع |
| الأثر | Audit | `audit.schema.json` | `logs/audit.jsonl` |

## ٦.٣ قواعد المعمارية غير القابلة للكسر (مفروضة آلياً في `rkpos validate`)

1. لا وكيل يكتب في `MEM-INSTITUTIONAL` أو `MEM-AUTHOR`.
2. `MEM-SOURCE` يكتبه `AG-SRC` وحده.
3. لا وكيل يكتب في `ST-APPROVED`؛ النقل إليه أمر بشري (`rkpos complete --approved-file` بصفة `HUMAN-AUTHOR`).
4. المشرفون لا يكتبون في مخازن المحتوى (`ST-DRAFT/EDITED/APPROVED`).
5. المراجعون المستقلون (EVA · PRV · RED · SUP-*) على فئة `T4-independent`.
6. كل إرسال (X → Y) يقابله قبول عند Y (تبادلية التسليم).
7. كل خطوة L4 في سير العمل تحمل `human_approval: true`؛ وQG0 وQG6 من مستوى L4.
8. الملفات المولدة مطابقة للمصدر `agents/_specs/`.
