(function () {
  const script = document.currentScript;
  const apiKey = script.dataset.apiKey;
  const baseUrl = script.dataset.baseUrl;

  const btn = document.createElement("button");
  btn.innerText = "💬";
  btn.style.cssText = "position:fixed;bottom:20px;right:20px;width:56px;height:56px;border-radius:50%;z-index:9999;border:none;cursor:pointer;";
  document.body.appendChild(btn);

  const iframe = document.createElement("iframe");
  iframe.src = `${baseUrl}/widget?apiKey=${encodeURIComponent(apiKey)}`;
  iframe.style.cssText = "position:fixed;bottom:90px;right:20px;width:360px;height:520px;border:none;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.2);display:none;z-index:9999;";
  document.body.appendChild(iframe);

  btn.onclick = () => {
    iframe.style.display = iframe.style.display === "none" ? "block" : "none";
  };
})();