"""لوحة القيادة — HTML ثابت يُولَّد من حالات المشاريع وسجل الكلفة (القسم 47)، ومؤشرات المؤسسة بخط الأساس.

قاعدة خط الأساس: لا تُعتمد مستهدفات رقمية قبل تأسيس خط أساس تجريبي. تُعرض كل قيمة بحالها،
ويُثبَّت أول قياس خطَّ أساس بقرار من المؤلف (HUMAN-AUTHOR، مستوى L4)، ثم تُقارن القيم اللاحقة به.
"""
from __future__ import annotations
import html
import json

import yaml

from . import cost as C
from .ids import now_iso
from .paths import PROJECTS, CONFIG, ROOT, LOGS
from .verify import claims as CL, sources as SRC

BASELINE_NOTE = "لا تُعتمد مستهدفات رقمية قبل تأسيس خط أساس تجريبي"
KPI_DEFS = [   # (المفتاح، التسمية، الوحدة، الاتجاه المرغوب: 1 الأعلى أفضل، -1 الأدنى أفضل، 0 محايد)
    ("projects", "المشاريع", "", 0),
    ("active", "المشاريع النشطة", "", 0),
    ("sources_verified", "نسبة المصادر المتحقق منها", "%", 1),
    ("claims", "الادعاءات المسجلة", "", 0),
    ("independent_avg", "متوسط الأصول المستقلة لكل ادعاء", "", 1),
    ("weak_established", "ادعاءات معتمدة على الصحافة وحدها أو على أصل واحد", "", -1),
    ("pending", "قرارات بانتظار المؤلف", "", -1),
    ("cost", "الكلفة الإجمالية", "USD", -1),
    ("vault_integrity", "سلامة الأصول الرقمية في الخزنة", "%", 1),
]


def collect() -> list[dict]:
    rows = []
    for p in sorted(PROJECTS.glob("RKP-*")):
        if not (p / "state.yaml").exists():
            continue
        st = yaml.safe_load((p / "state.yaml").read_text(encoding="utf-8"))
        mf = yaml.safe_load((p / "manifest.yaml").read_text(encoding="utf-8"))
        srcs = SRC.load(p / "research/sources.jsonl")
        claims = CL.load_ledger(p / "evidence/claims.jsonl")
        tri = CL.triangulate(claims, srcs + SRC.load())["summary"]
        spent = C.report(mf["project_id"])["total_usd"]
        rows.append({"id": mf["project_id"], "title": mf["title"], "type": mf["project_type"], "stage": st["STATE"],
                     "step": st.get("STAGE_ID"), "pct": st.get("COMPLETION_PCT", 0), "agent": st["CURRENT_AGENT"],
                     "gate": (st.get("QUALITY_GATE") or {}).get("current"), "gate_status": (st.get("QUALITY_GATE") or {}).get("status"),
                     "issues": st.get("OPEN_ISSUES", 0), "blockers": st.get("BLOCKERS", []),
                     "sources": len(srcs), "verified": sum(1 for s in srcs if s["Verification_Status"] == "VERIFIED"),
                     "claims": len(claims), "triangulation": tri, "cost": spent, "budget": mf.get("budget_usd"), "deadline": st.get("DEADLINE"),
                     "pending": st.get("PENDING_HUMAN_DECISIONS", []), "next": st["NEXT_ACTION"]})
    return rows


def _pct(a, b):
    return round(100 * a / b, 1) if b else None


def baseline_path():
    return LOGS / "kpi_baseline.json"


def baseline() -> dict | None:
    p = baseline_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def kpi_values(rows: list[dict]) -> dict:
    from . import vault
    srcs = sum(r["sources"] for r in rows)
    claims = sum(r["claims"] for r in rows)
    tri = [r.get("triangulation") or {} for r in rows]
    return {"projects": len(rows), "active": sum(1 for r in rows if r["stage"] != "CLOSED"),
            "sources_verified": _pct(sum(r["verified"] for r in rows), srcs), "claims": claims,
            "independent_avg": round(sum(t.get("independent_avg", 0) * r["claims"] for t, r in zip(tri, rows)) / claims, 2) if claims else None,
            "weak_established": sum(t.get("press_only_established", 0) + t.get("single_origin_established", 0) for t in tri),
            "pending": sum(len(r["pending"]) for r in rows), "cost": round(sum(r["cost"] for r in rows), 2),
            "vault_integrity": vault.summary()["integrity_pct"]}


