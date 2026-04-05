document.addEventListener("DOMContentLoaded", function () {
  const sections = document.querySelectorAll(".balance-section");

  sections.forEach(section => {
    const summary = section.querySelector(".balance-summary");
    const detailsHeader = section.querySelector(".balance-details-header");

    function toggleSection() {
      const isOpen = section.classList.contains("open");

      // 🔒 jei nori TIK VIENO atidaryto – palik šitą bloką
      sections.forEach(s => s.classList.remove("open"));

      // toggle
      if (!isOpen) {
        section.classList.add("open");
      }
    }

    if (summary) summary.addEventListener("click", toggleSection);
    if (detailsHeader) detailsHeader.addEventListener("click", toggleSection);
  });
});