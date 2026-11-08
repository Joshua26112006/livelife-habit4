// Reads generated/habit4.json (made by app.py). Serve this folder with:  python -m http.server 8000
    const PHASES = [
      { key: "think_cards", emoji: "🔦", name: "Engagement",    color: "#D97706", pill: "Engagement Phase" },
      { key: "blog",        emoji: "📖", name: "Understanding", color: "#4F46E5", pill: "Understanding Phase" },
      { key: "quiz",        emoji: "⚡", name: "Mastery",       color: "#DC2626", pill: "Mastery Phase" },
      { key: "flashcards",  emoji: "✨", name: "Retention",     color: "#059669", pill: "Retention Phase" }];
    const view = document.getElementById("view"), tabs = document.getElementById("tabs");
    let data = null, tab = "think_cards", visited = new Set(), idx = { think_cards: 0, quiz: 0, flashcards: 0 };
    let score = 0, answered = {}, flipped = false;

    const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
    const frame = (emoji, counter, inner, img) =>
      `<div class="card"><div class="hero"><div class="win"><i></i><i></i><i></i></div>${counter ? `<div class="counter">${counter}</div>` : ""}${img ? `<img src="${esc(img)}" alt="">` : emoji}</div><div class="body">${inner}</div></div>`;
    const nav = (i, n, last) =>
      `<div class="nav"><button class="btn" data-nav="-1" ${i === 0 ? "disabled" : ""}>‹ Back</button>` +
      `<button class="btn go" data-nav="1" ${i === n - 1 ? "disabled" : ""}>${last || "Next ›"}</button></div>`;

    function chrome() {
      document.body.dataset.phase = tab;
      const ph = PHASES.find(p => p.key === tab);
      document.getElementById("pill").textContent = ph.emoji + "  " + ph.pill;
      tabs.innerHTML = PHASES.map((p, i) =>
        (i ? '<span class="line"></span>' : "") +
        `<button class="tab" role="tab" data-tab="${p.key}" aria-selected="${p.key === tab}">${p.emoji} ${p.name}</button>`).join("");
      document.getElementById("dots").innerHTML = PHASES.map(p =>
        `<span class="dot ${visited.has(p.key) ? "done" : ""}" style="color:${p.color}"></span>`).join("");
      document.getElementById("count").textContent = visited.size + "/4";
      document.getElementById("bar").style.width = visited.size * 25 + "%";
    }

    function render() {
      visited.add(tab); chrome();
      if (tab === "think_cards") {
        const i = idx.think_cards, c = data.think_cards[i], n = data.think_cards.length;
        view.innerHTML = frame("🤔", `${i + 1}/${n}`,
          `<p class="kicker">🤔 Think about it…</p><p class="big">${esc(c.title)}</p><p class="text">${esc(c.scenario)}</p>` +
          `<p class="big" style="font-size:20px">${esc(c.question)}</p><textarea placeholder="Type your win-win idea here…"></textarea>`, c.image) + nav(i, n);
      } else if (tab === "blog") {
        view.innerHTML = `<h2 class="title" style="font-size:22px">${esc(data.blog.title)}</h2>` +
          data.blog.sections.map((s, i) => frame(["📖", "🤝", "🏦", "⭐"][i % 4], `${i + 1}/${data.blog.sections.length}`,
            `<p class="kicker">${esc(s.heading)}</p><p class="text" style="font-size:18px">${esc(s.body)}</p>`, s.image)).join("");
      } else if (tab === "quiz") {
        const n = data.quiz.length, i = idx.quiz;
        if (i >= n) {
          view.innerHTML = frame("🏆", "", `<div class="score"><b>${score}/${n}</b><p class="big">Quiz complete</p></div>`) +
            `<div class="nav"><button class="btn" data-restart>Try again</button><span></span></div>`;
          return;
        }
        const q = data.quiz[i], done = answered[i];
        view.innerHTML = frame("⚡", `${i + 1}/${n}`,
          `<p class="kicker">Test your knowledge</p><p class="big">${esc(q.question)}</p>` +
          q.options.map((o, j) => `<button class="opt ${done ? (j === q.answer_index ? "right" : done.pick === j ? "wrong" : "") : ""}" data-j="${j}" ${done ? "disabled" : ""}><span class="ltr">${"ABCD"[j]}</span>${esc(o)}</button>`).join("") +
          (done ? `<p class="why">${esc(q.why)}</p>` : "")) +
          `<div class="nav"><button class="btn" data-nav="-1" ${i === 0 ? "disabled" : ""}>‹ Back</button><button class="btn go" data-nav="1" ${done ? "" : "disabled"}>${i === n - 1 ? "Finish" : "Next ›"}</button></div>`;
      } else {
        const i = idx.flashcards, f = data.flashcards[i], n = data.flashcards.length;
        view.innerHTML = frame("✨", `${i + 1}/${n}`,
          `<div class="flip" data-flip><div><p class="big" style="margin:0">${esc(flipped ? f.back : f.front)}</p><span class="hint">${flipped ? "answer" : "tap to flip"}</span></div></div>`, f.image) + nav(i, n);
      }
    }

    document.addEventListener("click", e => {
      if (!data) return;
      const t = e.target.closest("[data-tab]"), nv = e.target.closest("[data-nav]"), op = e.target.closest(".opt");
      if (t) { tab = t.dataset.tab; flipped = false; render(); }
      else if (nv) { idx[tab] += +nv.dataset.nav; flipped = false; render(); }
      else if (op && !op.disabled) { const i = idx.quiz, j = +op.dataset.j; answered[i] = { pick: j }; if (j === data.quiz[i].answer_index) score++; render(); }
      else if (e.target.closest("[data-flip]")) { flipped = !flipped; render(); }
      else if (e.target.closest("[data-restart]")) { idx.quiz = 0; score = 0; answered = {}; render(); }
    });

    fetch("generated/habit4.json").then(r => { if (!r.ok) throw 0; return r.json(); })
      .then(j => { data = j; render(); })
      .catch(() => { chrome(); view.innerHTML = '<p class="empty">No generated content yet. Run <code>python app.py</code>, then serve this folder with <code>python -m http.server 8000</code>.</p>'; });