def kpis(rows: list[dict] | None = None) -> dict:
    """مؤشرات المؤسسة بقيمها الحالية، ومقارنتها بخط الأساس إن ثُبِّت؛ وإلا فملاحظة القاعدة."""
    rows = collect() if rows is None else rows
    vals, base = kpi_values(rows), baseline()
    bv = (base or {}).get("values", {})
    items = []
    for key, label, unit, better in KPI_DEFS:
        v, b = vals.get(key), bv.get(key)
        delta = round(v - b, 2) if isinstance(v, (int, float)) and isinstance(b, (int, float)) else None
        trend = None if delta is None or delta == 0 or better == 0 else ("up" if delta * better > 0 else "down")
        items.append({"key": key, "label": label, "unit": unit, "value": v, "baseline": b, "delta": delta, "trend": trend})
    return {"items": items, "baseline_set": bool(base), "baseline_at": (base or {}).get("at"),
            "baseline_by": (base or {}).get("by"), "baseline_decision": (base or {}).get("decision"),
            "note": None if base else BASELINE_NOTE}


def set_baseline(actor: str, decision: str = "") -> dict:
    """تثبيت خط الأساس: قرار بشري للمؤلف وحده (L4)، يُسجَّل في سجل التدقيق."""
    from . import audit
    if actor != "HUMAN-AUTHOR":
        raise PermissionError("تثبيت خط الأساس قرار للمؤلف وحده (HUMAN-AUTHOR)")
    b = {"at": now_iso(), "by": actor, "decision": decision or "تثبيت خط الأساس التجريبي للمؤشرات",
         "values": kpi_values(collect())}
    p = baseline_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(b, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit.log(actor, "kpi_baseline", None, files_changed=[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name],
              decision=b["decision"], decision_level="L4", approval=actor)
    return b


def _fmt(v, unit=""):
    if v is None:
        return "—"
    return f"{v}{'%' if unit == '%' else (' ' + unit if unit else '')}"


def render_kpis(k: dict) -> str:
    e = html.escape
    rows = "".join(f"<tr><td>{e(i['label'])}</td><td>{e(_fmt(i['value'], i['unit']))}</td>"
                   + (f"<td>{e(_fmt(i['baseline'], i['unit']))}</td><td class=\"{i['trend'] or ''}\">"
                      f"{'—' if i['delta'] is None else ('+' if i['delta'] > 0 else '') + str(i['delta'])}</td>" if k["baseline_set"] else "")
                   + "</tr>" for i in k["items"])
    head = "<tr><th>المؤشر</th><th>القيمة الحالية</th>" + ("<th>خط الأساس</th><th>الفرق</th>" if k["baseline_set"] else "") + "</tr>"
    note = (f'<p class="pending">{e(k["note"])}</p>' if k["note"] else
            f'<p class="muted">خط الأساس مثبّت في {e(str(k["baseline_at"]))} بقرار {e(str(k["baseline_by"]))}.</p>')
    return f'<section class="kpi-sec"><h2>مؤشرات المؤسسة</h2>{note}<table>{head}{rows}</table></section>'


def render(rows: list[dict]) -> str:
    brand = yaml.safe_load((CONFIG / "brand.yaml").read_text(encoding="utf-8"))["colors"]
    e = html.escape
    cards = "".join(f"""
<article class="card">
  <header><span class="pid">{e(r['id'])}</span><span class="type">{e(r['type'])}</span></header>
  <h2>{e(r['title'])}</h2>
  <div class="bar"><span style="width:{r['pct']}%"></span></div>
  <dl>
    <dt>المرحلة</dt><dd>{e(str(r['stage']))} · {e(str(r['step']))}</dd>
    <dt>الوكيل الحالي</dt><dd>{e(r['agent'])}</dd>
    <dt>بوابة الجودة</dt><dd>{e(str(r['gate']))} — {e(str(r['gate_status']))}</dd>
    <dt>المصادر المتحققة</dt><dd>{r['verified']} / {r['sources']}</dd>
    <dt>الادعاءات المسجلة</dt><dd>{r['claims']}</dd>
    <dt>الكلفة</dt><dd>{r['cost']:.2f} / {r['budget'] or '—'} USD</dd>
    <dt>الموعد</dt><dd>{e(str(r['deadline'] or '—'))}</dd>
    <dt>مشكلات مفتوحة</dt><dd>{r['issues']}</dd>
  </dl>
  <p class="next"><b>التالي:</b> {e(r['next'])}</p>
  {''.join(f'<p class="pending">⏳ قرار للمؤلف: {e(x)}</p>' for x in r['pending'])}
  {''.join(f'<p class="blocker">⛔ {e(x)}</p>' for x in r['blockers'])}
</article>""" for r in rows) or "<p>لا مشاريع نشطة بعد. ابدأ بـ <code>rkpos new-project</code>.</p>"
    pending_total = sum(len(r["pending"]) for r in rows)
    return f"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>لوحة باحث</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{{--primary:{brand['primary']};--accent:{brand['accent']};--ink:{brand['ink']};--paper:{brand['paper']};--muted:{brand['muted']};--light:{brand['light']}}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--ink:#E8EEF4;--paper:#0F1B26;--light:#16283A;--muted:#9FB2C4}}}}
:root[data-theme="dark"]{{--ink:#E8EEF4;--paper:#0F1B26;--light:#16283A;--muted:#9FB2C4}}
body{{margin:0;font-family:'Noto Naskh Arabic',serif;background:var(--paper);color:var(--ink)}}
.top{{background:var(--primary);color:#fff;padding:20px 16px;border-bottom:4px solid var(--accent)}}
.top h1{{margin:0;font-size:1.5rem}} .kpis{{display:flex;gap:12px;flex-wrap:wrap;margin-top:8px}}
.kpis span{{background:rgba(255,255,255,.12);padding:4px 10px;border-radius:6px}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;padding:16px}}
.card{{background:var(--light);border-radius:10px;padding:16px;border-top:4px solid var(--primary)}}
.card header{{display:flex;justify-content:space-between;color:var(--muted);font-size:.85rem}}
.card h2{{font-size:1.15rem;margin:.4rem 0}} .pid{{color:var(--accent);font-weight:700}}
.bar{{height:8px;background:rgba(127,127,127,.25);border-radius:4px;overflow:hidden}} .bar span{{display:block;height:100%;background:var(--accent)}}
dl{{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;font-size:.92rem}} dt{{color:var(--muted)}} dd{{margin:0}}
.kpi-sec{{padding:16px}} .kpi-sec h2{{font-size:1.2rem;margin:0 0 8px}} .kpi-sec table{{width:100%;border-collapse:collapse;background:var(--light)}}
.kpi-sec td,.kpi-sec th{{padding:6px 10px;border-bottom:1px solid rgba(127,127,127,.25);text-align:start}} .up{{color:#2e7d32}} .down{{color:#B03A2E}} .muted{{color:var(--muted)}}
.next{{border-top:1px dashed var(--muted);padding-top:8px}} .pending{{color:var(--accent)}} .blocker{{color:#B03A2E}}
</style></head><body>
<div class="top"><h1>باحث — لوحة القيادة البحثية</h1>
<div class="kpis"><span>المشاريع: {len(rows)}</span><span>قرارات بانتظار المؤلف: {pending_total}</span>
<span>الكلفة الإجمالية: {sum(r['cost'] for r in rows):.2f} USD</span></div></div>
{render_kpis(kpis(rows))}
<main>{cards}</main></body></html>"""


def build(out=None):
    out = out or ROOT / "publishing/dashboard/index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(collect()), encoding="utf-8")
    return out
