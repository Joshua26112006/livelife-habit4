// V5 Kinetic Editorial: masked line reveal, cursor glow, glass lens preview that follows the cursor over rows.
(function () {
  const reduce = window.AIDA_REDUCE;
  if (reduce || !window.AIDA_MOTION) return;
  document.documentElement.classList.add("js-motion");
  gsap.registerPlugin(SplitText);
  const fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  // Soft blue light follows the cursor.
  const glow = document.querySelector(".glow");
  const gx = gsap.quickTo(glow, "x", { duration: 1.2, ease: "power3.out" });
  const gy = gsap.quickTo(glow, "y", { duration: 1.2, ease: "power3.out" });
  gsap.set(glow, { x: innerWidth * 0.7, y: innerHeight * 0.3 });

  // Lens preview.
  const lens = document.querySelector(".lens");
  const lx = gsap.quickTo(lens, "x", { duration: 0.45, ease: "power3.out" });
  const ly = gsap.quickTo(lens, "y", { duration: 0.45, ease: "power3.out" });
  // The lens rides along the hovered row's title line, so it never covers the description below it.
  let activeTitle = null;
  const titleY = () => { const r = activeTitle.getBoundingClientRect(); return r.top + r.height / 2; };
  window.addEventListener("pointermove", (e) => {
    gx(e.clientX); gy(e.clientY);
    if (activeTitle) { lx(Math.min(e.clientX, innerWidth - 300)); ly(titleY()); }
  }, { passive: true });
  if (fine) {
    document.querySelectorAll(".row").forEach((row) => {
      row.addEventListener("pointerenter", (e) => {
        activeTitle = row.querySelector(".row-title");
        lens.classList.toggle("on-1", row.dataset.lens === "1");
        gsap.set(lens, { x: Math.min(e.clientX, innerWidth - 300), y: titleY() });
        gsap.to(lens, { opacity: 1, scale: 1, duration: 0.35, ease: "expo.out", overwrite: "auto" });
      });
      row.addEventListener("pointerleave", () => {
        gsap.to(lens, { opacity: 0, scale: 0.85, duration: 0.2, ease: "power2.out", overwrite: "auto" });
      });
    });
  }

  // Intro: headline chars, then the two big titles rise out of their masks.
  const hello = new SplitText(".hello", { type: "chars,words", mask: "words" });
  // .row-title has overflow:hidden, so each title rises out of its own mask (no split: keeps the gradient text fill).
  gsap.timeline({ defaults: { ease: "expo.out" } })
    .to(".top", { opacity: 1, duration: 0.6 }, 0)
    .from(hello.chars, { yPercent: 110, duration: 0.9, stagger: 0.015 }, 0.05)
    .fromTo(".ask", { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.7 }, 0.3)
    .to(".rows", { opacity: 1, duration: 0.01 }, 0.35)
    .from(".fill", { yPercent: 105, duration: 1.1, stagger: 0.12, clearProps: "transform" }, 0.4)
    .fromTo(".row-side", { opacity: 0, x: 20 }, { opacity: 1, x: 0, duration: 0.8, stagger: 0.12 }, 0.7);

  window.AIDA_EXIT = (_id, el) => new Promise((done) => {
    const other = [...document.querySelectorAll(".row")].filter((r) => r !== el);
    gsap.timeline({ onComplete: done })
      .to(lens, { opacity: 0, duration: 0.15 }, 0)
      .to([other, ".intro", ".top"], { opacity: 0, duration: 0.25 }, 0)
      .to(el.querySelector(".fill"), { backgroundPosition: "0% 0", xPercent: 4, duration: 0.4, ease: "expo.out" }, 0)
      .to(".page", { opacity: 0, y: -20, duration: 0.3, ease: "power2.in" }, 0.2);
  });
  window.AIDA_RESET = () => {
    gsap.set([".row", ".intro", ".top", ".page"], { opacity: 1, clearProps: "transform" });
    gsap.set(".fill", { clearProps: "backgroundPosition,xPercent" });
  };
})();
