document.addEventListener("DOMContentLoaded", () => {
  const mobileQuery = window.matchMedia("(max-width: 700px)");
  const dropdowns = document.querySelectorAll(".nav-item-dropdown");

  dropdowns.forEach((dropdown) => {
    const trigger = dropdown.querySelector(".nav-dropdown-trigger");

    if (!trigger) return;

    trigger.addEventListener("click", (event) => {
      if (!mobileQuery.matches) return;

      const isOpen = dropdown.classList.contains("is-open");

      if (!isOpen) {
        event.preventDefault();

        dropdowns.forEach((item) => {
          if (item !== dropdown) {
            item.classList.remove("is-open");
          }
        });

        dropdown.classList.add("is-open");
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
