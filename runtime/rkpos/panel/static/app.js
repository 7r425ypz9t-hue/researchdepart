/* لوحة تحكم «مِداد» — واجهة محلية. كل النصوص تُدرج عبر textContent (لا innerHTML لبيانات). */
"use strict";

// ---------- الرمز والاتصال ----------
(function () {
  const m = location.hash.match(/t=([\w-]+)/);
  if (m) { sessionStorage.setItem("rkpos-token", m[1]); history.replaceState(null, "", location.pathname); }
})();
const TOKEN = sessionStorage.getItem("rkpos-token") || "";
const store = {
  get(k, d) { try { return localStorage.getItem(k) ?? d; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* تفضيل محلي فقط */ } },
};

async function api(name, body, quiet) {
  const opt = { headers: { "X-Rkpos-Token": TOKEN } };
  let url = "/api/" + name;
  if (body !== undefined && body !== null && body.__get) {
    const q = new URLSearchParams(Object.entries(body).filter(([k, v]) => k !== "__get" && v !== undefined && v !== null && v !== ""));
    url += "?" + q.toString();
  } else if (body !== undefined) {
    opt.method = "POST"; opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body);
  }
  const r = await fetch(url, opt);
  let j = {};
  try { j = await r.json(); } catch (e) { j = { ok: false, error: "استجابة غير مفهومة" }; }
  if (r.status === 401) { toast("انتهت صلاحية الجلسة: أعد فتح اللوحة من الأيقونة", true); throw new Error("token"); }
  if (!j.ok) { if (!quiet) toast(j.error || "خطأ", true); throw new Error(j.error); }
  return j.data;
}
const G = (name, q) => api(name, Object.assign({ __get: true }, q || {}));

// ---------- أدوات DOM ----------
function h(tag, props, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "class") el.className = v;
    else if (k === "value") el.value = v;
    else if (k === "checked") el.checked = !!v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const c of kids.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}
const $ = (s) => document.querySelector(s);
const main = () => $("#main");
function set(...nodes) { const m = main(); m.replaceChildren(...nodes); window.scrollTo(0, 0); }
function toast(msg, bad) {
  const t = $("#toast"); t.textContent = msg; t.className = "toast" + (bad ? " bad" : ""); t.hidden = false;
  clearTimeout(t._t); t._t = setTimeout(() => (t.hidden = true), bad ? 7000 : 3500);
}
async function busy(text, fn) {
  $("#busy-text").textContent = text; $("#busy").hidden = false;
  try { return await fn(); } finally { $("#busy").hidden = true; }
}
const pre = (text, code) => h("pre", { class: "out" + (code ? " code" : "") }, text);
const json = (o) => pre(JSON.stringify(o, null, 2), true);
const pill = (t, cls) => h("span", { class: "pill " + (cls || "") }, t);
const btn = (t, fn, cls) => h("button", { class: "btn " + (cls || ""), type: "button", onclick: fn }, t);
const field = (label, input, wide) => h("label", { class: wide ? "wide" : "" }, label, input);
const sel = (id, opts, val) => h("select", { id }, opts.map(([v, t]) => h("option", { value: v, selected: v === val }, t)));
const val = (id) => { const e = document.getElementById(id); return e ? (e.type === "checkbox" ? e.checked : e.value.trim()) : ""; };
const engine = () => $("#engine").value;
const ENGINE_LABEL = { manual: "يدوي", claude_code: "Claude Code", api: "API", auto: "تلقائي" };
const STATUS_CLS = { DONE: "ok", AWAITING_AUTHOR: "gold", IN_REVIEW: "warn", IN_PROGRESS: "warn", REJECTED: "bad" };
const REGISTERS = [["", "— بلا سجلّ —"], ["essay", "مقال (essay)"], ["narrative", "سرد (narrative)"], ["academic", "أكاديمي (academic)"]];
const TYPE_AR = { core: "أساسي", specialist: "متخصص", supervisory: "إشرافي", utility: "خدمي", on_demand: "عند الطلب" };
const PTYPE_AR = {
  intellectual_book: "كتاب فكري", academic_book: "كتاب أكاديمي", policy_study: "دراسة سياسات", systematic_review: "مراجعة منهجية",
  literature_review: "مراجعة أدبيات", foresight_study: "دراسة استشرافية", critical_edition: "تحقيق تراثي", journal_article: "بحث محكّم",
  op_ed: "مقال رأي", strategic_report: "تقرير استراتيجي", translation: "ترجمة", re_edition: "إعادة إصدار",
  novel: "رواية", novella: "رواية قصيرة (نوفيلا)", short_story: "قصة قصيرة", essay_collection: "مجموعة مقالات فكرية",
};
const UNIT_STATUS_AR = { PLANNED: "مخطّطة", CARDED: "بطاقة جاهزة", DRAFTED: "مسودة الوكيل", REVISED: "عدّلها المؤلف", APPROVED: "معتمدة" };
const UNIT_STATUS_CLS = { APPROVED: "ok", REVISED: "gold", DRAFTED: "warn", CARDED: "" };
let GEN = null;
async function genresData() { GEN = GEN || await G("genres"); return GEN; }
async function downloadRaw(path) {
  const r = await fetch("/api/raw?path=" + encodeURIComponent(path), { headers: { "X-Rkpos-Token": TOKEN } });
  if (!r.ok) return toast("تعذّر التنزيل", true);
  const a = h("a", { href: URL.createObjectURL(await r.blob()), download: path.split("/").pop() });
  document.body.append(a); a.click(); a.remove();
}
const authorBox = (id) => h("label", { class: "confirm" }, h("input", { type: "checkbox", id }), " أقرّ بصفتي المؤلف (قرار L4)");

async function copyAndOpen(text) {
  try { await navigator.clipboard.writeText(text); toast("نُسخ البرومبت؛ الصقه في Claude ثم أعد المخرج إلى اللوحة"); }
  catch (e) { toast("تعذّر النسخ الآلي؛ انسخ النص يدوياً", true); }
  window.open("https://claude.ai/new", "_blank", "noopener");
}
function download(name, text) {
  const a = h("a", { href: URL.createObjectURL(new Blob([text], { type: "text/markdown" })), download: name });
  document.body.append(a); a.click(); a.remove();
}

// ---------- المحرّك ----------
let ENG = null;
async function refreshEngines(fresh) {
  ENG = await G("engines", fresh ? { fresh: 1 } : {});
  const e = $("#engine");
  e.value = store.get("rkpos-engine", ENG.claude_code ? "claude_code" : "manual");
  paintEngine();
}
function paintEngine() {
  const e = engine(), p = $("#engine-state");
  const keys = ENG ? Object.values(ENG.api_keys).some(Boolean) : false;
  const ready = e === "manual" || (e === "claude_code" && ENG.claude_code) || (e === "api" && keys) || e === "auto";
  const needLogin = (e === "claude_code" || e === "auto") && ENG && ENG.claude_code && ENG.claude_logged_in === false && !keys;
  p.textContent = needLogin ? "سجّلوا الدخول إلى Claude ←" : ready ? "جاهز" : "غير مهيأ — سيُستعمل اليدوي";
  p.className = "pill " + (needLogin ? "bad" : ready ? "ok" : "warn");
  p.style.cursor = needLogin ? "pointer" : "";
  p.onclick = needLogin ? () => go("settings") : null;
}
async function claudeLogin() {
  await api("claude_login", {});
  toast("فُتحت نافذة تسجيل الدخول: اتبعوا ما فيها في المتصفح، ثم اضغطوا «تحقق من الحالة»");
}
$("#engine").addEventListener("change", () => { store.set("rkpos-engine", engine()); paintEngine(); });

