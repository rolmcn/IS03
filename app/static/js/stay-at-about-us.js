document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("contact-form");
  const messageContainer = document.getElementById("form-message");

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);

    try {
      const response = await fetch(form.action.replace('/#about-us', '/'), {
        method: "POST",
        body: formData,
      });

      const html = await response.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");

      const newMessage = doc.getElementById("form-message");
      if (newMessage && messageContainer) {
        messageContainer.innerHTML = newMessage.innerHTML;

        const msgText = newMessage.textContent.toLowerCase();
        if (msgText.includes("dėkojame")) {
          form.reset();
        }
      }

    } catch (error) {
      if (messageContainer) {
        messageContainer.innerHTML = '<p style="color: #ff6b6b;">Klaida siunčiant formą.</p>';
      }
      console.error("Formos siuntimo klaida:", error);
    }
  });
});
