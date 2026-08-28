document.addEventListener("DOMContentLoaded", () => {
  const mobileQuery = window.matchMedia("(max-width: 700px)");
  const dropdowns = [...document.querySelectorAll(".nav-item-dropdown")];

  dropdowns.forEach((dropdown) => {
    const trigger = dropdown.querySelector(".nav-dropdown-trigger");

    if (!trigger) return;

    trigger.addEventListener("click", (event) => {
      if (!mobileQuery.matches) return;

      if (!dropdown.classList.contains("is-open")) {
        event.preventDefault();
        event.stopPropagation();

        dropdowns.forEach((item) => {
          item.classList.toggle("is-open", item === dropdown);
        });
      }
    });
  });

  document.addEventListener("click", (event) => {
    if (!mobileQuery.matches) return;

    if (!event.target.closest(".nav-item-dropdown")) {
      dropdowns.forEach((dropdown) => {
        dropdown.classList.remove("is-open");
      });
    }
  });
});
