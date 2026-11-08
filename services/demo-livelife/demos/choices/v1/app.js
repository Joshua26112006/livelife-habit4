// V1 Liquid Glass: WebGL2 light field + pointer specular + Chromium edge refraction + GSAP intro.
(function () {
  const reduce = window.AIDA_REDUCE;
  const root = document.documentElement;

  /* ---------- 1. Light field (one canvas, one shader pass, half resolution) ---------- */
  const canvas = document.querySelector(".field");
  const gl = canvas.getContext("webgl2", { antialias: false, alpha: false, powerPreference: "low-power" });
  let draw = null;
  if (!gl) {
    root.classList.add("no-gl");
  } else {
    const vs = `#version 300 es
      in vec2 p; void main(){ gl_Position = vec4(p,0.,1.); }`;
    const fs = `#version 300 es
      precision highp float;
      uniform vec2 r; uniform float t; uniform vec2 m; out vec4 o;
      float h(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
      float n(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f);
        return mix(mix(h(i),h(i+vec2(1,0)),f.x), mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x), f.y); }
      float fbm(vec2 p){ float v=0., a=.5; for(int i=0;i<5;i++){ v+=a*n(p); p=p*2.02+vec2(1.7,9.2); a*=.5; } return v; }
      void main(){
        vec2 uv = gl_FragCoord.xy / r; vec2 p = (gl_FragCoord.xy - .5*r) / r.y;
        float tt = t*.045;
        vec2 q = vec2(fbm(p*1.4 + tt), fbm(p*1.4 - tt + 3.1));
        vec2 w = vec2(fbm(p*1.8 + 2.*q + vec2(1.7, 9.2) + tt*.6), fbm(p*1.8 + 2.*q + vec2(8.3, 2.8) - tt*.4));
        float f = fbm(p*1.3 + 2.4*w + (m - .5)*.35);
        f = smoothstep(.28, .72, f);                       // spread the noise into the full 0..1 range
        // light mass sits behind the cards (right-centre), calmer behind the headline (left)
        float mass = exp(-2.2 * dot(uv - vec2(.64, .5), (uv - vec2(.64, .5)) * vec2(.9, 2.)));
        float ribbon = pow(smoothstep(.62, .9, f) * (1. - smoothstep(.9, 1., f)), 1.6);
        vec3 deep = vec3(.010, .028, .085);
        vec3 navy = vec3(.035, .10, .30);
        vec3 blue = vec3(.20, .45, 1.);
        vec3 ice  = vec3(.80, .90, 1.);
        vec3 col = mix(deep, navy, f);
        col = mix(col, blue, smoothstep(.45, .95, f) * (.35 + .75 * mass));
        col += ice * ribbon * (.25 + .9 * mass);
        col += blue * mass * .22;
        col *= mix(.5, 1., smoothstep(.05, .6, uv.x));
        o = vec4(col, 1.);
      }`;
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; };
    const prog = gl.createProgram();
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, vs));
    gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      root.classList.add("no-gl");
    } else {
      gl.useProgram(prog);
      const buf = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
      const loc = gl.getAttribLocation(prog, "p");
      gl.enableVertexAttribArray(loc);
      gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      const uR = gl.getUniformLocation(prog, "r"), uT = gl.getUniformLocation(prog, "t"), uM = gl.getUniformLocation(prog, "m");
      const scale = Math.min(window.devicePixelRatio || 1, 2) * 0.5;
      const mouse = { x: 0.6, y: 0.5, tx: 0.6, ty: 0.5 };
      window.addEventListener("pointermove", (e) => { mouse.tx = e.clientX / innerWidth; mouse.ty = 1 - e.clientY / innerHeight; }, { passive: true });
      const size = () => {
        canvas.width = Math.round(innerWidth * scale); canvas.height = Math.round(innerHeight * scale);
        gl.viewport(0, 0, canvas.width, canvas.height);
        if (reduce && draw) draw(performance.now()); // static frame is cleared by a resize; redraw it
      };
      size(); window.addEventListener("resize", size);
      const t0 = performance.now() - 20000;
      draw = (now) => {
        mouse.x += (mouse.tx - mouse.x) * 0.04; mouse.y += (mouse.ty - mouse.y) * 0.04;
        gl.uniform2f(uR, canvas.width, canvas.height);
        gl.uniform1f(uT, (now - t0) / 1000);
        gl.uniform2f(uM, mouse.x, mouse.y);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
      };
      if (reduce) {
        draw(performance.now());
      } else {
        let raf = 0;
        const loop = (now) => { draw(now); raf = requestAnimationFrame(loop); };
        raf = requestAnimationFrame(loop);
        document.addEventListener("visibilitychange", () => {
          cancelAnimationFrame(raf);
          if (!document.hidden) raf = requestAnimationFrame(loop);
        });
      }
    }
  }

  /* ---------- 2. Edge refraction (Chromium only; Safari accepts the syntax but renders nothing) ---------- */
  const cards = [...document.querySelectorAll(".card")];
  const isChromium = !!(navigator.userAgentData && navigator.userAgentData.brands.some((b) => /Chromium/.test(b.brand)));
  function buildLensMap() {
    const c = cards[0]; if (!c) return;
    const w = Math.round(c.offsetWidth), h = Math.round(c.offsetHeight);
    if (!w || !h) return;
    const cv = document.createElement("canvas"); cv.width = w; cv.height = h;
    const ctx = cv.getContext("2d"); const img = ctx.createImageData(w, h);
    const bezel = 34, rad = 32;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        // signed distance to a rounded rectangle, negative inside
        const qx = Math.abs(x - w / 2) - (w / 2 - rad), qy = Math.abs(y - h / 2) - (h / 2 - rad);
        const out = Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - rad;
        const d = -out; // distance from edge, inside
        let dx = 0, dy = 0;
        if (d < bezel) {
          const k = Math.pow(1 - Math.max(d, 0) / bezel, 2);
          const nx = (x - w / 2) / (w / 2), ny = (y - h / 2) / (h / 2);
          dx = -nx * k; dy = -ny * k;
        }
        const i = (y * w + x) * 4;
        img.data[i] = 128 + dx * 127; img.data[i + 1] = 128 + dy * 127; img.data[i + 2] = 128; img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    const fe = document.getElementById("lens-map");
    fe.setAttribute("href", cv.toDataURL());
    fe.setAttribute("width", w); fe.setAttribute("height", h);
  }
  if (isChromium && window.innerWidth > 900) {
    buildLensMap();
    root.classList.add("refract");
    let to; window.addEventListener("resize", () => { clearTimeout(to); to = setTimeout(buildLensMap, 200); });
  }

  /* ---------- 3. Specular highlight follows the pointer (writes to the card only) ---------- */
  cards.forEach((card) => {
    card.addEventListener("pointermove", (e) => {
      const r = card.getBoundingClientRect();
      card.style.setProperty("--mx", ((e.clientX - r.left) / r.width) * 100 + "%");
      card.style.setProperty("--my", ((e.clientY - r.top) / r.height) * 100 + "%");
    }, { passive: true });
  });

  /* ---------- 4. Intro and exit ---------- */
  if (!window.AIDA_MOTION) return;
  {
    root.classList.add("js-motion");
    gsap.registerPlugin(SplitText);
    const split = new SplitText(".hello", { type: "words,chars", mask: "words" });
    const tl = gsap.timeline({ defaults: { ease: "expo.out" } });
    tl.to(".brand", { opacity: 1, duration: 0.6 }, 0)
      .fromTo(".tag", { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.7 }, 0.05)
      .from(split.chars, { yPercent: 110, duration: 0.9, stagger: 0.018 }, 0.1)
      .fromTo(".ask", { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.8 }, 0.35)
      .fromTo(".card", { opacity: 0, y: 40, scale: 0.97 }, { opacity: 1, y: 0, scale: 1, duration: 1, stagger: 0.09, clearProps: "transform" }, 0.3);
  }

  window.AIDA_EXIT = (_id, el) => new Promise((done) => {
    const other = cards.filter((c) => c !== el);
    gsap.timeline({ onComplete: done })
      .to(other, { opacity: 0, y: 16, duration: 0.25, ease: "power2.out" }, 0)
      .to(".intro", { opacity: 0, x: -16, duration: 0.25, ease: "power2.out" }, 0)
      .to(el, { scale: 1.03, duration: 0.35, ease: "expo.out" }, 0)
      .to(".veil", { opacity: 1, duration: 0.3, ease: "power2.in" }, 0.12);
  });
  window.AIDA_RESET = () => {
    gsap.set([".card", ".intro"], { opacity: 1, clearProps: "transform" });
    gsap.set(".veil", { opacity: 0 });
  };
})();
