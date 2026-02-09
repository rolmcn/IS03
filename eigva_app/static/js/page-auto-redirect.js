document.addEventListener("DOMContentLoaded", () => {
    const countdownElem = document.querySelector(".countdown");
    if (!countdownElem) return;

    let countdown = parseInt(countdownElem.textContent, 10);

    const interval = setInterval(() => {
        countdown -= 1;
        countdownElem.textContent = countdown;

        if (countdown <= 0) {
            clearInterval(interval);
            window.location.href = "http://127.0.0.1:8001/login";
        }
    }, 1000);
});
