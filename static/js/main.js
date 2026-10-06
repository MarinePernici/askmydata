const sidebar = document.querySelector("[data-sidebar]");
const sidebarOpen = document.querySelector("[data-sidebar-open]");
const sidebarClose = document.querySelector("[data-sidebar-close]");
const sidebarOverlay = document.querySelector("[data-sidebar-overlay]");

if (sidebar && sidebarOpen && sidebarClose && sidebarOverlay) {
    const openSidebar = () => {
        sidebar.classList.add("sidebar-open");
        sidebarOverlay.hidden = false;
        sidebarOpen.setAttribute("aria-expanded", "true");
        sidebarClose.focus();
    };

    const closeSidebar = () => {
        sidebar.classList.remove("sidebar-open");
        sidebarOverlay.hidden = true;
        sidebarOpen.setAttribute("aria-expanded", "false");
        sidebarOpen.focus();
    };

    sidebarOpen.addEventListener("click", openSidebar);
    sidebarClose.addEventListener("click", closeSidebar);
    sidebarOverlay.addEventListener("click", closeSidebar);

    document.addEventListener("keydown", (event) => {
        if (
            event.key === "Escape" &&
            sidebar.classList.contains("sidebar-open")
        ) {
            closeSidebar();
        }
    });
}
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
const conversationQuestionForm = document.querySelector(
    "[data-conversation-question-form]",
);
const conversationQuestionInput = document.querySelector(
    "[data-conversation-question-input]",
);
const conversationQuestionSubmit = document.querySelector(
    "[data-conversation-question-submit]",
);

if (
    conversationQuestionForm &&
    conversationQuestionInput &&
    conversationQuestionSubmit
) {
    const updateQuestionSubmitState = () => {
        conversationQuestionSubmit.disabled =
            conversationQuestionInput.value.trim() === "";
    };

    conversationQuestionInput.addEventListener(
        "input",
        updateQuestionSubmitState,
    );

    updateQuestionSubmitState();

    conversationQuestionForm.addEventListener("submit", (event) => {
        const question = conversationQuestionInput.value.trim();

        if (question === "") {
            event.preventDefault();
            return;
        }

        const submittedQuestion = document.createElement("input");
        submittedQuestion.type = "hidden";
        submittedQuestion.name = conversationQuestionInput.name;
        submittedQuestion.value = question;

        conversationQuestionForm.append(submittedQuestion);

        conversationQuestionInput.removeAttribute("name");
        conversationQuestionInput.value = "";
        conversationQuestionInput.readOnly = true;
        conversationQuestionSubmit.disabled = true;

        const emptyState = document.querySelector(
            "[data-conversation-empty]",
        );

        if (emptyState) {
            emptyState.remove();
        }

        const messagesContainer = document.querySelector(
            "[data-conversation-messages]",
        );

        if (!messagesContainer) {
            return;
        }

        const userMessage = document.createElement("article");
        userMessage.className =
            "conversation-message conversation-message-user";

        const userAuthor = document.createElement("p");
        userAuthor.className = "conversation-message-author";
        userAuthor.textContent = conversationMessages.dataset.userLabel;

        const userContent = document.createElement("div");
        userContent.className = "conversation-message-content";
        userContent.textContent = question;

        userMessage.append(userAuthor, userContent);

        const thinkingMessage = document.createElement("article");
        thinkingMessage.className =
            "conversation-message conversation-message-assistant " +
            "conversation-message-pending";

        const assistantAuthor = document.createElement("p");
        assistantAuthor.className = "conversation-message-author";
        assistantAuthor.textContent = "AskMyData";

        const thinkingContent = document.createElement("div");
        thinkingContent.className = "conversation-message-content";

        const thinkingIndicator = document.createElement("span");
        thinkingIndicator.className = "conversation-thinking";
        thinkingIndicator.textContent = conversationMessages.dataset.thinkingLabel;

        thinkingContent.append(thinkingIndicator);
        thinkingMessage.append(assistantAuthor, thinkingContent);

        messagesContainer.append(userMessage, thinkingMessage);

        requestAnimationFrame(() => {
            thinkingMessage.scrollIntoView({
                behavior: "smooth",
                block: "end",
            });
        });
    });
}
const conversationLastMessage = document.querySelector(
    "[data-conversation-last-message]",
);