// ---------- عرض نتيجة تشغيل ----------
function runView(res, ctx) {
  const box = h("div", { class: "card" });
  const w = (res.warnings || []).map((x) => pill(x, "warn"));
  if (res.kind === "prompt.md" || (res.output == null && res.system)) {
    const text = res.text || `# SYSTEM\n\n${res.system}\n\n# USER\n\n${res.user}`;
    const out = h("textarea", { id: "paste-out", placeholder: "الصق هنا ردّ Claude ثم سجّله" });
    box.append(h("h3", {}, "حزمة البرومبت جاهزة (الوضع اليدوي)"), h("div", { class: "row" }, w),
      h("div", { class: "row" }, btn("انسخ وافتح Claude", () => copyAndOpen(text), "gold"),
        btn("تنزيل الحزمة", () => download("prompt.md", text), "ghost")),
      h("details", {}, h("summary", {}, "عرض الحزمة"), pre(text)));
    if (ctx && ctx.project && ctx.step) {
      box.append(h("h3", {}, "تسجيل المخرج"), out, h("div", { class: "row" }, btn("سجّل المخرج", async () => {
        if (!out.value.trim()) return toast("الصق المخرج أولاً", true);
        await api("record_output", { project: ctx.project, step: ctx.step, text: out.value });
        toast("سُجّل المخرج"); openProject(ctx.project);
      })));
    } else box.append(h("p", { class: "muted small" }, "مجلد التشغيل: " + (res.dir || res.path || "")));
  } else if (res.kind === "author_task.md") {
    box.append(h("h3", {}, "مهمة للمؤلف (L4)"), pre(res.text));
    if (ctx && ctx.project) box.append(btn("اعتماد الخطوة", () => completeForm(ctx.project, ctx.step), "gold"));
  } else {
    const text = res.text ?? res.output ?? "";
    box.append(h("h3", {}, "مخرج الوكيل"), h("div", { class: "row" }, w, res.model ? pill(res.model) : null,
      res.usd != null ? pill("$" + Number(res.usd).toFixed(4), "gold") : null),
      pre(text), h("div", { class: "row" },
        btn("نسخ", () => navigator.clipboard.writeText(text).then(() => toast("نُسخ")), "ghost"),
        btn("فحص المخطوطة", () => checkTextView(text, ctx && ctx.project)),
        btn("تنزيل", () => download("output.md", text), "ghost"),
        ctx && ctx.project && ctx.step ? btn("اعتماد الخطوة", () => completeForm(ctx.project, ctx.step, text), "gold") : null));
  }
  return box;
}

// ---------- الرئيسة ----------
async function home() {
  const o = await G("overview");
  const e = o.engines;
  set(
    h("h2", {}, "نظرة عامة"),
    h("div", { class: "grid" },
      h("div", { class: "card" }, h("div", { class: "kpi" }, o.agents), "وكيلاً معرّفاً"),
      h("div", { class: "card" }, h("div", { class: "kpi" }, o.workflows), "سير عمل"),
      h("div", { class: "card" }, h("div", { class: "kpi" }, o.projects.length), "مشروعاً"),
      h("div", { class: "card click", onclick: () => go("governance") }, h("div", { class: "kpi" }, o.candidates), "مرشّحاً للذاكرة بانتظار الاعتماد"),
      h("div", { class: "card" }, h("h4", {}, "المحرّكات"),
        h("div", {}, pill("Claude Code: " + (!e.claude_code ? "غير مثبت" : e.claude_logged_in === false ? "غير مسجّل الدخول" : "جاهز"),
          e.claude_code && e.claude_logged_in !== false ? "ok" : "warn"),
          e.claude_code && e.claude_logged_in === false ? btn("سجّلوا الدخول", claudeLogin, "sm gold") : null),
        h("div", {}, pill("مفتاح Anthropic: " + (e.api_keys.ANTHROPIC_API_KEY ? "موجود" : "غير موجود"), e.api_keys.ANTHROPIC_API_KEY ? "ok" : "")),
        h("div", {}, pill("الذاكرة الخاصة: " + (e.private_memory ? "مستعادة" : "غير موجودة"), e.private_memory ? "ok" : "bad")))),
    h("h2", {}, "إجراءات سريعة"),
    h("div", { class: "row" },
      btn("مشروع جديد", () => newProjectForm(), "gold"), btn("تفعيل وكيل", () => go("agents")),
      btn("فحص نص", () => go("tools")), btn("اعتماد مرشّحات الذاكرة", () => go("governance"), "ghost"),
      btn("فحص سلامة المنظومة", () => go("tools"), "ghost")),
    h("h2", {}, "بانتظار قراركم"),
    o.pending.length ? h("table", {}, h("tr", {}, h("th", {}, "المشروع"), h("th", {}, "المطلوب"), h("th", {}, "")),
      o.pending.map((p) => h("tr", {}, h("td", {}, p.project, h("br"), h("span", { class: "small muted" }, p.title)),
        h("td", {}, (p.items || []).join("، ") || p.next), h("td", {}, btn("افتح", () => openProject(p.project), "sm")))))
      : h("p", { class: "muted" }, "لا قرارات معلّقة."),
    h("h2", {}, "المشاريع"), projectsTable(o.projects),
  );
}
function projectsTable(rows) {
  if (!rows.length) return h("p", { class: "muted" }, "لا مشاريع بعد. ابدأ بـ«مشروع جديد».");
  return h("table", {}, h("tr", {}, ["المعرّف", "العنوان", "النوع", "المرحلة", "الإنجاز", "الإجراء التالي", ""].map((x) => h("th", {}, x))),
    rows.map((p) => h("tr", {}, h("td", {}, p.id), h("td", {}, p.title), h("td", {}, PTYPE_AR[p.type] || p.type),
      h("td", {}, pill(p.stage, STATUS_CLS[p.stage])), h("td", {}, (p.pct || 0) + "%"), h("td", { class: "small" }, p.next),
      h("td", {}, btn("افتح", () => openProject(p.id), "sm")))));
}

// ---------- المشاريع ----------
async function projects() {
  const o = await G("overview");
  set(h("h2", {}, "المشاريع"), h("div", { class: "row" }, btn("مشروع جديد", () => newProjectForm(), "gold")), projectsTable(o.projects));
}
async function newProjectForm(preGenre, preType) {
  const g = await genresData();
  let genre = preGenre || "intellectual", level = null;
  const typeBox = h("div"), levelBox = h("div", { class: "grid" }), sizeBox = h("div"), genreBox = h("div", { class: "grid" });
  const paintSize = () => {
    const gs = g.genres[genre];
    if (gs.max_words) { sizeBox.replaceChildren(h("p", { class: "muted" }, "سقف الطول " + gs.max_words + " كلمة.")); return; }
    const calc = h("span", { class: "pill gold" }, "—");
    const upd = () => { const p = +val("np-pages"), w = +val("np-wpp") || 250; calc.textContent = p ? (p * w).toLocaleString("ar") + " كلمة تقريباً" : "حدّدوا عدد الصفحات"; };
    sizeBox.replaceChildren(h("div", { class: "form" },
      field("عدد الصفحات المطلوب", h("input", { id: "np-pages", type: "number", min: 1, placeholder: "مثال: 200", oninput: upd })),
      field("كلمات الصفحة", h("input", { id: "np-wpp", type: "number", min: 100, value: g.levels.words_per_page_default, oninput: upd })),
      h("label", {}, "الحجم", calc)));
    upd();
  };
  const paintLevels = () => {
    const allowed = g.genres[genre].levels;
    if (!allowed.includes(level)) level = allowed.includes("staged") ? "staged" : allowed[0];
    levelBox.replaceChildren(...Object.entries(g.levels.levels).filter(([k]) => allowed.includes(k)).map(([k, L]) =>
      h("div", { class: "card click" + (k === level ? " sel" : ""), onclick: () => { level = k; paintLevels(); } },
        h("h4", {}, L.order + ". " + L.name_ar), h("p", { class: "small" }, L.summary))));
  };
  const paintTypes = () => {
    const types = g.genres[genre].project_types.concat(Object.keys(g.cross_genre));
    typeBox.replaceChildren(field("نوع المشروع", sel("np-type", types.map((t) => [t, PTYPE_AR[t] || t]), preType && types.includes(preType) ? preType : types[0])));
  };
  const paintGenres = () => {
    genreBox.replaceChildren(...Object.entries(g.genres).map(([k, G2]) =>
      h("div", { class: "card click" + (k === genre ? " sel" : ""), onclick: () => { genre = k; preType = null; paintAll(); } },
        h("h4", {}, G2.name_ar), h("p", { class: "small muted" }, G2.intellectual[0]),
        h("div", { class: "row" }, pill(G2.register), pill(G2.lead_agent, "gold")))));
  };
  const paintAll = () => { paintGenres(); paintTypes(); paintLevels(); paintSize(); };
  set(h("h2", {}, "مشروع جديد"),
    h("h3", {}, "١. الجنس"), genreBox,
    h("h3", {}, "٢. النوع والعنوان"), h("div", { class: "form" }, field("العنوان العامل", h("input", { id: "np-title" }), true)), typeBox,
    h("h3", {}, "٣. مستوى الإنتاج"), levelBox,
    h("h3", {}, "٤. الحجم"), sizeBox,
    h("details", {}, h("summary", {}, "خيارات متقدمة"),
      h("div", { class: "form" },
        field("نموذج التشغيل", sel("np-model", [["A", "A — خفيف"], ["B", "B — قياسي"], ["C", "C — موسّع"]], "A")),
        field("المجال", h("input", { id: "np-domain", placeholder: "cultural_policy" })),
        field("المخاطر", sel("np-risk", [["low", "منخفضة"], ["medium", "متوسطة"], ["high", "عالية"]], "medium")),
        field("متطلب الأدلة", sel("np-evidence", [["light", "خفيف"], ["standard", "قياسي"], ["high", "مرتفع"]], "standard")),
        field("جهة النشر المستهدفة", h("input", { id: "np-target" })),
        field("الموعد", h("input", { id: "np-deadline", type: "date" })),
        field("بيانات كمية؟", h("input", { id: "np-data", type: "checkbox" })))),
    h("div", { class: "row" }, btn("أنشئ المشروع", async () => {
      const r = await api("new_project", { title: val("np-title"), type: val("np-type"), genre, level, pages: val("np-pages"), wpp: val("np-wpp"),
        model: val("np-model"), domain: val("np-domain"), risk: val("np-risk"), evidence: val("np-evidence"), target: val("np-target"),
        deadline: val("np-deadline"), has_data: val("np-data") });
      toast("أُنشئ " + r.project_id + " — " + r.workflow); openProject(r.project_id);
    }, "gold"), btn("محاكاة اختيار الوكلاء", async () => {
      const r = await api("select", { type: val("np-type"), model: val("np-model"), domain: val("np-domain"), risk: val("np-risk"),
        evidence: val("np-evidence"), target: val("np-target"), has_data: val("np-data") });
      $("#np-sim").replaceChildren(json(r));
    }, "ghost")), h("div", { id: "np-sim" }));
  paintAll();
}

