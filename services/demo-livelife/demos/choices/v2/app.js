// V2 Split Worlds: intro + the chosen half takes the whole screen on exit.
(function () {
  if (!window.AIDA_MOTION) return;
  document.documentElement.classList.add("js-motion");
  gsap.registerPlugin(SplitText);

  const words = [...document.querySelectorAll(".word")];
  const splits = words.map((w) => new SplitText(w, { type: "chars", mask: "chars" }));
  const tl = gsap.timeline({ defaults: { ease: "expo.out" } });
  tl.fromTo(".side-a", { clipPath: "inset(0 0 100% 0)" }, { clipPath: "inset(0 0 0% 0)", duration: 1.1, ease: "expo.inOut" }, 0)
    .fromTo(".side-b", { clipPath: "inset(100% 0 0 0)" }, { clipPath: "inset(0% 0 0 0)", duration: 1.1, ease: "expo.inOut" }, 0.06)
    .from(splits[0].chars, { yPercent: 105, duration: 1, stagger: 0.03 }, 0.55)
    .from(splits[1].chars, { yPercent: -105, duration: 1, stagger: 0.03 }, 0.6)
    .fromTo(".bar", { opacity: 0, y: -14 }, { opacity: 1, y: 0, duration: 0.8 }, 0.75)
    .fromTo(".panel", { opacity: 0, y: 28 }, { opacity: 1, y: 0, duration: 0.9, stagger: 0.08, clearProps: "transform" }, 0.8)
    .add(() => gsap.set([".side-a", ".side-b"], { clearProps: "clipPath" }));

  window.AIDA_EXIT = (_id, el) => new Promise((done) => {
    const other = [...document.querySelectorAll(".side")].filter((s) => s !== el);
    gsap.timeline({ onComplete: done })
      .to(".bar", { opacity: 0, y: -10, duration: 0.25 }, 0)
      .to(el.querySelector(".panel"), { opacity: 0, y: 12, duration: 0.25 }, 0)
      .to(other, { flexGrow: 0.0001, duration: 0.55, ease: "expo.inOut" }, 0)
      .to(el, { flexGrow: 1, duration: 0.55, ease: "expo.inOut" }, 0);
  });
  window.AIDA_RESET = () => {
    gsap.set(".side", { clearProps: "flexGrow" });
    gsap.set([".bar", ".panel"], { opacity: 1, y: 0 });
  };
})();
