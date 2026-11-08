// V3 Win-Win Venn: blur-in headline, circles slide together to form the overlap.
(function () {
  if (!window.AIDA_MOTION) return;
  document.documentElement.classList.add("js-motion");
  gsap.registerPlugin(SplitText);
  const split = new SplitText(".hello", { type: "words" });
  const mobile = window.matchMedia("(max-width: 820px)").matches;
  const tl = gsap.timeline({ defaults: { ease: "expo.out" } });
  tl.to(".top", { opacity: 1, duration: 0.6 }, 0)
    .from(split.words, { opacity: 0, filter: "blur(12px)", y: 18, duration: 0.9, stagger: 0.08 }, 0.05)
    .fromTo(".ask", { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.7 }, 0.3)
    .fromTo(".c-self", { opacity: 0, x: mobile ? 0 : -90, y: mobile ? -60 : 0 }, { opacity: 1, x: 0, y: 0, duration: 1.2, clearProps: "transform" }, 0.35)
    .fromTo(".c-class", { opacity: 0, x: mobile ? 0 : 90, y: mobile ? 60 : 0 }, { opacity: 1, x: 0, y: 0, duration: 1.2, clearProps: "transform" }, 0.35)
    .fromTo(".overlap", { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.6, ease: "back.out(2)", clearProps: "scale" }, 0.95);

  window.AIDA_EXIT = (_id, el) => new Promise((done) => {
    const other = [...document.querySelectorAll(".circle")].filter((c) => c !== el);
    gsap.timeline({ onComplete: done })
      .to([".overlap", ".head", other], { opacity: 0, duration: 0.25 }, 0)
      .to(el, { scale: 1.08, duration: 0.45, ease: "expo.out" }, 0)
      .to("body", { opacity: 0, duration: 0.25 }, 0.2);
  });
  window.AIDA_RESET = () => {
    gsap.set(["body", ".overlap", ".head", ".circle"], { opacity: 1 });
    gsap.set(".circle", { clearProps: "transform" });
  };
})();