async function openProject(pid) {
  go("projects", true);
  const d = await G("project", { id: pid });
  const m = d.manifest, s = d.state, steps = d.plan.steps;
  const runBox = h("div", { id: "run-box" });
  set(
    h("h2", {}, m.title), h("div", { class: "row" }, pill(pid), pill(PTYPE_AR[m.project_type] || m.project_type), pill(m.workflow),
      pill("نموذج " + m.operating_model), pill(s.STATE, STATUS_CLS[s.STATE]), pill((s.COMPLETION_PCT || 0) + "%", "gold")),
    h("div", { class: "card" }, h("b", {}, "الإجراء التالي: "), s.NEXT_ACTION, h("br"),
      h("span", { class: "muted small" }, "الوكيل الحالي: " + s.CURRENT_AGENT + " — بانتظار: " + (s.WAITING_FOR || "—")),
      (s.BLOCKERS || []).length ? h("div", {}, pill("عوائق: " + s.BLOCKERS.join("، "), "bad")) : null),
    h("div", { class: "row" },
      steps.some((x) => x.status !== "DONE") ? btn("شغّل الخطوة التالية بالمحرّك المختار", () => runStep(pid, null), "gold") : pill("اكتملت الخطة", "ok"),
      btn("افتح مجلد المشروع", () => api("open_folder", { path: "projects/" + pid }), "ghost"),
      btn("تحديث", () => openProject(pid), "ghost")),
    h("div", { id: "book-box" }),
    runBox,
    h("h3", {}, "الخطة (الحوكمة)"),
    h("table", {}, h("tr", {}, ["الخطوة", "الوكيل", "المهمة", "المستوى", "البوابة", "الحالة", "الإجراءات"].map((x) => h("th", {}, x))),
      steps.map((st) => h("tr", {}, h("td", {}, st.id), h("td", {}, st.assigned_agent || st.agent), h("td", { class: "small" }, st.task),
        h("td", {}, st.decision_level || ""), h("td", {}, st.gate || ""), h("td", {}, pill(st.status, STATUS_CLS[st.status])),
        h("td", {}, h("div", { class: "row" },
          st.status !== "DONE" ? btn("تشغيل", () => runStep(pid, st.id), "sm") : null,
          st.status !== "DONE" ? btn("تسجيل مخرج", () => recordForm(pid, st.id), "sm ghost") : null,
          st.status !== "DONE" ? btn("اعتماد", () => completeForm(pid, st.id), "sm gold") : null))))),
    h("h3", {}, "التشغيلات والملفات"),
    d.runs.length ? h("table", {}, d.runs.map((r) => h("tr", {}, h("td", {}, r.id),
      h("td", {}, h("div", { class: "row" }, r.files.map((f) => btn(f, () => showFile(`projects/${pid}/runs/${r.id}/${f}`, pid, r.id), "sm ghost")))))))
      : h("p", { class: "muted" }, "لا تشغيلات بعد."),
    h("details", {}, h("summary", {}, "ملفات المشروع (" + d.files.length + ")"),
      h("div", { class: "list" }, d.files.map((f) => h("div", { class: "item small", onclick: () => showFile(f, pid) }, f)))),
    h("h3", {}, "القرارات"),
    d.decisions.length ? h("table", {}, h("tr", {}, ["المعرّف", "الخطوة", "المستوى", "القرار", "المعتمِد"].map((x) => h("th", {}, x))),
      d.decisions.map((x) => h("tr", {}, h("td", {}, x.id), h("td", {}, x.step), h("td", {}, x.level || ""), h("td", {}, x.decision), h("td", {}, x.approved_by))))
      : h("p", { class: "muted" }, "لا قرارات."),
    h("h3", {}, "الكلفة"), h("p", {}, "$" + (d.cost.total_usd || 0).toFixed(4) + (m.budget_usd ? " من ميزانية $" + m.budget_usd : "")),
  );
  renderBook(pid);
}
async function runStep(pid, step) {
  const e = engine();
  const res = await busy(e === "manual" ? "تُعدّ حزمة البرومبت…" : "يعمل الوكيل عبر " + ENGINE_LABEL[e] + "… قد يستغرق دقائق", () =>
    api("run_step", { project: pid, step, engine: e }));
  const stepId = step || (res.path.split("/runs/")[1] || "").split("/")[0];
  await openProject(pid);
  $("#run-box").replaceChildren(runView(res, { project: pid, step: stepId }));
  $("#run-box").scrollIntoView({ behavior: "smooth" });
}
function recordForm(pid, step) {
  const t = h("textarea", { placeholder: "الصق مخرج الوكيل هنا" });
  $("#run-box").replaceChildren(h("div", { class: "card" }, h("h3", {}, "تسجيل مخرج " + step), t,
    h("div", { class: "row" }, btn("سجّل", async () => {
      await api("record_output", { project: pid, step, text: t.value }); toast("سُجّل"); openProject(pid);
    }, "gold"))));
  $("#run-box").scrollIntoView({ behavior: "smooth" });
}
async function completeForm(pid, step, approvedText) {
  if (!$("#run-box")) await openProject(pid);
  const box = h("div", { class: "card" }, h("h3", {}, "اعتماد الخطوة " + step),
    h("div", { class: "form" },
      field("الصفة", sel("cf-actor", [["HUMAN-AUTHOR", "المؤلف"], ["AG-ORC", "المنسق"], ["AG-DIR", "مدير الإدارة"],
        ["AG-SUP-INT", "مشرف النزاهة"], ["AG-SUP-EVD", "مشرف الأدلة"], ["AG-SUP-EDT", "مشرف التحرير"]], "HUMAN-AUTHOR")),
      field("نص القرار", h("input", { id: "cf-decision", placeholder: "مثال: اعتماد المسودة بعد التحرير" }), true),
      field("النص المعتمد (اختياري — يُنقل إلى manuscript/approved)", h("textarea", { id: "cf-text" }, approvedText || ""), true),
      field("اسم الملف المعتمد", h("input", { id: "cf-name", placeholder: step + "_approved.md" }))),
    h("div", { class: "row" }, authorBox("cf-confirm"), btn("اعتمد", async () => {
      const r = await api("complete", { project: pid, step, actor: val("cf-actor"), decision: val("cf-decision"),
        approved_text: $("#cf-text").value.trim() || null, approved_name: val("cf-name"), confirm_author: val("cf-confirm") });
      toast(r.decision && r.decision.id ? "سُجّل القرار " + r.decision.id : "أُغلقت الخطوة"); openProject(pid);
    }, "gold")),
    h("p", { class: "muted small" }, "خطوات L4 لا يغلقها إلا المؤلف، ونقل النص إلى المخطوط المعتمد للمؤلف وحده."));
  $("#run-box").replaceChildren(box); $("#run-box").scrollIntoView({ behavior: "smooth" });
}
async function showFile(path, pid, runId) {
  const f = await G("file", { path });
  const box = $("#run-box") || main();
  if (f.binary) { box.replaceChildren(h("div", { class: "card" }, path + " — ملف ثنائي (" + f.size + " بايت)", btn("افتح المجلد", () => api("open_folder", { path }), "sm ghost"))); return; }
  const name = path.split("/").pop();
  const kind = name === "prompt.md" ? "prompt.md" : name === "author_task.md" ? "author_task.md" : "output.md";
  box.replaceChildren(name.endsWith(".md") && runId ? runView({ kind, text: f.text, path }, { project: pid, step: runId })
    : h("div", { class: "card" }, h("h3", {}, path), pre(f.text), h("div", { class: "row" },
      btn("فحص النص", () => checkTextView(f.text, pid), "sm"), btn("افتح المجلد", () => api("open_folder", { path }), "sm ghost"))));
  box.scrollIntoView({ behavior: "smooth" });
}

