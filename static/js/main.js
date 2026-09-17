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
        userAuthor.textContent = "You";

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
        thinkingIndicator.textContent = "Thinking";

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
