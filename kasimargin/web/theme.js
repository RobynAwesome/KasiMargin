"use strict";
(() => {
  let preference;
  try { preference = localStorage.getItem("kasimargin-theme"); } catch { /* Storage may be unavailable. */ }
  const theme = preference === "light" || preference === "dark"
    ? preference : window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  document.documentElement.dataset.theme = theme;
})();
