export function focusInput() {
  const input = document.getElementById(`chat-input`);
  if (
    !input ||
    !(input instanceof HTMLInputElement) ||
    input.disabled ||
    input.readOnly
  )
    return;
  input.focus();
}

export function scrollUserMessageToTheTop() {
  /**
   * Scrolls last user message to the top of the window + header + clearance.
   * Should be called after a new user message is added.
   */
  const message = document.getElementsByClassName("user-message")[0];
  const header = document.getElementsByClassName("chat-header")[0];
  const spacer = document.getElementsByClassName("chat-spacer-div")[0];

  if (
    !(message instanceof HTMLElement) ||
    !(header instanceof HTMLElement) ||
    !(spacer instanceof HTMLElement)
  )
    return;

  const topClearance = 24;
  const usedHeight = header.offsetHeight + topClearance + message.offsetHeight;
  const spacerHeight = window.innerHeight - usedHeight;

  spacer.style.height = `${spacerHeight}px`;
  spacer.scrollIntoView({ behavior: "smooth", block: "end" });
}

export function scrollToTheBottom(isInitial: boolean) {
  const container = document.getElementsByClassName("scroll-container")[0];
  if (!(container instanceof HTMLElement)) return;

  if (isInitial) {
    container.scrollTo({
      top: container.scrollHeight,
      behavior: "smooth",
    });
    return;
  }

  /**
   * Scrolls to the bottom of the scroll container while ensuring that the last
   * message bottom is some clearance above the window bottom edge.
   */
  const assistantMessages =
    document.getElementsByClassName("assistant-message");
  const lastAssistantMessage = assistantMessages[assistantMessages.length - 1];
  if (
    !lastAssistantMessage ||
    lastAssistantMessage.nextElementSibling?.classList.contains("user-message")
  ) {
    console.log("no last assistant message");
    return;
  }

  const spacer = document.getElementsByClassName("chat-spacer-div")[0];
  if (!(spacer instanceof HTMLElement)) return;

  const scrollLeft =
    container.scrollHeight - (container.clientHeight + container.scrollTop);
  const bottomClearance = getMinSpacerHeight();
  /**
   * Update spacer height to prevent massive whitespace at the bottom.
   */
  const spacerHeight = Math.max(
    bottomClearance,
    spacer.clientHeight - scrollLeft
  );
  spacer.style.height = `${spacerHeight}px`;

  if (scrollLeft > 128) return;

  /**
   * Check only bottom clearance, does not need to test for top clearance,
   * assumption being that before the last assistant message, either:
   * 1. user message has been auto-scrolled to the top
   * 2. user has scrolled after 1.
   *
   * in case of 1, the message will be at the top (after last user message)
   * in case of 2, scroll is not moved as scroll-away intent is captured
   *
   * Bottom clearance accounts for bottom edge of the last assistant message
   * being at least `clearance` above the window bottom edge.
   */
  const rect = lastAssistantMessage.getBoundingClientRect();
  if (rect.bottom + bottomClearance < window.innerHeight) {
    return;
  }

  spacer.style.height = `${bottomClearance}px`;
  spacer.scrollIntoView({ behavior: "smooth", block: "end" });
}

function getInputTop() {
  const container = document.getElementById("input-container");
  if (!container) return window.innerHeight;
  return window.innerHeight - container?.getBoundingClientRect().top;
}

function getMinSpacerHeight() {
  return Math.max(
    window.innerHeight * 0.2 /* 20vh */,
    getInputTop() + 24 /* input + clearance */
  );
}

export function setInitialSpacerHeight() {
  const spacer = document.getElementsByClassName("chat-spacer-div")[0];
  if (!(spacer instanceof HTMLElement)) return;
  spacer.style.height = `${getMinSpacerHeight()}px`;
}
