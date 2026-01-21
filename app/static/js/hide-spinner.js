function hideSpinner() {
            const overlay = document.getElementById("loading-overlay");
            overlay.style.display = "none";
            document.body.classList.remove("loading");
        }

        window.addEventListener("load", () => {
            hideSpinner();
        });