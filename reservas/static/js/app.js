document.addEventListener("DOMContentLoaded", () => {
    if (window.lucide) {
        window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
    }

    const toggle = document.querySelector("[data-nav-toggle]");
    const navigation = document.querySelector("[data-nav]");
    if (toggle && navigation) {
        toggle.addEventListener("click", () => {
            const isOpen = navigation.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", String(isOpen));
        });
    }
});
