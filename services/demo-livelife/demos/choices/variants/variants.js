// Shared behaviour for the four layout variants: pointer sheen on choice cards, calm exit, Back restore.
// Navigation, the "is it live" check and the toast come from shared/choices.js.
(function () {
  const reduce = window.AIDA_REDUCE;
  document.querySelectorAll("[data-go]").forEach((el) => {
    el.addEventListener("pointermove", (e) => {
      const r = el.getBoundingClientRect();
      el.style.setProperty("--mx", e.clientX - r.left + "px");
      el.style.setProperty("--my", e.clientY - r.top + "px");
    }, { passive: true });
  });
  window.AIDA_EXIT = (_id, el) => new Promise((done) => {
    if (reduce) return done();
    document.querySelectorAll("[data-go]").forEach((o) => { if (o !== el) o.style.opacity = "0.35"; });
    el.style.transform = "scale(1.02)";
    const page = document.querySelector(".page");
    if (page) { page.style.transition = "opacity 260ms ease 120ms"; page.style.opacity = "0"; }
    setTimeout(done, 380);
  });
  window.AIDA_RESET = () => {
    document.querySelectorAll("[data-go], .page").forEach((e) => { e.style.opacity = ""; e.style.transform = ""; e.style.transition = ""; });
  };
})();
