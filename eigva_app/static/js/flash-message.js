document.addEventListener("DOMContentLoaded", () => {
    const messageContainers = [
        document.getElementById("register-form-message"),
        document.getElementById("forgot-login-form-message")
    ];

    messageContainers.forEach(container => {
        if (container && container.innerHTML.trim() !== "") {
            setTimeout(() => {
                container.innerHTML = "";

                if (container.id === "forgot-login-form-message") {
                    window.location.href = "/login";
                }
            }, 10000); // 10 s
        }
    });
});