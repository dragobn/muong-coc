/* =============================================================
   site.js — KHUNG DÙNG CHUNG Web Mường Cốc
   i18n VN/EN/FR: toggle <html lang> + nhớ localStorage.
   CSS lo việc ẩn/hiện các phần tử [data-lang]; JS chỉ đổi lang.
   FR tạm = bản EN (đánh dấu TODO dịch FR ở data layer).
   ============================================================= */
(function () {
  "use strict";

  var SUPPORTED = ["vi", "en", "fr"];
  var DEFAULT = "vi";
  var KEY = "mc-lang";

  function getStored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function setStored(lang) {
    try { localStorage.setItem(KEY, lang); } catch (e) {}
  }

  function applyLang(lang) {
    if (SUPPORTED.indexOf(lang) === -1) lang = DEFAULT;
    document.documentElement.setAttribute("lang", lang);
    // cập nhật trạng thái nút
    var btns = document.querySelectorAll(".lang-switch button[data-set-lang]");
    for (var i = 0; i < btns.length; i++) {
      var on = btns[i].getAttribute("data-set-lang") === lang;
      btns[i].setAttribute("aria-pressed", on ? "true" : "false");
    }
    setStored(lang);
  }

  function init() {
    // ưu tiên: localStorage → <html lang> sẵn có → default
    var initial = getStored() || document.documentElement.getAttribute("lang") || DEFAULT;
    applyLang(initial);

    // wire nút chuyển ngôn ngữ (event delegation)
    var sw = document.querySelector(".lang-switch");
    if (sw) {
      sw.addEventListener("click", function (e) {
        var b = e.target.closest("button[data-set-lang]");
        if (!b) return;
        applyLang(b.getAttribute("data-set-lang"));
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
