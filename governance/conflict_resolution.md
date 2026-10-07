# بروتوكول حل النزاع بين الوكلاء

سير العمل التنفيذي: [`workflows/WF-CONFLICT-RESOLUTION.yaml`](../workflows/WF-CONFLICT-RESOLUTION.yaml) — القالب: [`templates/dispute_record.template.yaml`](../templates/dispute_record.template.yaml)

| الخطوة | الفاعل | الإجراء | المخرج |
|---|---|---|---|
| ١ تسجيل الخلاف | AG-ORC | فتح `dispute_record` بموضوع محدد | DSP-xxxx |
| ٢ إرفاق الأدلة | الطرفان | كل طرف يقدم موقفه وأدلته (رسائل بدليل إلزامي) | position_a / position_b |
| ٣ الإحالة إلى المشرف المختص | AG-ORC | منهج ← SUP-MTH؛ أدلة ← SUP-EVD؛ تحرير ← SUP-EDT؛ نزاهة ← SUP-INT؛ إخراج ← SUP-PUB | supervisor_ruling (L2) |
| ٤ المجلس | AG-COUNCIL | إن لم يُحسم أو طُعن في الحكم | council_ruling (L3) |
| ٥ المؤلف | HUMAN-AUTHOR | كل خلاف جوهري (يمس الأطروحة/الاستنتاجات/الهيكل) | DC-xxx (L4) |

**قواعد:**
- عند التعارض يُغلَّب انضباط المصادر والصدق المعرفي على كل اعتبار.
- لا يحسم المنتج نزاعاً حول مخرجه.
- الحكم يُسجل في `MEM-EDITORIAL` سابقةً مرشحة (عبر ST-KB-CANDIDATES) إن كان قابلاً للتعميم.
