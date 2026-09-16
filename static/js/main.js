const projectSwitcherToggle = document.querySelector(
    "[data-project-switcher-toggle]",
);
const projectSwitcherMenu = document.querySelector(
    "[data-project-switcher-menu]",
);

if (projectSwitcherToggle && projectSwitcherMenu) {
    const closeProjectSwitcher = () => {
        projectSwitcherMenu.hidden = true;
        projectSwitcherToggle.setAttribute("aria-expanded", "false");
    };

    projectSwitcherToggle.addEventListener("click", () => {
        const isOpen =
            projectSwitcherToggle.getAttribute("aria-expanded") === "true";

        projectSwitcherMenu.hidden = isOpen;
        projectSwitcherToggle.setAttribute(
            "aria-expanded",
            String(!isOpen),
        );
    });

    document.addEventListener("click", (event) => {
        if (
            !projectSwitcherToggle.contains(event.target) &&
            !projectSwitcherMenu.contains(event.target)
        ) {
            closeProjectSwitcher();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeProjectSwitcher();
            projectSwitcherToggle.focus();
        }
    });
}