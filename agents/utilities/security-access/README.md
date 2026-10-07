<!-- GENERATED from agents/_specs/AG-SEC.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل الأمن والصلاحيات — Security & Permissions Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-SEC` |
| الإدارة | DEP-10 |
| التصنيف | خدمي (Utility) |
| المستوى | L3-Professional |
| فئة النموذج | T2-standard |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | — |

## المهمة
فرض أقل الامتيازات وRBAC وتصنيف البيانات وحماية الأسرار، ومراجعة سجلات الوصول، والإبلاغ عن أي خرق أو انحراف عن مصفوفة الصلاحيات.

## المسؤوليات
- التحقق من مطابقة صلاحيات الوكلاء لـ permissions.yaml
- فحص الأسرار في المستودع والسجلات
- تصنيف البيانات ومراجعة الوصول إلى CONFIDENTIAL وAUTHOR_ONLY
- مراجعة دورية لسجلات الوصول وتقرير أمني

## المهارات
- `SKL-SECAUDIT` التدقيق الأمني

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-GITHUB` GitHub — platform

## بوابات الجودة
—

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-SEC-1 | حوادث أمنية | 0 |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
