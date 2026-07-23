(function () {
  function render(alertas) {
    if (!alertas || !alertas.length) return;
    var banner = document.createElement("div");
    banner.setAttribute("data-testid", "banner-alertas-watchlist");
    banner.style.cssText =
      "position:relative;width:100%;background:#1a1a1a;color:#f5f5f0;" +
      "padding:12px 20px;font-family:'Source Sans 3',sans-serif;font-size:14px;" +
      "line-height:1.5;box-sizing:border-box;border-bottom:2px solid #c65b2e;";
    var items = alertas
      .map(function (a) {
        return (
          a.ticker +
          ": cierre " +
          a.cierre +
          " (máximo " +
          a.precio_maximo +
          ", " +
          a.dias_consecutivos +
          " día(s))"
        );
      })
      .join(" · ");
    banner.innerHTML =
      "<strong>Condición de precio del reporte alcanzada</strong> — pendiente decisión documentada: " +
      items +
      ". <em>Esta alerta no es una recomendación de compra; la decisión sigue exigiendo registro humano en el DecisionLog.</em>";
    document.body.insertBefore(banner, document.body.firstChild);
  }

  fetch("/data/alertas.json")
    .then(function (r) {
      return r.ok ? r.json() : { alertas: [] };
    })
    .then(function (data) {
      render(data.alertas || []);
    })
    .catch(function () {});
})();
