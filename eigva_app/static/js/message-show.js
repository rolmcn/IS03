document.addEventListener("DOMContentLoaded", () => {
  // =========================
  // 1️⃣ Gauname visas korteles ir messages list konteinerį
  // =========================
  const messagesList = document.querySelector(".messages-list");
  if (!messagesList) return;

  const cards = Array.from(messagesList.querySelectorAll(".message-card"));
  let openCard = null; // saugosime, kuri kortelė šiuo metu atidaryta

  // =========================
  // 2️⃣ Pagalbinė funkcija: gaunam timestamp iš kortelės datos
  // =========================
  const getTimestamp = (card) =>
    new Date(card.querySelector(".message-date").textContent).getTime();

  // =========================
  // 3️⃣ Flip animacija + rikiavimas
  // - neskaitytos viršuje
  // - skaitytos žemiau
  // - abiejų grupių viduje naujausi viršuje
  // =========================
  const reorderCards = () => {
    const oldPositions = cards.map(card => card.getBoundingClientRect().top);

    cards.sort((a, b) => {
      const aRead = a.classList.contains("unread") ? 0 : 1;
      const bRead = b.classList.contains("unread") ? 0 : 1;
      if (aRead !== bRead) return aRead - bRead; // unread pirmiau
      return getTimestamp(b) - getTimestamp(a);   // naujausi viršuje
    });

    cards.forEach((card, i) => {
      const newTop = card.getBoundingClientRect().top;
      const delta = oldPositions[i] - newTop;
      if (delta) {
        card.style.transform = `translateY(${delta}px)`;
        card.style.transition = "none";
      }
    });

    requestAnimationFrame(() => {
      cards.forEach(card => {
        card.style.transition = "transform 0.3s ease";
        card.style.transform = "";
      });
    });

    // Perkeliame korteles į DOM nauja tvarka
    cards.forEach(card => messagesList.appendChild(card));
  };

  // =========================
  // 4️⃣ Pradinis rikiavimas puslapio krovimo metu
  // =========================
  reorderCards();

  // =========================
  // 5️⃣ Kortelių click event
  // =========================
  cards.forEach(card => {
    const toggleArrow = card.querySelector(".message-toggle"); // rodyklė ▼/▲

    card.addEventListener("click", async () => {

      // -------------------------
      // 5a. Jei atidaryta kita kortelė → uždarom ją automatiškai
      // -------------------------
      if (openCard && openCard !== card) {
        openCard.classList.remove("open"); // uždarom
        const oldArrow = openCard.querySelector(".message-toggle");
        if (oldArrow) oldArrow.textContent = "▼"; // rodyklė nukreipiama žemyn
        reorderCards(); // persirikiuojam po uždarymo
      }

      // -------------------------
      // 5b. Atidarom arba uždarom paspaustą kortelę
      // -------------------------
      const isOpen = card.classList.toggle("open");
      openCard = isOpen ? card : null;

      // Rodyklė pasisuka: ▲ jei atidaryta, ▼ jei uždaryta
      if (toggleArrow) toggleArrow.textContent = isOpen ? "▲" : "▼";

      // -------------------------
      // 5c. Jei atidarome neskaitytą → pažymim skaityta backend’e
      // -------------------------
      if (isOpen && card.classList.contains("unread")) {
        const messageId = card.dataset.messageId;
        try {
          const res = await fetch(`/account/mark_read/${messageId}`, {
            method: "POST"
          });
          const data = await res.json();
          if (data.status === "ok") {
            card.classList.remove("unread"); // frontend’e atnaujinam klasę

            // ✅ Nauja dalis: gauname UTC laiką iš backendo
            // Tai ISO string UTC formatu, be jokių konvertavimų
            const readDateUtc = data.msg_read;
            console.log("Message marked as read at (UTC):", readDateUtc);
          }
        } catch (err) {
          console.error("Failed to mark message as read", err);
        }
      }

      // -------------------------
      // 5d. Jei uždarome kortelę → perrikiuojam su flip animacija
      // -------------------------
      if (!isOpen) {
        reorderCards();
      }
    });
  });

  // =========================
  // 6️⃣ Jei puslapis uždaromas / refresh → automatiškai uždarom atidarytą kortelę
  // =========================
  window.addEventListener("beforeunload", () => {
    if (openCard) openCard.classList.remove("open");
  });
});
