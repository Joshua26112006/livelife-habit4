// Shared behaviour for every design version.
// - fills [data-aida] text from config.js
// - checks whether each destination is live; if not, shows a calm message instead of a 404
// - runs the version's exit animation before navigating
(function () {
  const A = window.AIDA;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const live = {};
  // Motion runs only if both libraries loaded; otherwise every version shows its content statically.
  const motion = !reduce && !!(window.gsap && window.SplitText);
  // Safety net: any script error reveals the page instead of leaving it hidden behind .js-motion.
  window.addEventListener("error", () => document.documentElement.classList.remove("js-motion"));

  // Text from config: <span data-aida="greeting"></span>, <span data-aida="choices.0.title"></span>
  document.querySelectorAll("[data-aida]").forEach((el) => {
    const v = el.dataset.aida.split(".").reduce((o, k) => (o == null ? o : o[k]), A);
    if (typeof v === "string") el.textContent = v;
  });
  // Icons: <i data-icon="arrow-right-light"></i>
  document.querySelectorAll("[data-icon]").forEach((el) => {
    const svg = window.AIDA_ICONS && window.AIDA_ICONS[el.dataset.icon];
    if (svg) el.innerHTML = svg;
  });

  // Is the destination there? Ask the demo service for its folder list (/demo-livelife -> {"demos":[...]}),
  // so a missing folder never shows a 404 in the console during the demo.
  // Ask for /demo-livelife without the trailing slash: the slash form redirects to an absolute (proxy-internal) host.
  const listUrl = new URL("..", document.baseURI).pathname.replace(/\/$/, "");
  const demoList = fetch(listUrl, { cache: "no-store" })
    .then((r) => (r.ok ? r.json() : { demos: [] }))
    .then((j) => (j.demos || []).map((d) => d.replace(/\/+$/, "").split("/").pop()))
    .catch(() => null);
  A.choices.forEach((c) => {
    if (c.href.startsWith("../../")) {
      // A page of the website (outside /demo-livelife): ask that page directly.
      // A redirect (e.g. to the login page when the route does not exist) counts as "not live".
      live[c.id] = fetch(new URL(c.href, document.baseURI), { cache: "no-store" }).then((r) => r.ok && !r.redirected).catch(() => false);
      return;
    }
    const folder = c.href.replace(/^\.\.\//, "").split("/")[0];
    // null = list unavailable: allow the click and let the destination answer.
    live[c.id] = demoList.then((names) => (names === null ? true : names.includes(folder)));
  });

  let toastEl, toastTimer;
  function toast(title, rest) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "aida-toast";
      toastEl.setAttribute("role", "status");
      document.body.appendChild(toastEl);
    }
    const strong = document.createElement("strong");
    strong.textContent = title;
    toastEl.replaceChildren(strong, document.createTextNode(rest));
    requestAnimationFrame(() => toastEl.classList.add("is-on"));
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove("is-on"), 3200);
  }

  let busy = false;
  async function go(id, sourceEl) {
    if (busy) return;
    const c = A.choices.find((x) => x.id === id);
    if (!c) return;
    busy = true; // set before the await so a double click cannot start two exits
    const ok = await live[id];
    if (!ok) {
      busy = false;
      toast(c.title, " is being connected. It will open here once it is live.");
      return;
    }
    // Pages define AIDA_EXIT only when their motion can run (v1-v5 inside their library guard; the home page is CSS-only).
    const exit = window.AIDA_EXIT && !reduce ? window.AIDA_EXIT(id, sourceEl) : null;
    if (exit && typeof exit.then === "function") {
      try { await exit; } catch (_) { /* navigate anyway */ }
    }
    window.location.href = c.href;
  }

  // Any element with data-go="self" | "class" becomes a choice.
  document.querySelectorAll("[data-go]").forEach((el) => {
    if (el.tagName === "A") el.setAttribute("href", A.choices.find((c) => c.id === el.dataset.go).href);
    el.addEventListener("click", (e) => {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button === 1) return; // let new-tab clicks through
      e.preventDefault();
      go(el.dataset.go, el);
    });
  });

  // Back/forward cache: undo the exit state when the teacher comes back.
  window.addEventListener("pageshow", (e) => {
    if (e.persisted) { busy = false; if (window.AIDA_RESET) window.AIDA_RESET(); }
  });

  // Comparison switcher (only with ?compare in the URL).
  if (new URLSearchParams(location.search).has("compare")) {
    const here = (document.body.dataset.version || "").toLowerCase();
    const nav = document.createElement("nav");
    nav.className = "aida-switcher is-on";
    nav.setAttribute("aria-label", "Design versions");
    nav.innerHTML = `<a href="compare.html">All</a>` + [1, 2, 3, 4, 5]
      .map((n) => `<a href="v${n}/?compare"${here === "v" + n ? ' aria-current="page"' : ""}>V${n}</a>`).join("");
    document.body.appendChild(nav);
  }

  window.AIDA_GO = go;
  window.AIDA_REDUCE = reduce;
  window.AIDA_MOTION = motion;
})();
