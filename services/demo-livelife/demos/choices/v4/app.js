// V4 Spatial: window tilts with the pointer (gsap.quickTo), tiles get a spotlight, arrow buttons are magnetic.
(function () {
  const tiles = [...document.querySelectorAll(".tile")];

  tiles.forEach((t) => {
    t.addEventListener("pointermove", (e) => {
      const r = t.getBoundingClientRect();
      t.style.setProperty("--mx", e.clientX - r.left + "px");
      t.style.setProperty("--my", e.clientY - r.top + "px");
    }, { passive: true });
  });

  if (!window.AIDA_MOTION) return;
  document.documentElement.classList.add("js-motion");
  const fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  // Tilt the whole window, max 5 degrees, spring-like follow.
  const wrap = document.querySelector(".window-wrap");
  if (fine) {
    const rx = gsap.quickTo(wrap, "rotationX", { duration: 0.8, ease: "power3.out" });
    const ry = gsap.quickTo(wrap, "rotationY", { duration: 0.8, ease: "power3.out" });
    // Tilt only while the pointer is over the window; lie flat (sharp text) at rest.
    const win = document.querySelector(".window");
    win.addEventListener("pointermove", (e) => {
      const r = win.getBoundingClientRect();
      const nx = (e.clientX - r.left) / r.width - 0.5, ny = (e.clientY - r.top) / r.height - 0.5;
      ry(nx * 4); rx(-ny * 3);
    }, { passive: true });
    win.addEventListener("pointerleave", () => { rx(0); ry(0); });

    // Magnetic arrow buttons (after React Bits Magnet, reimplemented with quickTo).
    tiles.forEach((t) => {
      const go = t.querySelector(".go");
      const gx = gsap.quickTo(go, "x", { duration: 0.5, ease: "power3.out" });
      const gy = gsap.quickTo(go, "y", { duration: 0.5, ease: "power3.out" });
      t.addEventListener("pointermove", (e) => {
        const r = go.getBoundingClientRect();
        gx((e.clientX - (r.left + r.width / 2)) * 0.18);
        gy((e.clientY - (r.top + r.height / 2)) * 0.18);
      }, { passive: true });
      t.addEventListener("pointerleave", () => { gx(0); gy(0); });
    });
  }

  gsap.registerPlugin(SplitText);
  const split = new SplitText(".hello", { type: "words" });
  gsap.timeline({ defaults: { ease: "expo.out" } })
    .fromTo(".window", { opacity: 0, y: 60, rotationX: 14, scale: 0.94, transformOrigin: "50% 100%" },
      { opacity: 1, y: 0, rotationX: 0, scale: 1, duration: 1.3, clearProps: "transform" }, 0)
    .from(split.words, { opacity: 0, filter: "blur(10px)", y: 14, duration: 0.8, stagger: 0.07 }, 0.35)
    .from(".tile", { opacity: 0, z: -80, y: 20, duration: 0.9, stagger: 0.08, clearProps: "transform" }, 0.5)
    .fromTo(".grab", { opacity: 0, scaleX: 0.4 }, { opacity: 1, scaleX: 1, duration: 0.7 }, 0.8)
    .fromTo(".ornament", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.8 }, 0.9);

  window.AIDA_EXIT = (_id, el) => new Promise((done) => {
    const other = tiles.filter((t) => t !== el);
    gsap.timeline({ onComplete: done })
      .to([other, ".w-head", ".ornament", ".grab"], { opacity: 0, duration: 0.25 }, 0)
      .to(el, { z: 120, duration: 0.45, ease: "expo.out" }, 0)
      .to(".window", { opacity: 0, scale: 1.04, duration: 0.3, ease: "power2.in" }, 0.2);
  });
  window.AIDA_RESET = () => {
    gsap.set([".tile", ".w-head", ".ornament", ".grab", ".window"], { opacity: 1, clearProps: "transform" });
  };
})();