// ---------- الوكلاء ----------
let AGENTS = null;
async function agentsView() {
  AGENTS = AGENTS || await G("agents");
  const grid = h("div", { class: "grid" });
  const paint = () => {
    const q = val("ag-q"), t = val("ag-type"), dep = val("ag-dep"), mvp = val("ag-mvp");
    grid.replaceChildren(...AGENTS.items.filter((a) => (!t || a.type === t) && (!dep || a.department === dep) && (!mvp || a.mvp) &&
      (!q || (a.id + a.name_ar + a.name_en + a.mission).toLowerCase().includes(q.toLowerCase())))
      .map((a) => h("div", { class: "card click", onclick: () => agentDetail(a.id) }, h("h4", {}, a.name_ar),
        h("div", { class: "row" }, pill(a.id), pill(TYPE_AR[a.type] || a.type, "gold"), a.mvp ? pill("MVP", "ok") : null,
          a.reads_author ? pill("يقرأ البصمة") : null),
        h("p", { class: "small muted" }, a.mission.slice(0, 160) + (a.mission.length > 160 ? "…" : "")))));
  };
  set(h("h2", {}, "الوكلاء (" + AGENTS.items.length + ")"),
    h("div", { class: "note" }, "اختر وكيلاً لتفعيله مباشرة بتكليف منكم، داخل مشروع أو خارجه، بالمحرّك المختار أعلى الصفحة. يُحقن عقد أسلوبكم المعتمد للوكلاء الذين يقرؤون ذاكرتكم وحدهم."),
    h("div", { class: "row" }, h("input", { id: "ag-q", placeholder: "بحث…", oninput: paint }),
      h("select", { id: "ag-type", onchange: paint }, h("option", { value: "" }, "كل الأنواع"), Object.entries(TYPE_AR).map(([k, v]) => h("option", { value: k }, v))),
      h("select", { id: "ag-dep", onchange: paint }, h("option", { value: "" }, "كل الإدارات"), Object.entries(AGENTS.departments).map(([k, v]) => h("option", { value: k }, v))),
      h("label", {}, h("input", { type: "checkbox", id: "ag-mvp", onchange: paint }), " نواة التشغيل (MVP) فقط")),
    grid);
  paint();
}
async function agentDetail(aid) {
  const [d, ov] = await Promise.all([G("agent", { id: aid }), G("overview")]);
  const a = d.spec;
  const out = h("div", { id: "ag-out" });
  const list = (title, arr) => arr && arr.length ? h("details", {}, h("summary", {}, title + " (" + arr.length + ")"), h("ul", {}, arr.map((x) => h("li", {}, typeof x === "string" ? x : JSON.stringify(x))))) : null;
  set(h("div", { class: "row" }, btn("→ كل الوكلاء", () => agentsView(), "ghost sm")),
    h("h2", {}, a.name_ar + " — " + a.name_en),
    h("div", { class: "row" }, pill(a.agent_id), pill(TYPE_AR[a.type] || a.type, "gold"), pill(a.model_tier), pill("v" + a.version), pill(a.department)),
    h("p", {}, a.mission),
    h("div", { class: "split" },
      h("div", {}, list("المسؤوليات", a.responsibilities), list("المدخلات", a.inputs), list("المخرجات", a.outputs),
        list("المهارات", a.skills), list("قراءة الذاكرة", a.memory.read), list("كتابة الذاكرة", a.memory.write),
        list("يحتاج موافقة بشرية", a.human_approval), list("محظورات", (a.permissions || {}).prohibited),
        list("يستلم من", (a.handoffs || {}).receives_from), list("يسلّم إلى", (a.handoffs || {}).sends_to),
        list("شروط التوقف", a.stop_conditions)),
      h("div", { class: "card" }, h("h3", {}, "تفعيل الوكيل"),
        h("div", { class: "form" },
          field("التكليف", h("textarea", { id: "ad-task", placeholder: "مثال: اكتب مسودة عمود من 300 كلمة عن…" }), true),
          field("سياق أو مواد (اختياري)", h("textarea", { id: "ad-ctx", placeholder: "الصق نصوصاً أو ملاحظات يعتمد عليها الوكيل" }), true),
          field("الجنس", sel("ad-genre", [["", "— بلا جنس —"], ["creative", "الإبداع الروائي"], ["research", "البحث العلمي"], ["intellectual", "الفكري"], ["op_ed", "عمود الرأي"]], "")),
          field("السجلّ الأسلوبي", sel("ad-reg", REGISTERS, "")),
          field("داخل مشروع", sel("ad-proj", [["", "— خارج المشاريع —"], ...ov.projects.map((p) => [p.id, p.id + " " + p.title])], ""))),
        h("div", { class: "row" },
          btn("فعّل الوكيل بالمحرّك المختار", async () => {
            const e = engine();
            const r = await busy(e === "manual" ? "تُعدّ الحزمة…" : "يعمل " + a.name_ar + "…", () => api("adhoc", {
              agent: aid, task: val("ad-task"), context: $("#ad-ctx").value, register: val("ad-reg"), genre: val("ad-genre"), project: val("ad-proj"), engine: e }));
            out.replaceChildren(runView(r.output != null ? { ...r, kind: "output.md", text: r.output } : r, { project: val("ad-proj") || null }));
          }, "gold"),
          btn("معاينة البرومبت", async () => {
            const p = await G("agent", { id: aid, register: val("ad-reg") });
            out.replaceChildren(h("div", { class: "card" }, h("h3", {}, "البرومبت النظامي المركّب"),
              h("div", { class: "row" }, btn("نسخ", () => navigator.clipboard.writeText(p.system_prompt).then(() => toast("نُسخ")), "sm ghost")), pre(p.system_prompt)));
          }, "ghost"),
          btn("اختبار بنيوي", async () => { const r = await api("eval", { agent: aid }); out.replaceChildren(json(r)); }, "ghost"),
          btn("تقييم حيّ (يستهلك رصيداً)", async () => {
            if (!confirm("التقييم الحي يشغّل كل حالات الاختبار عبر المحرّك المختار ويستهلك رصيداً. متابعة؟")) return;
            const r = await busy("يجري التقييم الحي…", () => api("eval", { agent: aid, live: true, engine: engine() === "manual" ? "auto" : engine() }));
            out.replaceChildren(json(r));
          }, "ghost")),
        out)));
}

