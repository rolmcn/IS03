document.addEventListener("DOMContentLoaded", () => {
    const countdownElem = document.querySelector(".countdown");
    const autoClose = countdownElem !== null;

    if (autoClose) {
        let countdown = parseInt(countdownElem.textContent);

        const interval = setInterval(() => {
            countdown -= 1;
            countdownElem.textContent = countdown;

            if (countdown <= 0) {
                clearInterval(interval);
                window.close();
            }
        }, 1000);
    }
});
