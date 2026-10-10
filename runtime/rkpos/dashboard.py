"""لوحة القيادة — HTML ثابت يُولَّد من حالات المشاريع وسجل الكلفة (القسم 47)."""
from __future__ import annotations
import html
import json

import yaml

from . import cost as C
from .paths import PROJECTS, CONFIG, ROOT
from .verify import sources as SRC


def collect() -> list[dict]:
    rows = []
    for p in sorted(PROJECTS.glob("RKP-*")):
        if not (p / "state.yaml").exists():
            continue
        st = yaml.safe_load((p / "state.yaml").read_text(encoding="utf-8"))
        mf = yaml.safe_load((p / "manifest.yaml").read_text(encoding="utf-8"))
        srcs = SRC.load(p / "research/sources.jsonl")
        claims = [l for l in (p / "evidence/claims.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()] if (p / "evidence/claims.jsonl").exists() else []
        spent = C.report(mf["project_id"])["total_usd"]
        rows.append({"id": mf["project_id"], "title": mf["title"], "type": mf["project_type"], "stage": st["STATE"],
                     "step": st.get("STAGE_ID"), "pct": st.get("COMPLETION_PCT", 0), "agent": st["CURRENT_AGENT"],
                     "gate": (st.get("QUALITY_GATE") or {}).get("current"), "gate_status": (st.get("QUALITY_GATE") or {}).get("status"),
                     "issues": st.get("OPEN_ISSUES", 0), "blockers": st.get("BLOCKERS", []),
                     "sources": len(srcs), "verified": sum(1 for s in srcs if s["Verification_Status"] == "VERIFIED"),
                     "claims": len(claims), "cost": spent, "budget": mf.get("budget_usd"), "deadline": st.get("DEADLINE"),
                     "pending": st.get("PENDING_HUMAN_DECISIONS", []), "next": st["NEXT_ACTION"]})
    return rows


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
.next{{border-top:1px dashed var(--muted);padding-top:8px}} .pending{{color:var(--accent)}} .blocker{{color:#B03A2E}}
</style></head><body>
<div class="top"><h1>باحث — لوحة القيادة البحثية</h1>
<div class="kpis"><span>المشاريع: {len(rows)}</span><span>قرارات بانتظار المؤلف: {pending_total}</span>
<span>الكلفة الإجمالية: {sum(r['cost'] for r in rows):.2f} USD</span></div></div>
<main>{cards}</main></body></html>"""


def build(out=None):
    out = out or ROOT / "publishing/dashboard/index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(collect()), encoding="utf-8")
    return out