// ---------- سير العمل ----------
async function workflowsView() {
  const w = await G("workflows");
  set(h("h2", {}, "سير العمل (" + w.items.length + ")"), h("div", { class: "grid" }, w.items.map((x) =>
    h("div", { class: "card click", onclick: () => workflowDetail(x.id) }, h("h4", {}, x.name_ar || x.id),
      h("div", { class: "row" }, pill(x.id), pill(x.steps + " خطوة", "gold")),
      h("p", { class: "small muted" }, (x.project_types || []).map((t) => PTYPE_AR[t] || t).join("، ") || "سير مساند")))));
}
async function workflowDetail(id, type, model) {
  const d = await G("workflows", { id, type, model });
  const types = d.workflow.project_types || [];
  set(h("div", { class: "row" }, btn("→ كل سير العمل", () => workflowsView(), "ghost sm")),
    h("h2", {}, (d.workflow.name_ar || id)), d.workflow.notes ? h("p", { class: "muted" }, d.workflow.notes) : null,
    h("div", { class: "row" },
      types.length ? sel("wf-type", types.map((t) => [t, PTYPE_AR[t] || t]), d.context.project_type) : null,
      sel("wf-model", [["A", "A"], ["B", "B"], ["C", "C"]], d.context.operating_model || "A"),
      btn("وسّع الخطة", () => workflowDetail(id, val("wf-type"), val("wf-model")), "sm"),
      types.length ? btn("ابدأ مشروعاً بهذا المسار", () => newProjectForm(null, val("wf-type") || types[0]), "sm gold") : null),
    d.context.note ? h("p", { class: "muted small" }, d.context.note) : null,
    h("table", {}, h("tr", {}, ["الخطوة", "الوكيل", "المهمة", "المستوى", "البوابة", "موافقة بشرية"].map((x) => h("th", {}, x))),
      d.steps.map((s) => h("tr", {}, h("td", {}, s.id), h("td", {}, s.assigned_agent || s.agent || ""), h("td", { class: "small" }, s.task || s.workflow || ""),
        h("td", {}, s.decision_level || ""), h("td", {}, s.gate || ""), h("td", {}, s.human_approval ? "نعم" : "")))));
}

// ---------- الاعتمادات والذاكرة ----------
async function governanceView() {
  const [c, m] = await Promise.all([G("candidates"), G("memory")]);
  const layerOpts = [["MEM-AUTHOR", "ذاكرة المؤلف"], ["MEM-INSTITUTIONAL", "الذاكرة المؤسسية"], ["MEM-RESEARCH", "الذاكرة البحثية"], ["MEM-EDITORIAL", "الذاكرة التحريرية"]];
  const memBox = h("div", { id: "mem-box" });
  set(h("h2", {}, "مرشّحات بانتظار اعتمادكم (" + c.items.length + ")"),
    h("div", { class: "note" }, "لا يدخل عنصر ذاكرة المؤلف أو الذاكرة المؤسسية إلا بإقراركم (L4). العناصر الخاصة (AUTHOR_ONLY) لا تُرقّى إلا إلى ذاكرة المؤلف."),
    c.items.length ? h("table", {}, h("tr", {}, ["المعرّف", "النوع", "المضمون", "الطبقة", ""].map((x) => h("th", {}, x))),
      c.items.map((it, i) => h("tr", {}, h("td", {}, it.Memory_ID, h("br"), pill(it.Access_Level, it.Access_Level === "AUTHOR_ONLY" ? "gold" : "")),
        h("td", {}, it.Type), h("td", { class: "small" }, it.Content),
        h("td", {}, sel("pl-" + i, it.Access_Level === "AUTHOR_ONLY" ? [layerOpts[0]] : layerOpts.slice(1).concat([layerOpts[0]]),
          it.Access_Level === "AUTHOR_ONLY" ? "MEM-AUTHOR" : (it.Type === "lesson" || it.Type === "method" || it.Type === "error" ? "MEM-INSTITUTIONAL" : "MEM-RESEARCH"))),
        h("td", {}, authorBox("pc-" + i), btn("اعتمد", async () => {
          const r = await api("promote", { memory_id: it.Memory_ID, layer: val("pl-" + i), confirm_author: val("pc-" + i) });
          toast("رُقّي " + r.Memory_ID + " إلى " + r.Layer); governanceView();
        }, "sm gold")))))
      : h("p", { class: "muted" }, "لا مرشّحات معلّقة."),
    h("h2", {}, "طبقات الذاكرة"),
    h("div", { class: "grid" }, Object.entries(m.layers).map(([k, v]) => h("div", { class: "card click", onclick: () => showLayer(k) },
      h("h4", {}, m.definitions[k] || k), h("div", { class: "kpi" }, v.count), pill(k)))),
    memBox,
    h("h2", {}, "بوابات الجودة"), h("div", { id: "gates" }, btn("اعرض البوابات وحقوق القرار", async () => {
      const g = await G("governance");
      $("#gates").replaceChildren(h("table", {}, h("tr", {}, ["البوابة", "السؤال", "المعتمِد", "المستوى", "المعايير"].map((x) => h("th", {}, x))),
        g.gates.map((x) => h("tr", {}, h("td", {}, x.id + " " + x.name_ar), h("td", {}, x.question), h("td", {}, x.approver),
          h("td", {}, x.decision_level), h("td", { class: "small" }, h("ul", {}, (x.criteria || []).map((c) => h("li", {}, c))))))));
    }, "ghost")));
}
async function showLayer(layer) {
  const m = await G("memory", { layer });
  const items = m.layers[layer].items.sort((a, b) => a.Memory_ID.localeCompare(b.Memory_ID));
  $("#mem-box").replaceChildren(h("div", { class: "card" }, h("h3", {}, (m.definitions[layer] || layer) + " — " + items.length + " عنصراً"),
    items.length ? h("table", {}, h("tr", {}, ["المعرّف", "النوع", "الإصدار", "المضمون", ""].map((x) => h("th", {}, x))),
      items.map((it, i) => h("tr", {}, h("td", {}, it.Memory_ID), h("td", {}, it.Type), h("td", {}, "v" + it.Version),
        h("td", { class: "small" }, it.Content, h("div", { class: "row" }, (it.Tags || []).map((t) => pill(t)))),
        h("td", {}, btn("تعديل", () => amendForm(layer, it), "sm ghost")))))
      : h("p", { class: "muted" }, "فارغة (أو الذاكرة الخاصة غير مستعادة على هذا الجهاز).")));
  $("#mem-box").scrollIntoView({ behavior: "smooth" });
}
function amendForm(layer, it) {
  $("#mem-box").replaceChildren(h("div", { class: "card" }, h("h3", {}, "إصدار جديد لـ " + it.Memory_ID + " (لا يُمحى السابق)"),
    h("div", { class: "form" }, field("المضمون الجديد", h("textarea", { id: "am-content" }, it.Content), true),
      field("سبب التعديل", h("input", { id: "am-reason" }), true)),
    h("div", { class: "row" }, authorBox("am-confirm"), btn("احفظ الإصدار", async () => {
      const r = await api("amend", { memory_id: it.Memory_ID, layer, content: $("#am-content").value.trim(), reason: val("am-reason"), confirm_author: val("am-confirm") });
      toast(r.Memory_ID + " v" + r.Version); showLayer(layer);
    }, "gold"), btn("إلغاء", () => showLayer(layer), "ghost"))));
}

