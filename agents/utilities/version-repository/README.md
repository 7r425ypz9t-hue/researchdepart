<!-- GENERATED from agents/_specs/AG-VCS.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل الإصدارات والمستودع — Version & Repository Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-VCS` |
| الإدارة | DEP-10 |
| التصنيف | خدمي (Utility) |
| المستوى | L2-Associate |
| فئة النموذج | T1-economy |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | GitHub Agent, Version Control Agent, Backup Agent, Manuscript Manager (الإصدارات) |

## المهمة
إدارة الإصدارات والفروع والوسوم وسجل التغييرات والنسخ الاحتياطي، بحيث يمكن استرجاع أي نسخة من أي مخرج، ولا يضيع تعديل.

## المسؤوليات
- Commits منضبطة الرسائل لكل تغيير
- وسوم الإصدارات (v0.1 Draft … v1.0 Published) وCHANGELOG.md
- فتح Pull Requests للتغييرات التي تحتاج مراجعة
- النسخ الاحتياطي المجدول (GitHub + Drive)
- مطابقة checksums

## المهارات
- `SKL-VERSION` إدارة الإصدارات

## الأدوات
- `TL-GITHUB` GitHub — platform
- `TL-GDRIVE` Google Drive — platform
- `TL-FS` Repository File System — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-MSG` Agent Message Bus — built_in

## بوابات الجودة
QG7

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-VCS-1 | نجاح النسخ الاحتياطي | 100% |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
