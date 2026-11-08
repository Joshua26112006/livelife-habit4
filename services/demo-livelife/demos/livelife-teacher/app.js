// LiveLife Habit 4 "Think Win-Win" — TEACHER assessment (demo). Plain JavaScript, no framework, no storage in the browser.
// Flow (from the LiveLife Section 9 document), laid out like a form: name/ID and school -> all eight situational questions on
// one page -> submit -> a thank-you page with NO scores or recommendation and a link to the outcome, which is a separate page
// (outcome.html?id=...). What the teacher types lives in this variable only; closing the tab forgets it.
// Relative URLs on purpose: the page sits behind /demo-livelife/livelife-teacher/ (the service adds a <base> tag).
// Text from the server or from a model is only ever put on the page with textContent, never as markup.
(function () {
  "use strict";

  var SCORE_URL = "../../api/demo-livelife-score"; // the website's AI scorer (off unless a person switches it on)
  var MAX_ANSWER = 800;
  var INTRO = 0, QUESTIONS = 1;

  var app = document.getElementById("app");
  var progress = document.getElementById("progress");
  var bar = document.getElementById("bar");

  var items = null, at = INTRO, busy = false, S = null;

  function fresh() { return { name: "", school: "", answers: {} }; }

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

  function answered() { return items.questions.filter(function (q) { return (S.answers[q.id] || "").trim(); }).length; }
  function setBar() {
    if (!items || at === INTRO) { progress.hidden = true; return; }
    progress.hidden = false;
    bar.style.width = Math.round((answered() / items.questions.length) * 100) + "%";
  }

  function go(n) { at = n; render(); }
  function render() { setBar(); return at === INTRO ? renderIntro() : renderQuestions(); }

  function nav(onBack, onNext, nextLabel) {
    return h("div", { class: "nav" },
      onBack ? h("button", { class: "btn ghost", type: "button", text: "Back", onclick: onBack }) : h("span"),
      h("button", { class: "btn", type: "button", text: nextLabel || "Next", onclick: onNext }));
  }

  // ---- page 1: who is taking it -------------------------------------------------------------------------------
  function renderIntro() {
    var name = h("input", { type: "text", id: "f-name", maxlength: "60", autocomplete: "off", value: S.name, "aria-label": "Your name or ID" });
    var school = h("input", { type: "text", id: "f-school", maxlength: "80", autocomplete: "off", value: S.school, "aria-label": "Your school" });
    var start = h("button", { class: "btn", type: "button", text: "Start", onclick: function () { go(QUESTIONS); } });
    function check() { start.disabled = !(name.value.trim() && school.value.trim()); }
    name.addEventListener("input", function () { S.name = name.value; check(); });
    school.addEventListener("input", function () { S.school = school.value; check(); });
    check();
    show(h("div", null,
      h("div", { class: "card formhead" },
        h("span", { class: "tag", text: "Habit 4 · Teacher facilitation" }),
        h("h1", { text: "Teacher assessment: Think Win-Win" }),
        h("p", { text: "Eight short situations from a Habit 4 lesson. Answer each in your own words, in a few sentences. This checks how ready you are to facilitate Habit 4 accurately and inclusively." }),
        h("p", { class: "muted", text: "There is no word count and no marks for grammar. Say what you would actually do or say." })),
      h("div", { class: "card" },
        h("label", { class: "f", for: "f-name", text: "Your name or ID" }), name,
        h("label", { class: "f", for: "f-school", text: "Your school" }), school,
        h("p", { class: "muted small", style: "margin-top:12px", text: "Demo: please use made-up details, not your real name or school." })),
      h("div", { class: "nav" }, h("span"), start)));
  }

  // ---- page 2: the eight questions, like a form ---------------------------------------------------------------
  function renderQuestions() {
    var wrap = h("div", null);
    wrap.appendChild(h("div", { class: "card formhead" },
      h("span", { class: "tag", text: "Situational questions" }),
      h("h1", { text: "Eight situations" }),
      h("p", { class: "muted", text: "Answer each one in two to five sentences. A short, clear answer is fine." })));

    var count = h("div", { class: "answered", "aria-live": "polite" });
    function refresh() {
      var n = answered(), total = items.questions.length;
      count.textContent = n + " of " + total + " answered" + (n < total ? " (blank ones will count as no answer)" : "");
      setBar();
    }

    items.questions.forEach(function (q, i) {
      var ta = h("textarea", { id: "t-" + q.id, maxlength: String(MAX_ANSWER), "aria-labelledby": "stem-" + q.id, placeholder: "Write your answer here…" });
      ta.value = S.answers[q.id] || "";
      var chars = h("div", { class: "count", text: ta.value.length + " / " + MAX_ANSWER });
      ta.addEventListener("input", function () {
        S.answers[q.id] = ta.value;
        chars.textContent = ta.value.length + " / " + MAX_ANSWER;
        refresh();
      });
      wrap.appendChild(h("div", { class: "card qcard" },
        h("div", { class: "qnum", text: "Situation " + (i + 1) }),
        h("div", { class: "stem", id: "stem-" + q.id, text: q.question }), ta, chars));
    });

    wrap.appendChild(count);
    wrap.appendChild(nav(function () { go(INTRO); }, submit, "Submit"));
    refresh();
    show(wrap);
  }

  // ---- submit -------------------------------------------------------------------------------------------------
  function postJSON(url, body) {
    return fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  }

  // The eight answers go to the website's scorer as ONE call, as kind "teacher". Never throws: null means "no scores".
  function scoreAll() {
    return postJSON(SCORE_URL, { kind: "teacher", answers: S.answers }).then(function (r) {
      if (!r.ok) return null; // off (404), busy (429) or an error: the outcome will say the answers weren't scored
      return r.json().then(function (j) { return j && j.ok ? { results: j.results, summary: j.summary || null } : null; }, function () { return null; });
    }, function () { return null; });
  }

  function submit() {
    if (busy) return;
    busy = true;
    progress.hidden = true;
    show(h("div", { class: "card hero" }, h("div", { class: "spin" }), h("h2", { text: "Submitting your assessment…" }),
      h("p", { class: "muted", text: "This can take a few seconds. Please don't close this page." })));
    scoreAll().then(function (scored) {
      return postJSON("api/submit", { name: S.name, school: S.school, answers: S.answers, scored: scored });
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
        nav(function () { go(QUESTIONS); }, submit, "Try again")));
    });
  }

  // The thank-you page: the document's message, and NO scores or recommendation. The outcome is a separate page.
  function renderThanks(id) {
    progress.hidden = true;
    show(h("div", null,
      h("div", { class: "card hero" },
        h("h1", { text: items.thank_you }),
        h("p", { class: "muted", text: "Your assessment outcome is on its own page." }),
        h("a", { class: "btn linkbtn", href: "outcome.html?id=" + encodeURIComponent(id), text: "View assessment outcome" })),
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