// ---------- الأدوات ----------
async function checkTextView(text, pid) {
  go("tools", true);
  await toolsView();
  $("#ck-text").value = text || "";
  if (pid) $("#ck-proj").value = pid;
  $("#ck-text").scrollIntoView({ behavior: "smooth" });
}
function checkSummary(r) {
  const c = r.claims || {}, ci = r.citations || {};
  const vp = r.voice_pole;
  return h("div", { class: "card" }, h("h3", {}, "نتيجة الفحص"),
    h("div", { class: "row" },
      pill("وسوم الادعاءات: " + (c.passes ? "سليمة" : "ناقصة"), c.passes ? "ok" : "bad"),
      pill("الاستشهادات (QG4): " + (ci.passes_qg4 ? "سليمة" : "تحتاج مراجعة"), ci.passes_qg4 ? "ok" : "bad"),
      r.register ? pill("السجلّ: " + r.register) : pill("بلا مرجع أسلوبي"),
      vp ? pill("القرب من صوتكم: " + (vp.closer_to === "author" ? "صوت المؤلف" : "الصياغة المُعانة") + " (" + vp.assisted_share + ")", vp.closer_to === "author" ? "ok" : "warn") : null),
    h("p", { class: "muted small" }, "مؤشر القطب: 0 = صوت المؤلف تماماً، 1 = الصياغة المُعانة تماماً. التنبيه الأسلوبي لا يحجب البوابة؛ القرار للمحرر والمؤلف."),
    h("details", {}, h("summary", {}, "التفاصيل الكاملة"), json(r)));
}
async function toolsView() {
  const ov = await G("overview");
  const out = h("div", { id: "tool-out" });
  set(
    h("h2", {}, "فحص مخطوطة أو نص"),
    h("div", { class: "form" },
      field("النص", h("textarea", { id: "ck-text", placeholder: "الصق المسودة (مع وسوم الادعاءات والاستشهادات إن وجدت)" }), true),
      field("السجلّ الأسلوبي", sel("ck-reg", REGISTERS, "")),
      field("مصادر مشروع", sel("ck-proj", [["", "— المصادر المركزية فقط —"], ...ov.projects.map((p) => [p.id, p.id + " " + p.title])], ""))),
    h("div", { class: "row" }, btn("افحص", async () => {
      const r = await api("check_text", { text: $("#ck-text").value, register: val("ck-reg"), project: val("ck-proj") });
      $("#ck-out").replaceChildren(checkSummary(r));
    }, "gold")), h("div", { id: "ck-out" }),
    h("h2", {}, "التحقق من DOI"),
    h("div", { class: "form" }, field("DOI", h("input", { id: "doi", dir: "ltr", placeholder: "10.xxxx/yyyy" })), field("العنوان المتوقع", h("input", { id: "doi-t" })),
      field("السنة", h("input", { id: "doi-y", type: "number" }))),
    h("div", { class: "row" }, btn("تحقق", async () => {
      const r = await busy("يتحقق من Crossref…", () => api("verify_doi", { doi: val("doi"), title: val("doi-t"), year: val("doi-y") }));
      $("#doi-out").replaceChildren(json(r));
    })), h("div", { id: "doi-out" }),
    h("h2", {}, "سلامة المنظومة"),
    h("div", { class: "row" },
      btn("فحص الاتساق", async () => { const r = await api("validate", {}); out.replaceChildren(r.ok ? pill("المنظومة متسقة", "ok") : json(r.errors)); }),
      btn("توليد ملفات الوكلاء", async () => { const r = await api("generate", {}); out.replaceChildren(pill(r.written.length + " ملفاً كُتب", "ok")); }, "ghost"),
      btn("الاختبار البنيوي لكل الوكلاء", async () => { const r = await api("eval", {}); out.replaceChildren(r.ok ? pill(r.suites + " حزمة اختبار سليمة", "ok") : json(r.errors)); }, "ghost"),
      btn("الفحص الأمني", async () => { const r = await api("security_scan", {}); out.replaceChildren(pill(r.ok ? "سليم" : "مخالفات", r.ok ? "ok" : "bad"), pre(r.output, true)); }, "ghost"),
      btn("بناء لوحة القيادة HTML", async () => {
        const r = await api("dashboard", {});
        const f = await G("file", { path: r.path });
        window.open(URL.createObjectURL(new Blob([f.text], { type: "text/html" })), "_blank");
      }, "ghost")),
    out);
}

// ---------- السجل والكلفة ----------
async function logView(pid) {
  const [a, c, ov] = await Promise.all([G("audit", { project: pid, limit: 120 }), G("cost", { project: pid }), G("overview")]);
  set(h("h2", {}, "سجل التدقيق"),
    h("div", { class: "row" }, sel("lg-proj", [["", "كل المشاريع"], ...ov.projects.map((p) => [p.id, p.id])], pid || ""),
      btn("تصفية", () => logView(val("lg-proj") || undefined), "sm")),
    h("p", { class: "muted small" }, "آخر " + a.items.length + " من " + a.total + " حدثاً (السجل إلحاقي ويحفظ المعرّفات لا المحتوى)."),
    h("table", {}, h("tr", {}, ["التاريخ", "الفاعل", "الإجراء", "المشروع", "القرار", "النموذج"].map((x) => h("th", {}, x))),
      a.items.map((r) => h("tr", {}, h("td", { class: "small" }, r.DATE), h("td", {}, r.AGENT), h("td", { class: "small" }, r.ACTION),
        h("td", {}, r.PROJECT || ""), h("td", { class: "small" }, [r.DECISION, r.DECISION_LEVEL].filter(Boolean).join(" ")), h("td", { class: "small" }, r.MODEL || "")))),
    h("h2", {}, "الكلفة"), json(c));
}

// ---------- الإعدادات ----------
async function settingsView() {
  await refreshEngines(true);
  const e = ENG, o = await G("ping");
  set(h("h2", {}, "المحرّكات والاتصال بـ Claude"),
    h("table", {},
      h("tr", {}, h("th", {}, "يدوي"), h("td", {}, pill("متاح دائماً", "ok")), h("td", {}, "تُعدّ اللوحة حزمة البرومبت كاملة؛ زر «انسخ وافتح Claude» ينسخها ويفتح claude.ai، ثم تلصقون الرد في اللوحة.")),
      h("tr", {}, h("th", {}, "Claude Code"),
        h("td", {}, pill(!e.claude_code ? "غير مثبت" : e.claude_logged_in === true ? "مسجّل الدخول" : e.claude_logged_in === false ? "غير مسجّل الدخول" : "مثبت",
          e.claude_code && e.claude_logged_in !== false ? "ok" : "warn")),
        h("td", {}, e.claude_code ? h("div", {}, "المسار: " + e.claude_code_path + " — يعمل بحسابكم في Claude، بلا مفتاح في المستودع، ودون أدوات ملفات أو أوامر.",
          h("div", { class: "row" },
            e.claude_logged_in !== true ? btn("تسجيل الدخول إلى Claude", claudeLogin, "gold") : null,
            btn("تحقق من الحالة", async () => { await refreshEngines(true); settingsView(); }, "ghost")),
          e.claude_logged_in !== true ? h("p", { class: "small muted" }, "تنفتح نافذة سوداء ثم المتصفح: سجّلوا الدخول بحسابكم في claude.ai ووافقوا. إن طُلب رمز فانسخوه من المتصفح إلى النافذة. ثم أغلقوها واضغطوا «تحقق من الحالة».") : null)
          : "ثبّتوه من PowerShell بالأمر: irm https://claude.ai/install.ps1 | iex ثم أعيدوا تشغيل اللوحة.")),
      h("tr", {}, h("th", {}, "API"), h("td", {}, Object.entries(e.api_keys).map(([k, v]) => h("div", {}, pill(k + ": " + (v ? "موجود" : "—"), v ? "ok" : "")))),
        h("td", {}, "تُضبط المفاتيح في ملف ‎.env‎ أو متغيرات البيئة؛ لا تعرضها اللوحة ولا تخزنها."))),
    h("h2", {}, "الحالة"),
    h("p", {}, "جذر المستودع: ", h("code", {}, o.root)),
    h("div", { class: "row" }, pill("الذاكرة الخاصة: " + (e.private_memory ? "مستعادة" : "غير موجودة — استعيدوا النسخة الاحتياطية إلى memory/author/private"), e.private_memory ? "ok" : "bad")),
    h("h2", {}, "الخصوصية"),
    h("ul", {}, h("li", {}, "اللوحة تعمل على هذا الجهاز وحده (127.0.0.1) وبرمز يتجدد عند كل تشغيل."),
      h("li", {}, "مخرجات التشغيل وحزم البرومبت لا تُرفع إلى GitHub لأنها قد تحمل عقد أسلوبكم."),
      h("li", {}, "قرارات L4 (الاعتماد، الترقية، تعديل الذاكرة) تتطلب إقراركم الصريح في كل مرة.")),
    h("div", { class: "row" }, btn("إيقاف اللوحة", async () => {
      if (!confirm("إيقاف خادم اللوحة؟ تعيد تشغيله الأيقونة.")) return;
      await api("shutdown", {}); set(h("div", { class: "note" }, "أُوقفت اللوحة. افتحوها من الأيقونة متى شئتم."));
    }, "danger")));
}


