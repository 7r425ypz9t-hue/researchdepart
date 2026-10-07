from rkpos import stylometry as S

FLOWING = ("كانت المدينة تستيقظ على صوت البحر، والباعة يفتحون دكاكينهم، والأطفال يركضون بين السكيك، "
           "ولا أحد يسأل عن الوقت، فالوقت كان يمضي على مهل كأنه ماء يتسرب بين الأصابع، "
           "ونحن نحمل حكاياتنا من بيت إلى بيت، ونعرف أن الثقافة ليست ترفاً بل هي طريقة العيش نفسها. ") * 6
CHOPPY = ("المقصود: الثقافة مهمة. مثال: المهرجان. النتيجة: نحتاج خطة. وهذا يعني أن العمل ضروري. "
          "الفجوة الأولى: غياب البيانات. ") * 10


def test_profile_separates_flowing_from_template_prose():
    f, c = S.profile(FLOWING), S.profile(CHOPPY)
    assert f["sentence_len"]["mean"] > 3 * c["sentence_len"]["mean"]
    assert f["comma_period_ratio"] > c["comma_period_ratio"]
    assert c["template_markers_per_1k"] > 0 and f["template_markers_per_1k"] == 0
    assert c["explanatory_per_1k"] > f["explanatory_per_1k"]


def test_diacritics_do_not_split_words():
    p = S.profile("الصداقةُ علاقةٌ بين اثنينِ، لكنّ مصيرها يحسمه طرفٌ ثالثٌ في الغالبِ. " * 5)
    assert p["words"] == 5 * 11


def test_distance_zero_against_itself():
    p = S.profile(FLOWING)
    assert all(v in (0.0, None) for v in S.distance(p, p).values())


def test_missing_reference_is_none():
    assert S.load_reference("no-such-register") is None


def test_pole_classifies_by_structure():
    author, assisted = S.profile(FLOWING), S.profile(CHOPPY)
    assert S.pole(S.profile(FLOWING), author, assisted)["closer_to"] == "author"
    assert S.pole(S.profile(CHOPPY), author, assisted)["closer_to"] == "assisted"


def test_style_contract_least_privilege(tmp_path, monkeypatch):
    from rkpos import knowledge as K, runner
    f = tmp_path / "items.jsonl"
    import json
    rows = [{"Memory_ID": "MEM-ESSAY-000001", "Type": "style_rule", "Version": 2, "Approved_By": "HUMAN-AUTHOR",
             "Tags": ["essay"], "Content": "ملمح معتمد"},
            {"Memory_ID": "MEM-ESSAY-000099", "Type": "style_rule", "Version": 1, "Approved_By": None,
             "Tags": ["essay"], "Content": "مرشّح غير معتمد"}]
    f.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    monkeypatch.setattr(K, "LAYER_FILES", {**K.LAYER_FILES, "MEM-AUTHOR": f})
    wrt = runner.compose_system_prompt("AG-WRT", "essay")
    assert "ملمح معتمد" in wrt and "مرشّح غير معتمد" not in wrt and runner.AUTHOR_ONLY_BEGIN in wrt
    assert "ملمح معتمد" not in runner.compose_system_prompt("AG-PUB", "essay")      # لا يقرأ MEM-AUTHOR
    assert "ملمح معتمد" not in runner.compose_system_prompt("AG-WRT", "academic")   # سجلّ آخر
