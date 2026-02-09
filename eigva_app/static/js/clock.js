// /static/js/clock.js
document.addEventListener("DOMContentLoaded", () => {
  function updateClock() {
    const now = new Date();

    // formatas: data + valandos:minutės
    const formatted = now.toLocaleString("lt-LT", {
      dateStyle: "short",   // pvz. 22.01.26
      hour: "2-digit",
      minute: "2-digit"
    });

    const clockEl = document.getElementById("clock");
    if (clockEl) {
      clockEl.textContent = formatted;
    }

    // kitam atnaujinimui iki kitos minutės
    const delay = (60 - now.getSeconds()) * 1000 + 50; // +50ms tikslumui
    setTimeout(updateClock, delay);
  }

  updateClock();
});
