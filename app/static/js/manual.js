const content = document.getElementById('manualContent');
const navLinks = document.querySelectorAll('.manual-nav a');
const HEADER_OFFSET = 10; // tarpas tarp header ir elemento

// Expand/collapse pagrindinės temos
document.querySelectorAll('.manual-nav > ul > li > a').forEach(mainLink => {
  mainLink.addEventListener('click', () => {
    mainLink.parentElement.classList.toggle('expanded');
  });
});

// Scroll tik dešinėje pusėje + active būsena
navLinks.forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();

    const id = link.getAttribute('href').substring(1);
    const target = document.getElementById(id);
    if (!target) return;

    // === SCROLL (NELIESTAS, VEIKIANTIS) ===
    const targetRect = target.getBoundingClientRect();
    const contentRect = content.getBoundingClientRect();

    const scrollTop =
      content.scrollTop +
      (targetRect.top - contentRect.top) -
      HEADER_OFFSET;

    content.scrollTo({
      top: scrollTop,
      behavior: 'smooth'
    });

    // === ACTIVE STATE ===
    navLinks.forEach(l => l.classList.remove('active'));
    link.classList.add('active');

    // jei paspausta vidinė tema – išskleisti tėvinę šaką
    const parentLi = link.closest('li');
    const parentUl = parentLi?.parentElement;
    const topLi = parentUl?.closest('li');

    if (topLi) {
      topLi.classList.add('expanded');
    }
  });
});
