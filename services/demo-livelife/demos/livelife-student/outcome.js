// LiveLife Habit 4 "Think Win-Win" — the student's SCORECARD, on its own page (outcome.html?id=<long random id>).
// Layout from the LiveLife document, Section 3: header (name | grade | date), overall application %, final rating,
// a score summary (Knowledge Check, Situational Check, Overall Application, Final Rating), the 8-competency scorecard,
// then Strengths / Skills to practice / Try this next / Teacher support, and the rating guide.
// All the numbers are worked out by the demo backend; this page only draws them. Text from the server or from a model is
// only ever put on the page with textContent, never as markup. Nothing is stored in the browser.
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

  function rclass(r) { return r ? "r-" + String(r).toLowerCase() : "r-none"; }
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

  function render(o) {
    document.title = "Think Win-Win Scorecard — " + o.student.name;
    var wrap = h("div", null);

    // header + overall
    var rating = o.overall.rating;
    wrap.appendChild(h("div", { class: "card hero scorecard-head" },
      h("span", { class: "tag", text: "Your Think Win-Win scorecard" }),
      h("h1", { text: o.student.name }),
      h("p", { class: "muted", text: "Grade " + o.student.grade + "  |  " + o.student.date }),
      h("div", { class: "overall-label", text: "Final score" }),
      h("div", { class: "big", text: o.overall.score == null ? "—" : o.overall.score + " / " + o.overall.max }),
      rating
        ? h("div", { class: "badge " + rclass(rating), text: rating })
        : h("div", { class: "badge r-none", text: "Rating not available" }),
      o.overall.complete ? null
        : h("p", { class: "muted small", text: "Some of your written answers could not be scored, so there is no overall rating yet. Your teacher can look at them with you." })));

    // score summary
    var k = o.knowledge, s = o.situational;
    wrap.appendChild(h("div", { class: "tiles" },
      tile("Knowledge Check", k.score + " / " + k.max, k.correct + " of " + k.of + " correct"),
      tile("Situational Check", s.score + " / " + s.max, s.percent == null ? "not scored" : pct(s.percent) + (s.scored < s.of ? " (" + s.scored + " of " + s.of + " scored)" : "")),
      tile("Total score", o.overall.score == null ? "—" : o.overall.score + " / " + o.overall.max,
        o.overall.raw == null ? "needs every situation scored" : o.overall.raw + " of " + o.overall.raw_max + " marks, out of 100"),
      tile("Final Rating", rating || "—", null)));

    // competency scorecard
    var table = h("table", { class: "comp" },
      h("thead", null, h("tr", null,
        h("th", { scope: "col", text: "Competency" }), h("th", { scope: "col", text: "Mark" }),
        h("th", { scope: "col", text: "Rating" }), h("th", { scope: "col", text: "What your answer showed / next step" }))),
      h("tbody"));
    var body = table.querySelector("tbody");
    o.competencies.forEach(function (c) {
      var meter = h("div", { class: "meter", "aria-hidden": "true" }, h("i", { style: "width:" + (c.mark_percent || 0) + "%" }));
      body.appendChild(h("tr", null,
        h("td", { "data-label": "Competency" }, h("strong", { text: c.id + " " + c.name })),
        h("td", { "data-label": "Mark" }, h("span", { text: pct(c.mark_percent) }), meter),
        h("td", { "data-label": "Rating" }, h("span", { class: "badge small " + rclass(c.rating), text: c.rating || "—" })),
        h("td", { "data-label": "What your answer showed / next step", text: c.note })));
    });
    wrap.appendChild(h("div", { class: "card" }, h("h2", { text: "Competency scorecard" }), table));

    // outcome
    wrap.appendChild(h("div", { class: "grid2" },
      h("div", { class: "card" }, h("h2", { text: "Strengths" }), list(o.strengths)),
      h("div", { class: "card" }, h("h2", { text: "Skills to practice" }), list(o.skills)),
      h("div", { class: "card" }, h("h2", { text: "Try this next" }), h("p", { text: o.try_next })),
      h("div", { class: "card" }, h("h2", { text: "Teacher support" }), h("p", { text: o.teacher_support }))));

    wrap.appendChild(h("p", { class: "muted small guide", text: o.rating_guide }));
    wrap.appendChild(h("div", { class: "nav noprint" }, h("span"),
      h("button", { class: "btn ghost", type: "button", text: "Print", onclick: function () { window.print(); } })));
    app.replaceChildren(wrap);
  }

  function missing() {
    app.replaceChildren(h("div", { class: "card" },
      h("h2", { text: "We can't find this scorecard" }),
      h("p", { class: "muted", text: "The link may be incomplete, or a newer assessment has replaced it (this demo keeps only the latest result), or the demo was restarted. Please take the assessment again." }),
      h("a", { class: "btn linkbtn", href: "./", text: "Take the assessment" })));
  }

  var id = new URLSearchParams(window.location.search).get("id") || "";
  if (!/^[A-Za-z0-9_-]{16,40}$/.test(id)) { missing(); return; }
  fetch("api/outcome/" + encodeURIComponent(id)).then(function (r) {
    if (!r.ok) throw new Error("none");
    return r.json();
  }).then(render).catch(missing);
})();
