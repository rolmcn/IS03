document.addEventListener("DOMContentLoaded", () => {
  function updateClock() {
    const now = new Date();

    const formatted = now.toLocaleString("lt-LT", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit"
    });

    const clockEl = document.getElementById("clock");
    if (clockEl) {
      clockEl.textContent = formatted;
    }

    const delay = (60 - now.getSeconds()) * 1000 + 50;
    setTimeout(updateClock, delay);
  }

  updateClock();
});