// ---------- بناء العمل (الأجناس ومستويات الإنتاج) ----------
const voicePill = (u) => {
  const sh = u.voice && u.voice.pole ? u.voice.pole.assisted_share : null;
  if (sh == null) return u.voice && u.voice.deviation_mean != null ? pill("انحراف " + u.voice.deviation_mean) : "";
  return pill((sh <= 0.35 ? "صوت المؤلف " : sh <= 0.5 ? "قريب " : "مُعان ") + sh, sh <= 0.35 ? "ok" : sh <= 0.5 ? "gold" : "bad");
};
async function renderBook(pid) {
  const box = $("#book-box");
  if (!box) return;
  const [b, g] = await Promise.all([G("book", { id: pid }), genresData()]);
  if (!b.outline) { box.replaceChildren(); return; }
  const ob = b.outline, GN = g.genres[ob.genre], L = g.levels.levels[ob.level];
  const approved = ob.units.filter((u) => u.status === "APPROVED").length;
  const card = h("div", { class: "card" },
    h("h3", {}, "بناء العمل"),
    h("div", { class: "row" }, pill(GN.name_ar, "gold"), pill("المستوى: " + L.name_ar), ob.target_pages ? pill(ob.target_pages + " صفحة") : null,
      ob.target_words ? pill((ob.target_words).toLocaleString("ar") + " كلمة") : null,
      pill("معتمد " + approved + " / " + ob.units.length, approved && approved === ob.units.length ? "ok" : ""),
      pill("مكتوب " + (b.voice.total_words || 0).toLocaleString("ar") + " كلمة")),
    h("p", { class: "small muted" }, L.summary));
  const body = h("div");
  card.append(body);
  box.replaceChildren(card);
  if (b.job) return jobView(pid, b.job, body);
  if (!ob.units.length) return outlineStart(pid, ob, body);
  if (!ob.outline_approved) return outlineEditor(pid, ob, body);
  // جدول الوحدات
  body.append(h("table", {}, h("tr", {}, ["الوحدة", "العنوان", "الموازنة", "المكتوب", "الحالة", "الصوت", "تعديل المؤلف", ""].map((x) => h("th", {}, x))),
    ob.units.map((u) => h("tr", {}, h("td", {}, u.id), h("td", {}, u.title, u.brief ? h("div", { class: "small muted" }, u.brief) : null),
      h("td", {}, u.target_words || "—"), h("td", {}, u.words || 0), h("td", {}, pill(UNIT_STATUS_AR[u.status] || u.status, UNIT_STATUS_CLS[u.status])),
      h("td", {}, voicePill(u)), h("td", {}, u.author_change != null ? Math.round(u.author_change * 100) + "%" : "—"),
      h("td", {}, h("div", { class: "row" },
        u.status !== "APPROVED" ? btn(ob.level === "scaffold" && u.status === "PLANNED" ? "بطاقة" : (u.status === "PLANNED" ? "اكتب" : "أعد الكتابة"), () => draftUnit(pid, u.id), "sm") : null,
        btn("افتح", () => unitEditor(pid, u.id), "sm ghost")))))));
  const actions = h("div", { class: "row" },
    btn("جمّع الكتاب", async () => {
      const r = await busy("يُجمَّع الكتاب…", () => api("book_assemble", { project: pid }));
      toast(r.words.toLocaleString("ar") + " كلمة ≈ " + r.pages + " صفحة" + (r.missing.length ? " — ناقص: " + r.missing.join("، ") : ""));
      renderBook(pid);
    }, "ghost"),
    b.book ? btn("تنزيل الكتاب (Markdown)", () => downloadRaw(b.book), "ghost") : null,
    b.book ? btn("تنزيل Word", () => downloadRaw(b.book.replace(/\.md$/, ".docx")), "ghost") : null);
  body.append(actions);
  if (ob.level === "full" && b.estimate && b.estimate.units) {
    const e = b.estimate;
    body.append(h("div", { class: "note" },
      h("b", {}, "الكتابة الكاملة: "), e.units + " وحدة، " + e.calls + " استدعاء، نحو " + e.words.toLocaleString("ar") + " كلمة (≈ " + e.pages + " صفحة). ",
      "الكلفة التقديرية: " + (e.usd_estimate != null ? "$" + e.usd_estimate : "غير محددة") + (e.budget_usd ? " من ميزانية $" + e.budget_usd : "") + ". ",
      h("div", { class: "small muted" }, e.assumptions),
      e.over_budget ? pill("تتجاوز الميزانية", "bad") : null,
      h("div", { class: "row" }, h("label", { class: "confirm" }, h("input", { type: "checkbox", id: "bk-cost" }), " أقرّ بالتقدير وأبدأ الكتابة"),
        btn("اكتب الكتاب كاملاً بالمحرّك المختار", async () => {
          const j = await api("book_draft_all", { project: pid, engine: engine(), confirm_cost: val("bk-cost") });
          renderBook(pid);
        }, "gold"))));
  }
  const flagged = b.voice.flagged || [];
  body.append(h("details", {}, h("summary", {}, "تقرير الصوت" + (flagged.length ? " — " + flagged.length + " وحدة تحتاج عودة إلى صوتكم" : "")),
    h("p", { class: "small muted" }, b.voice.note), b.voice.author_change_mean != null ? h("p", {}, "متوسط تعديل المؤلف: " + Math.round(b.voice.author_change_mean * 100) + "%") : null,
    flagged.length ? h("p", {}, "ابدؤوا بـ: " + flagged.join("، ")) : null));
}
function jobView(pid, job, body) {
  const bar = h("progress", { max: job.total || 1, value: job.done || 0, style: "width:100%" });
  body.append(h("div", { class: "note" }, h("b", {}, "تُكتب الوحدات الآن… "), (job.done || 0) + " / " + (job.total || "…") + (job.current ? " — " + job.current : ""), bar,
    h("p", { class: "small muted" }, "يمكنكم إغلاق هذه الصفحة؛ العمل مستمر ما دامت اللوحة تعمل.")));
  setTimeout(async () => {
    const j = await G("job", { id: job.id }).catch(() => null);
    if (!j || j.state === "running") return $("#book-box") && renderBook(pid);
    if (j.state === "error") toast("توقفت الكتابة: " + j.error, true); else toast("اكتملت الكتابة وجُمّع الكتاب");
    openProject(pid);
  }, 3000);
}
function outlineStart(pid, ob, body) {
  const paste = h("textarea", { placeholder: "الصقوا هنا ردّ Claude الذي يحوي كتلة yaml للمخطط" });
  body.append(h("h4", {}, "المخطط"),
    h("div", { class: "form" }, field("عدد الوحدات/المحاور", h("input", { id: "ol-n", type: "number", value: 5, min: 1 })),
      field("توجيهكم للمخطط (اختياري)", h("input", { id: "ol-g", placeholder: "مثال: ابدأ بالتاريخ وانته بالاستشراف" }), true)),
    h("div", { class: "row" },
      btn("مخطط افتراضي أحرّره بنفسي", async () => { await api("book_skeleton", { project: pid, n: val("ol-n") }); renderBook(pid); }, "ghost"),
      btn("اقترح المخطط (الوكيل)", async () => {
        const r = await busy("يقترح الوكيل المخطط…", () => api("book_propose", { project: pid, engine: engine(), n: val("ol-n"), guidance: val("ol-g") }));
        if (r.manual) {
          body.append(h("div", { class: "card" }, h("div", { class: "row" }, btn("انسخ وافتح Claude", () => copyAndOpen(r.text), "gold")), paste,
            btn("استورد المخطط", async () => { await api("book_import_outline", { project: pid, text: paste.value }); renderBook(pid); })));
        } else renderBook(pid);
      }, "gold")));
}
function outlineEditor(pid, ob, body) {
  const rows = ob.units.map((u) => ({ ...u }));
  const tbl = h("table");
  const paint = () => tbl.replaceChildren(h("tr", {}, ["#", "العنوان", "الموجز", "الكلمات", ""].map((x) => h("th", {}, x))),
    rows.map((u, i) => h("tr", {}, h("td", {}, i + 1),
      h("td", {}, h("input", { value: u.title, oninput: (e) => (u.title = e.target.value) })),
      h("td", {}, h("textarea", { style: "min-height:50px", oninput: (e) => (u.brief = e.target.value) }, u.brief || "")),
      h("td", {}, h("input", { type: "number", value: u.target_words || "", style: "width:90px", oninput: (e) => (u.target_words = +e.target.value || null) })),
      h("td", {}, h("div", { class: "row" },
        i > 0 ? btn("↑", () => { [rows[i - 1], rows[i]] = [rows[i], rows[i - 1]]; paint(); }, "sm ghost") : null,
        btn("✕", () => { rows.splice(i, 1); paint(); }, "sm ghost"),
        btn("+", () => { rows.splice(i + 1, 0, { title: "وحدة جديدة", brief: "", kind: u.kind }); paint(); }, "sm ghost"))))));
  paint();
  body.append(h("h4", {}, "حرّروا المخطط ثم اعتمدوه"),
    h("p", { class: "small muted" }, "اتركوا خانة الكلمات فارغة لتوزَّع آلياً على الطول الكلي؛ المقدمة والخاتمة نصف وزن المحور."), tbl,
    h("div", { class: "row" },
      btn("احفظ المخطط", async () => { await api("book_set_units", { project: pid, units: rows }); toast("حُفظ"); renderBook(pid); }, "ghost"),
      authorBox("ol-confirm"),
      btn("اعتمد المخطط", async () => {
        await api("book_set_units", { project: pid, units: rows });
        await api("book_approve_outline", { project: pid, confirm_author: val("ol-confirm") });
        toast("اعتُمد المخطط"); renderBook(pid);
      }, "gold")));
}
async function draftUnit(pid, uid) {
  const e = engine();
  const r = await busy(e === "manual" ? "تُعدّ الحزمة…" : "يكتب الوكيل " + uid + "… قد يستغرق دقائق", () => api("book_draft", { project: pid, unit: uid, engine: e }));
  if (r.manual) return unitEditor(pid, uid, r.text);
  toast(uid + ": " + r.words + " كلمة"); await renderBook(pid); unitEditor(pid, uid);
}
async function unitEditor(pid, uid, manualPrompt) {
  const [u, b] = await Promise.all([G("book_unit", { project: pid, unit: uid }), G("book", { id: pid })]);
  const meta = b.outline.units.find((x) => x.id === uid);
  const box = $("#run-box");
  const ta = h("textarea", { style: "min-height:420px", dir: "rtl" }, u.current || u.approved || "");
  const out = h("div");
  const parts = [h("h3", {}, uid + " — " + meta.title), h("div", { class: "row" }, pill(UNIT_STATUS_AR[meta.status], UNIT_STATUS_CLS[meta.status]),
    pill((meta.words || 0) + " / " + (meta.target_words || "—") + " كلمة"), voicePill(meta),
    meta.author_change != null ? pill("تعديلكم " + Math.round(meta.author_change * 100) + "%", "gold") : null)];
  if (manualPrompt) {
    const paste = h("textarea", { placeholder: "الصقوا ردّ Claude هنا" });
    parts.push(h("div", { class: "note" }, "الوضع اليدوي: انسخوا الحزمة إلى Claude ثم الصقوا الرد.",
      h("div", { class: "row" }, btn("انسخ وافتح Claude", () => copyAndOpen(manualPrompt), "gold")), paste,
      btn("سجّل نص الوكيل", async () => { await api("book_record", { project: pid, unit: uid, text: paste.value }); await renderBook(pid); unitEditor(pid, uid); })));
  }
  if (u.card) parts.push(h("details", { open: !u.current }, h("summary", {}, "بطاقة الوحدة"), pre(u.card)));
  parts.push(h("p", { class: "small muted" }, b.outline.level === "scaffold" ? "اكتبوا نص الوحدة هنا بأقلامكم، ثم احفظوا أو اعتمدوا." :
    "حرّروا النص بحرية: كل حفظ يُقاس، ومسودة الوكيل الأصلية محفوظة للمقارنة."), ta,
    h("div", { class: "row" },
      btn("احفظ تعديلي", async () => { await api("book_revise", { project: pid, unit: uid, text: ta.value }); toast("حُفظ وقيس"); await renderBook(pid); unitEditor(pid, uid); }),
      btn("مواءمة الصوت (اقتراح)", async () => {
        const r = await busy("يواءم المحرر الصوت…", () => api("book_align", { project: pid, unit: uid, engine: engine() }));
        if (r.manual) return out.replaceChildren(h("div", { class: "row" }, btn("انسخ وافتح Claude", () => copyAndOpen(r.text), "gold")));
        const sh = (v) => v && v.pole ? v.pole.assisted_share : "—";
        out.replaceChildren(h("div", { class: "card" }, h("h4", {}, "نسخة المواءمة"), h("p", {}, "القطب قبل: " + sh(r.before) + " ← بعد: " + sh(r.after)),
          pre(r.text), h("div", { class: "row" }, btn("اعتمدها نسخة عمل", async () => { await api("book_adopt_aligned", { project: pid, unit: uid }); await renderBook(pid); unitEditor(pid, uid); }, "gold"))));
      }, "ghost"),
      btn("فحص النص", () => checkTextView(ta.value, pid), "ghost"),
      authorBox("un-confirm"),
      btn("اعتمد الوحدة", async () => {
        const r = await api("book_approve_unit", { project: pid, unit: uid, text: ta.value, confirm_author: val("un-confirm") });
        toast("اعتُمدت " + uid + " — " + r.decision); openProject(pid);
      }, "gold")),
    out);
  if (u.ai && u.ai !== u.current) parts.push(h("details", {}, h("summary", {}, "مسودة الوكيل الأصلية"), pre(u.ai)));
  if (u.notes) parts.push(h("details", {}, h("summary", {}, "ملاحظات الوكيل"), pre(u.notes)));
  box.replaceChildren(h("div", { class: "card" }, ...parts));
  box.scrollIntoView({ behavior: "smooth" });
}