if (conversationLastMessage) {
    requestAnimationFrame(() => {
        conversationLastMessage.scrollIntoView({
            block: "end",
        });
    });
}
const conversationPanel = document.querySelector(
    "[data-conversation-panel]",
);
const conversationPanelToggle = document.querySelector(
    "[data-conversation-panel-toggle]",
);

if (conversationPanel && conversationPanelToggle) {
    const closeConversationPanel = () => {
        conversationPanel.classList.remove("conversation-panel-open");
        conversationPanelToggle.setAttribute("aria-expanded", "false");
    };

    conversationPanelToggle.addEventListener("click", () => {
        const isOpen = conversationPanel.classList.toggle(
            "conversation-panel-open",
        );

        conversationPanelToggle.setAttribute(
            "aria-expanded",
            String(isOpen),
        );
    });

    document.addEventListener("keydown", (event) => {
        if (
            event.key === "Escape" &&
            conversationPanel.classList.contains(
                "conversation-panel-open",
            )
        ) {
            closeConversationPanel();
            conversationPanelToggle.focus();
        }
    });
}

const questionErrorDialog = document.querySelector(
    "[data-question-error-dialog]",
);

if (questionErrorDialog && !questionErrorDialog.open) {
    questionErrorDialog.showModal();
}

const tableSelectionCheckboxes = Array.from(
    document.querySelectorAll('input[name="tables"]'),
);
const tableSelectionToggle = document.querySelector(
    "[data-table-selection-toggle]",
);
const tableSelectionCount = document.querySelector(
    "[data-table-selection-count]",
);
const tableSelectionSubmit = document.querySelector(
    "[data-table-selection-submit]",
);

if (
    tableSelectionCheckboxes.length &&
    tableSelectionToggle &&
    tableSelectionCount &&
    tableSelectionSubmit
) {
    const updateTableSelectionControls = () => {
        const selectedCount = tableSelectionCheckboxes.filter(
            (checkbox) => checkbox.checked,
        ).length;
        const allSelected =
            selectedCount === tableSelectionCheckboxes.length;

        const selectedLabel =
            selectedCount === 1
                ? tableSelectionCount.dataset.selectedSingular
                : tableSelectionCount.dataset.selectedPlural;

        tableSelectionCount.textContent =
            `${selectedCount} / ${tableSelectionCheckboxes.length} ${selectedLabel}`;

        tableSelectionToggle.textContent = allSelected
            ? tableSelectionToggle.dataset.deselectAllLabel
            : tableSelectionToggle.dataset.selectAllLabel;

        tableSelectionSubmit.disabled = selectedCount === 0;
    };

    tableSelectionToggle.addEventListener("click", () => {
        const allSelected = tableSelectionCheckboxes.every(
            (checkbox) => checkbox.checked,
        );

        tableSelectionCheckboxes.forEach((checkbox) => {
            checkbox.checked = !allSelected;
        });

        updateTableSelectionControls();
    });

    tableSelectionCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener(
            "change",
            updateTableSelectionControls,
        );
    });

    updateTableSelectionControls();
}

const projectCreateForm = document.querySelector(
    "[data-project-create-form]",
);
const projectCreateSubmit = document.querySelector(
    "[data-project-create-submit]",
);
const projectCreationProgress = document.querySelector(
    "[data-project-creation-progress]",
);
const projectCreateActions = document.querySelector(
    "[data-project-create-actions]",
);

if (
    projectCreateForm &&
    projectCreateSubmit &&
    projectCreateActions &&
    projectCreationProgress
) {
    projectCreateForm.addEventListener("submit", () => {
            projectCreateSubmit.disabled = true;
            projectCreateActions.hidden = true;
            projectCreationProgress.hidden = false;
    });
}

const catalogRegenerateForm = document.querySelector(
    "[data-catalog-regenerate-form]",
);
const catalogRegenerateSubmit = document.querySelector(
    "[data-catalog-regenerate-submit]",
);
const catalogRegenerationProgress = document.querySelector(
    "[data-catalog-regeneration-progress]",
);

if (
    catalogRegenerateForm &&
    catalogRegenerateSubmit &&
    catalogRegenerationProgress
) {
    catalogRegenerateForm.addEventListener("submit", () => {
        catalogRegenerateSubmit.disabled = true;
        catalogRegenerateForm.hidden = true;
        catalogRegenerationProgress.hidden = false;
    });
}
