// LiveLife Habit 4 "Think Win-Win" — student assessment (demo). Plain JavaScript, no framework, no storage in the browser.
// Flow (from the LiveLife document), laid out like a form: name and grade -> Part 1, Knowledge Check (all 9 questions on
// one page) -> Part 2, Situational Check (all 8 situations on one page) -> submit -> a thank-you page with NO marks and a
// link to the scorecard, which is a separate page (outcome.html?id=...).
// What the student types lives in this variable only; closing the tab forgets it.
// Relative URLs on purpose: the page sits behind /demo-livelife/livelife-student/ (the service adds a <base> tag).
// Text from the server or from a model is only ever put on the page with textContent, never as markup.
(function () {
  "use strict";

  var SCORE_URL = "../../api/demo-livelife-score"; // the website's AI scorer (off unless a person switches it on)
  var MAX_ANSWER = 600;
  var INTRO = 0, PART1 = 1, PART2 = 2;

  var app = document.getElementById("app");
  var progress = document.getElementById("progress");
  var bar = document.getElementById("bar");

  var items = null, at = INTRO, busy = false, S = null;

  function fresh() { return { name: "", grade: "", mcq: {}, answers: {} }; }

  // ---- tiny DOM helper ----------------------------------------------------------------------------------------
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
  function show(node) { app.replaceChildren(node); window.scrollTo(0, 0); }

  // ---- progress: how much of the form is filled in ------------------------------------------------------------
  function mcqAnswered() { return items.mcqs.filter(function (q) { return S.mcq[q.id]; }).length; }
  function scenAnswered() { return items.scenarios.filter(function (s) { return (S.answers[s.id] || "").trim(); }).length; }
  function setBar() {
    if (!items || at === INTRO) { progress.hidden = true; return; }
    progress.hidden = false;
    var total = items.mcqs.length + items.scenarios.length;
    bar.style.width = Math.round(((mcqAnswered() + scenAnswered()) / total) * 100) + "%";
  }

  function go(n) { at = n; render(); }
  function render() {
    setBar();
    if (at === INTRO) return renderIntro();
    if (at === PART1) return renderPart1();
    return renderPart2();
  }

  function nav(onBack, onNext, nextLabel, nextButtonRef) {
    var next = h("button", { class: "btn", type: "button", text: nextLabel || "Next", onclick: onNext });
    if (nextButtonRef) nextButtonRef.el = next;
    return h("div", { class: "nav" },
      onBack ? h("button", { class: "btn ghost", type: "button", text: "Back", onclick: onBack }) : h("span"), next);
  }

  // ---- page 1: who is taking it -------------------------------------------------------------------------------
  function renderIntro() {
    var name = h("input", { type: "text", id: "f-name", maxlength: "40", autocomplete: "off", value: S.name, "aria-label": "Your name" });
    var grade = h("input", { type: "text", id: "f-grade", maxlength: "12", autocomplete: "off", value: S.grade, placeholder: "for example 8", "aria-label": "Your grade" });
    var start = h("button", { class: "btn", type: "button", text: "Start", onclick: function () { go(PART1); } });
    function check() { start.disabled = !(name.value.trim() && grade.value.trim()); }
    name.addEventListener("input", function () { S.name = name.value; check(); });
    grade.addEventListener("input", function () { S.grade = grade.value; check(); });
    check();
    show(h("div", null,
      h("div", { class: "card formhead" },
        h("span", { class: "tag", text: "Level 5 · Habit 4" }),
        h("h1", { text: "Think Win-Win" }),
        h("p", { text: "Part 1 is " + items.mcqs.length + " quick questions. Part 2 is " + items.scenarios.length + " real-life situations to answer in your own words. Then you can see your scorecard." }),
        h("p", { class: "muted", text: "Take your time. Write what you really think: there is no trick. Spelling and grammar don't matter." })),
      h("div", { class: "card" },
        h("label", { class: "f", for: "f-name", text: "Your name" }), name,
        h("label", { class: "f", for: "f-grade", text: "Your grade" }), grade,
        h("p", { class: "muted small", style: "margin-top:12px", text: "Demo: please use made-up details, not your real name or school." })),
      h("div", { class: "nav" }, h("span"), start)));
  }

  // ---- page 2: Part 1, all nine questions, like a form -------------------------------------------------------
  function renderPart1() {
    var wrap = h("div", null);
    wrap.appendChild(h("div", { class: "card formhead" },
      h("span", { class: "tag", text: "Part 1 of 2" }),
      h("h1", { text: "Knowledge Check" }),
      h("p", { class: "muted", text: "Choose one answer for each of the " + items.mcqs.length + " questions." })));

    var count = h("div", { class: "answered", "aria-live": "polite" });
    var ref = {};

    function refresh() {
      var n = mcqAnswered();
      count.textContent = n + " of " + items.mcqs.length + " answered";
      if (ref.el) ref.el.disabled = n < items.mcqs.length;
      setBar();
    }

    items.mcqs.forEach(function (q, i) {
      var group = h("div", { class: "choices", role: "radiogroup", "aria-labelledby": "stem-" + q.id });
      Object.keys(q.options).forEach(function (letter) {
        var rid = "r-" + q.id + "-" + letter;
        var input = h("input", { type: "radio", name: "q-" + q.id, id: rid, value: letter, checked: S.mcq[q.id] === letter });
        input.addEventListener("change", function () { S.mcq[q.id] = letter; refresh(); });
        group.appendChild(h("label", { class: "choice", for: rid },
          input, h("span", { class: "letter", text: letter }), h("span", { class: "choice-text", text: q.options[letter] })));
      });
      wrap.appendChild(h("div", { class: "card qcard" },
        h("div", { class: "qnum", text: "Question " + (i + 1) }),
        h("div", { class: "stem", id: "stem-" + q.id, text: q.stem }), group));
    });

    var footer = nav(function () { go(INTRO); }, function () { go(PART2); }, "Next", ref);
    wrap.appendChild(count);
    wrap.appendChild(footer);
    refresh();
    show(wrap);
  }

  // ---- page 3: Part 2, all eight situations, like a form ------------------------------------------------------
  function renderPart2() {
    var wrap = h("div", null);
    wrap.appendChild(h("div", { class: "card formhead" },
      h("span", { class: "tag", text: "Part 2 of 2" }),
      h("h1", { text: "Situations" }),
      h("p", { class: "muted", text: "Answer each one in your own words. A short answer is fine. You can leave one blank if you are not sure, but then it can't be scored." })));

    var count = h("div", { class: "answered", "aria-live": "polite" });
    function refresh() {
      var n = scenAnswered(), total = items.scenarios.length;
      count.textContent = n + " of " + total + " answered" + (n < total ? " (blank ones will count as no answer)" : "");
      setBar();
    }

    items.scenarios.forEach(function (s, i) {
      var ta = h("textarea", { id: "t-" + s.id, maxlength: String(MAX_ANSWER), "aria-labelledby": "stem-" + s.id, placeholder: "Write your answer here…" });
      ta.value = S.answers[s.id] || "";
      var chars = h("div", { class: "count", text: ta.value.length + " / " + MAX_ANSWER });
      ta.addEventListener("input", function () {
        S.answers[s.id] = ta.value;
        chars.textContent = ta.value.length + " / " + MAX_ANSWER;
        refresh();
      });
      wrap.appendChild(h("div", { class: "card qcard" },
        h("div", { class: "qnum", text: "Situation " + (i + 1) }),
        h("div", { class: "stem", id: "stem-" + s.id, text: s.question }), ta, chars));
    });

    wrap.appendChild(count);
    wrap.appendChild(nav(function () { go(PART1); }, submit, "Submit"));
    refresh();
    show(wrap);
  }

  // ---- submit -------------------------------------------------------------------------------------------------
  function postJSON(url, body) {
    return fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  }

  // The eight scenario answers go to the website's scorer as ONE call. Never throws: null means "no scores".
  function scoreAll() {
    return postJSON(SCORE_URL, { answers: S.answers }).then(function (r) {
      if (!r.ok) return null; // off (404), busy (429) or an error: the scorecard will say the answers weren't scored
      return r.json().then(function (j) { return j && j.ok ? { results: j.results, summary: j.summary || null } : null; }, function () { return null; });
    }, function () { return null; });
  }

  function submit() {
    if (busy) return;
    busy = true;
    progress.hidden = true;
    show(h("div", { class: "card hero" }, h("div", { class: "spin" }), h("h2", { text: "Submitting your answers…" }),
      h("p", { class: "muted", text: "This can take a few seconds. Please don't close this page." })));
    scoreAll().then(function (scored) {
      return postJSON("api/submit", { name: S.name, grade: S.grade, mcq: S.mcq, answers: S.answers, scored: scored });
    }).then(function (r) {
      if (!r.ok) throw new Error("submit");
      return r.json();
    }).then(function (j) {
      busy = false;
      renderThanks(j.id);
    }).catch(function () {
      busy = false;
      show(h("div", { class: "card" }, h("h2", { text: "We couldn't submit just now" }),
        h("p", { text: "Your answers are still here. Please try again." }),
        nav(function () { go(PART2); }, submit, "Try again")));
    });
  }

  // The thank-you page: the document's sentence, and NO marks or rating. The scorecard is a separate page.
  function renderThanks(id) {
    progress.hidden = true;
    show(h("div", null,
      h("div", { class: "card hero" },
        h("h1", { text: items.thank_you }),
        h("p", { class: "muted", text: "Your scorecard is on its own page." }),
        h("a", { class: "btn linkbtn", href: "outcome.html?id=" + encodeURIComponent(id), text: "View my scorecard" })),
      h("div", { class: "nav noprint" }, h("span"),
        h("button", { class: "btn ghost", type: "button", text: "Start again", onclick: function () { S = fresh(); go(INTRO); } }))));
  }

  // ---- start --------------------------------------------------------------------------------------------------
  S = fresh();
  fetch("api/items").then(function (r) { return r.json(); }).then(function (j) {
    items = j; go(INTRO);
  }).catch(function () {
    show(h("div", { class: "card" }, h("h2", { text: "This page can't start right now" }), h("p", { class: "muted", text: "Please try again in a moment." })));
  });
})();
