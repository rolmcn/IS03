document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll(".token-confirm-btn");
    const messageContainer = document.getElementById("register-form-message");

    buttons.forEach(btn => {
        btn.addEventListener("click", async () => {
            const token = btn.dataset.token;
            if (!token) return;

            try {
                const response = await fetch(`/login/confirm?token=${token}`, { method: "GET" });
                const data = await response.json();

                if (messageContainer) {
                    messageContainer.innerHTML = `<p style="color: ${data.success ? '#28a745' : '#ff6b6b'};">${data.message}</p>`;

                    setTimeout(() => {
                        messageContainer.innerHTML = "";
                    }, 10000);
                }
            } catch (err) {
                console.error("Patvirtinimo nuorodos klaida:", err);
            }
        });
    });
});
