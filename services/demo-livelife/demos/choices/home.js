// Teacher entry page: a short, calm exit before opening the chosen destination (CSS-driven, no libraries).
(function () {
  const reduce = window.AIDA_REDUCE;
  window.AIDA_EXIT = (_id, el) => new Promise((done) => {
    if (reduce) return done();
    el.style.transition = "transform 220ms cubic-bezier(0.23, 1, 0.32, 1), box-shadow 220ms ease";
    el.style.transform = "scale(1.015)";
    document.querySelectorAll(".option").forEach((o) => { if (o !== el) o.style.opacity = "0.4"; });
    const shell = document.querySelector(".shell");
    shell.style.transition = "opacity 260ms ease 120ms";
    shell.style.opacity = "0";
    setTimeout(done, 380);
  });
  window.AIDA_RESET = () => {
    document.querySelectorAll(".option, .shell").forEach((e) => { e.style.opacity = ""; e.style.transform = ""; e.style.transition = ""; });
  };
})();
