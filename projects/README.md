# المشاريع

كل مشروع يُنشأ بالأمر:

```bash
rkpos new-project "عنوان العمل" --type intellectual_book --domain cultural_governance --model A
```

فيتولد `projects/RKP-YYYY-NNNN/` وفيه: `manifest.yaml` · `state.yaml` · `plan.yaml` · `decisions.yaml` · `outline.yaml` · `CHANGELOG.md`
ومجلدات: `research/ evidence/ data/ manuscript/{drafts,edited,approved}/ reviews/ messages/ runs/ archive/ watch/ figures/ tables/`.

قالب البيان الكامل في [templates/project_manifest.template.yaml](../templates/project_manifest.template.yaml).
