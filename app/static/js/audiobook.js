document.addEventListener("DOMContentLoaded", () => {
  const audioBtn = document.getElementById("load-audio");
  const textBtn  = document.getElementById("load-text");
  const audioInput = document.getElementById("audio-input");
  const textInput  = document.getElementById("text-input");
  const audioPlayer = document.getElementById("audio-player");
  const textContent = document.getElementById("text-content");

  // --- Utility: enable or disable native text selection ---
  function toggleSelection(disabled) {
    const value = disabled ? "none" : "text";
    textContent.style.userSelect = value;
    textContent.style.touchAction = disabled ? "manipulation" : "auto";
    textContent.style.webkitTouchCallout = disabled ? "none" : "default";
  }

  // Default: selection enabled (so user can highlight normally)
  toggleSelection(false);

  // Optional: prevent long-press menu but still allow highlighting
  const isTouchDevice = "ontouchstart" in window || navigator.maxTouchPoints > 0;
  if (isTouchDevice) {
    // This stops the “Copy / Share / Web Search” popup, but not highlighting itself
    textContent.addEventListener("contextmenu", e => e.preventDefault());
  }

  // File upload logic
  audioBtn.addEventListener("click", () => audioInput.click());
  textBtn.addEventListener("click", () => textInput.click());

  audioInput.addEventListener("change", e => {
    const file = e.target.files[0];
    if (!file) return;
    audioPlayer.src = URL.createObjectURL(file);
    audioPlayer.style.display = "block";
  });

  textInput.addEventListener("change", e => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      textContent.textContent = reader.result;
      textContent.style.display = "block";
    };
    reader.readAsText(file);
  });

  // Selection event for desktop and mobile
  textContent.addEventListener("mouseup", handleSelection);
  textContent.addEventListener("touchend", handleSelection, { passive: true });

  async function handleSelection() {
    const selection = window.getSelection().toString().trim();
    if (!selection) return;

    // disable selection temporarily to avoid flicker
    toggleSelection(true);

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
    const response = await fetch("/audiobook/translate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken
      },
      body: JSON.stringify({ text: selection })
    });

    const { translation } = await response.json();
    showModal(selection, translation);
  }

  function showModal(original, translation) {
    const modal = document.getElementById("custom-modal");
    const qEl = document.getElementById("modal-question");
    const aEl = document.getElementById("modal-answer");
    const yesBtn = document.getElementById("yesBtn");
    const noBtn = document.getElementById("noBtn");
    const flipBtn = document.getElementById("flipBtn");

    // re-enable selection inside modal for editing
    toggleSelection(false);

    qEl.value = original;
    aEl.value = translation;
    modal.style.display = "block";
    setTimeout(() => qEl.focus(), 0);

    flipBtn.onclick = () => {
      [qEl.value, aEl.value] = [aEl.value, qEl.value];
      qEl.focus();
    };

    yesBtn.onclick = () => {
      const question = qEl.value.trim();
      const answer = aEl.value.trim();
      if (!question || !answer) {
        showFlash("Both question and answer are required.", "error");
        return;
      }
      addFlashcard(question, answer);
      modal.style.display = "none";
      toggleSelection(false); // keep enabled for next highlight
    };

    noBtn.onclick = () => {
      modal.style.display = "none";
      toggleSelection(false);
    };

    window.onclick = (evt) => {
      if (evt.target === modal) {
        modal.style.display = "none";
        toggleSelection(false);
      }
    };
  }

  async function addFlashcard(question, answer) {
    const formData = new FormData();
    formData.append("question", question);
    formData.append("answer", answer);

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
    const response = await fetch("/flashcard/addcards", {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
      body: formData
    });

    const result = await response.json();
    showFlash(result.message, result.status === "success" ? "success" : "error");
  }

  function showFlash(msg, kind = "success") {
    const flashDiv = document.createElement("div");
    flashDiv.className = `flashcard-${kind}-message`;
    flashDiv.textContent = msg;
    document.getElementById("flash-message-container").appendChild(flashDiv);
    setTimeout(() => flashDiv.remove(), 3000);
  }
});
