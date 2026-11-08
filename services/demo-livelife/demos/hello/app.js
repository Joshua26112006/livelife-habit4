// Relative URL on purpose: it works under /demo-livelife/hello/ whatever address the service sits behind.
fetch("api/ping")
  .then((r) => r.json())
  .then((d) => { document.getElementById("api").textContent = "Sample backend says: " + d.message; })
  .catch(() => { document.getElementById("api").textContent = "Sample backend did not answer."; });
