function updateClock() {
  const now = new Date();
  document.getElementById("clock").textContent =
    now.toLocaleString("lt-LT", {
      dateStyle: "short",
      timeStyle: "short"
    });
}

updateClock();               // iškart
setInterval(updateClock, 60*1000); // kas sekundę
