// LiveLife Habit 4 "Think Win-Win" — the TEACHER ASSESSMENT OUTCOME, on its own page (outcome.html?id=<random id>, or with no
// id the latest result, which is what the front page's third button opens). Laid out like the LiveLife Section 9 outcome form:
// teacher, school, date, version; assessment score /32, overall performance %, overall rating; the recommendation (the chosen
// one ticked) with why; the eight competencies with score, mark %, rating and the evidence-based rationale; the conversion
// line; the proposed recommendation guide; strengths, priority growth areas, coaching and reassessment plan. No evaluator section.
// All numbers are worked out by the demo backend; this page only draws them. Text from the server or from a model is only ever
// put on the page with textContent, never as markup. Nothing is stored in the browser.
(function () {
  "use strict";

  var app = document.getElementById("app");

  function h(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === "class") el.className = attrs[k];
      else if (k === "text") el.textContent = attrs[k];
      else if (k.indexOf("on") === 0) el.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] === true) el.setAttribute(k, "");
      else if (attrs[k] !== false && attrs[k] != null) el.setAttribute(k, attrs[k]);
    });
    for (var i = 2; i < arguments.length; i++) {
      var c = arguments[i];
      if (c == null || c === false) continue;
      el.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    }
    return el;
  }

  function pct(v) { return v == null ? "—" : v + "%"; }
  function list(arr) {
    var ul = h("ul", { class: "clean" });
    (arr || []).forEach(function (t) { ul.appendChild(h("li", { text: t })); });
    return ul;
  }
  function tile(label, main, sub) {
    return h("div", { class: "tile" },
      h("div", { class: "tile-label", text: label }),
      h("div", { class: "tile-main", text: main }),
      sub ? h("div", { class: "tile-sub", text: sub }) : null);
  }
  function meta(label, value) { return h("div", null, h("b", { text: label }), h("span", { text: value })); }

  function render(o) {
    document.title = "Teacher Assessment Outcome — " + o.teacher.name;
    var wrap = h("div", null);

    wrap.appendChild(h("div", { class: "card outcome-head" },
      h("div", { class: "kicker", text: "LiveLife Education | Habit 4: Think Win-Win" }),
      h("h1", { text: "Teacher Assessment Outcome" }),
      h("p", { class: "muted", text: "Performance summary • Competency percentages • Recommendation" }),
      h("div", { class: "meta" },
        meta("Teacher name / ID", o.teacher.name), meta("School", o.teacher.school),
        meta("Assessment date", o.teacher.date), meta("Assessment version", o.teacher.version))));

    if (o.critical.flagged) {
      wrap.appendChild(h("div", { class: "critical", role: "alert",
        text: "Critical safety or inclusion concern flagged for review (" + o.critical.items.join(", ") +
              "). Coaching and reassessment are required whatever the total score." }));
    }

    var s = o.score;
    wrap.appendChild(h("div", { class: "scoreline" },
      tile("Assessment score", s.total + " / " + s.max, s.complete ? null : s.scored + " of " + s.of + " scored"),
      tile("Overall performance", pct(s.percent), "total ÷ 32"),
      tile("Overall rating", s.overall_rating || "—", null)));

    // recommendation: the chosen one ticked, as the form's checkboxes
    var reco = h("div", { class: "card" }, h("h2", { text: "Recommendation" }));
    var listEl = h("div", { class: "reco-list" });
    o.guide.forEach(function (g) {
      var on = o.recommendation === g.label;
      listEl.appendChild(h("div", { class: "reco-item" + (on ? " on" : "") },
        h("span", { class: "box", "aria-hidden": "true", text: on ? "✓" : "" }),
        h("div", null,
          h("div", { class: "lab", text: g.label }),
          h("div", { class: "rule", text: g.rule }))));
    });
    reco.appendChild(listEl);
    if (o.recommendation_why) reco.appendChild(h("p", { class: "why", text: o.recommendation_why }));
    else reco.appendChild(h("p", { class: "muted", text: "No recommendation yet: some responses could not be scored, so the thresholds can't be applied." }));
    reco.appendChild(h("p", { class: "muted small", text: o.guide_note }));
    wrap.appendChild(reco);

    // competency table
    var table = h("table", { class: "comp" },
      h("thead", null, h("tr", null,
        h("th", { scope: "col", text: "Competency" }), h("th", { scope: "col", text: "Score /4" }), h("th", { scope: "col", text: "Mark %" }),
        h("th", { scope: "col", text: "Rating" }), h("th", { scope: "col", text: "Evidence-based rationale (why this mark was awarded)" }))),
      h("tbody"));
    var body = table.querySelector("tbody");
    o.competencies.forEach(function (c) {
      var why = h("td", { "data-label": "Evidence-based rationale" }, h("span", { text: c.rationale }));
      if (c.coaching) why.appendChild(h("span", { class: "coach", text: "Coaching: " + c.coaching }));
      if (c.critical) why.appendChild(h("span", { class: "coach", text: "Critical concern: flagged for review." }));
      body.appendChild(h("tr", null,
        h("td", { "data-label": "Competency" }, h("strong", { text: c.id + ". " + c.name })),
        h("td", { "data-label": "Score /4", text: c.score == null ? "—" : String(c.score) }),
        h("td", { "data-label": "Mark %" }, h("span", { text: pct(c.mark_percent) }),
          h("div", { class: "meter", "aria-hidden": "true" }, h("i", { style: "width:" + (c.mark_percent || 0) + "%" }))),
        h("td", { "data-label": "Rating" }, h("span", { class: "badge " + (c.score == null ? "r-none" : "r-" + c.score), text: c.rating || "—" })),
        why));
    });
    wrap.appendChild(h("div", { class: "card" }, h("h2", { text: "Competencies" }), table,
      h("p", { class: "muted small", style: "margin-top:12px", text: o.conversion })));

    wrap.appendChild(h("div", { class: "card" }, h("h2", { text: "Overall performance summary (strengths evidenced)" }), list(o.strengths)));
    wrap.appendChild(h("div", { class: "card" }, h("h2", { text: "Priority growth areas / rationale for recommendation" }), list(o.growth)));
    wrap.appendChild(h("div", { class: "card" }, h("h2", { text: "Recommended coaching / support and reassessment plan" }), list(o.coaching_plan)));

    wrap.appendChild(h("div", { class: "nav noprint" }, h("span"),
      h("button", { class: "btn ghost", type: "button", text: "Print", onclick: function () { window.print(); } })));
    app.replaceChildren(wrap);
  }

  function missing(latest) {
    app.replaceChildren(h("div", { class: "card" },
      h("h2", { text: latest ? "No teacher assessment has been submitted yet" : "We can't find this outcome" }),
      h("p", { class: "muted", text: latest
        ? "When a teacher completes the assessment, the outcome appears here."
        : "The link may be incomplete, or a newer assessment has replaced it (this demo keeps only the latest result), or the demo was restarted." }),
      h("a", { class: "btn linkbtn", href: "./", text: "Take the teacher assessment" })));
  }

  var id = new URLSearchParams(window.location.search).get("id") || "";
  var latest = id === "";
  if (!latest && !/^[A-Za-z0-9_-]{16,40}$/.test(id)) { missing(false); return; }
  fetch("api/outcome/" + (latest ? "latest" : encodeURIComponent(id))).then(function (r) {
    if (!r.ok) throw new Error("none");
    return r.json();
  }).then(render).catch(function () { missing(latest); });
})();