async function genresView() {
  const g = await genresData();
  set(h("h2", {}, "الأجناس الكتابية"),
    h("div", { class: "note" }, "لكل جنس صفاته الفكرية والأسلوبية ووكيله وسير عمله؛ تُحقن صفاته في برومبت الوكيل، ويُقاس النص بمرجع بصمتكم في سجلّه."),
    h("div", { class: "grid" }, Object.entries(g.genres).map(([k, G2]) => h("div", { class: "card" },
      h("h4", {}, G2.name_ar), h("div", { class: "row" }, pill("السجلّ: " + G2.register), pill(G2.lead_agent, "gold"), G2.max_words ? pill("≤ " + G2.max_words + " كلمة") : null),
      h("p", { class: "small" }, G2.project_types.map((t) => PTYPE_AR[t] || t).join("، ")),
      h("b", { class: "small" }, "فكرياً"), h("ul", { class: "small" }, G2.intellectual.map((x) => h("li", {}, x))),
      h("b", { class: "small" }, "أسلوبياً"), h("ul", { class: "small" }, G2.stylistic.map((x) => h("li", {}, x))),
      h("p", { class: "small muted" }, G2.evidence),
      h("div", { class: "row" }, btn("مشروع من هذا الجنس", () => newProjectForm(k), "sm gold"))))),
    h("h2", {}, "مستويات الإنتاج"),
    h("div", { class: "grid" }, Object.entries(g.levels.levels).map(([k, L]) => h("div", { class: "card" },
      h("h4", {}, L.order + ". " + L.name_ar), h("p", { class: "small" }, L.summary),
      h("ol", { class: "small" }, L.steps.map((x) => h("li", {}, x)))))),
    h("p", { class: "muted small" }, "في كل المستويات تبقى مسودة الوكيل الأصلية محفوظة، ويُرصد مقدار تعديلكم عليها؛ ولا يدخل نص المخطوط المعتمد إلا بإقراركم."));
}

// ---------- التنقل ----------
const VIEWS = { home, projects, agents: agentsView, genres: genresView, workflows: workflowsView, governance: governanceView, tools: toolsView, log: () => logView(), settings: settingsView };
function go(tab, noRender) {
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
  if (!noRender) VIEWS[tab]().catch((e) => console.error(e));
}
$("#tabs").addEventListener("click", (ev) => { const b = ev.target.closest("button"); if (b) go(b.dataset.tab); });

(async function boot() {
  if (!TOKEN) { set(h("div", { class: "note" }, "افتحوا اللوحة من أيقونة سطح المكتب أو بالأمر rkpos panel (الرابط يحمل رمز الجلسة).")); return; }
  try { await refreshEngines(); await home(); } catch (e) { console.error(e); }
})();
