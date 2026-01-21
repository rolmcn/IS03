document.addEventListener("DOMContentLoaded", () => {
    const messageContainer = document.getElementById("register-form-message");

    if (messageContainer && messageContainer.innerHTML.trim() !== "") {
        setTimeout(() => {
            messageContainer.innerHTML = "";
        }, 10000);
    }
});
