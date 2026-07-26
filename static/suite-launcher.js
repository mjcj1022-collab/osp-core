/* OSP Suite launcher (stub) — drop into any app's frontend.
 *
 * Renders a topbar app-switcher showing only the apps the tenant is entitled to,
 * deep-linking by the current job number. Reads GET /api/me/entitlements from the
 * app's own backend (which includes osp_core.urls).
 *
 *   <div id="osp-suite"></div>
 *   <script src="/static/suite-launcher.js"></script>
 *   <script>ospSuite.mount({ current: "makeready", apiBase: "", token: JWT });</script>
 */
(function () {
  "use strict";

  // Where each app lives. Update URLs to your deployments.
  var APP_REGISTRY = {
    oden:      { label: "ODEN",            url: "https://lucky-basbousa-c909b8.netlify.app" },
    makeready: { label: "Make-Ready",      url: "https://courageous-seahorse-d21112.netlify.app" },
    redline:   { label: "REDLINE",         url: "https://redline-app.netlify.app" },
    bim:       { label: "Light Speed BIM", url: "https://light-speed-bim.netlify.app" }
  };

  function currentJob() {
    try { return new URLSearchParams(location.search).get("job") || ""; } catch (e) { return ""; }
  }

  function linkFor(appKey) {
    var a = APP_REGISTRY[appKey];
    if (!a) return null;
    var job = currentJob();
    return a.url + (job ? ("?job=" + encodeURIComponent(job)) : "");
  }

  async function fetchEntitlements(apiBase, token) {
    var headers = token ? { Authorization: "Bearer " + token } : {};
    var r = await fetch((apiBase || "") + "/api/me/entitlements/", { headers: headers });
    if (!r.ok) throw new Error("entitlements " + r.status);
    return r.json(); // { tenant, apps: [{app, tier, seats}] }
  }

  function render(el, apps, current) {
    el.innerHTML = "";
    var bar = document.createElement("div");
    bar.style.cssText = "display:flex;gap:6px;align-items:center;font-family:monospace;font-size:12px";
    apps.forEach(function (e) {
      var reg = APP_REGISTRY[e.app];
      if (!reg) return;
      var isCurrent = e.app === current;
      var node = document.createElement(isCurrent ? "span" : "a");
      node.textContent = reg.label;
      if (!isCurrent) { node.href = linkFor(e.app); }
      node.style.cssText = "padding:4px 8px;border-radius:4px;text-decoration:none;" +
        (isCurrent ? "background:#f59e0b;color:#000;font-weight:700" : "color:#22d3ee;border:1px solid #334");
      bar.appendChild(node);
    });
    el.appendChild(bar);
  }

  window.ospSuite = {
    async mount(opts) {
      opts = opts || {};
      var el = document.getElementById(opts.mountId || "osp-suite");
      if (!el) return;
      try {
        var data = await fetchEntitlements(opts.apiBase, opts.token);
        render(el, (data && data.apps) || [], opts.current);
      } catch (e) {
        el.innerHTML = ""; // fail silent: no launcher rather than a broken one
        if (window.console) console.warn("[ospSuite]", e.message);
      }
    },
    linkFor: linkFor,
    registry: APP_REGISTRY
  };
})();
