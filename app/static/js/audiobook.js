document.addEventListener("DOMContentLoaded", () => {
  const audioBtn    = document.getElementById("load-audio");
  const textBtn     = document.getElementById("load-text");
  const audioInput  = document.getElementById("audio-input");
  const textInput   = document.getElementById("text-input");
  const audioPlayer = document.getElementById("audio-player");
  const textContent = document.getElementById("text-content");

  if (!textContent) {
    // Nothing to attach to – just bail out
    return;
  }

  // --- Utility: enable or disable native text selection ---
  function toggleSelection(disabled) {
    const value = disabled ? "none" : "text";
    textContent.style.userSelect = value;
    textContent.style.touchAction = disabled ? "manipulation" : "auto";
    textContent.style.webkitTouchCallout = disabled ? "none" : "default";
  }

  // Default: selection enabled
  toggleSelection(false);

  const isTouchDevice = "ontouchstart" in window || navigator.maxTouchPoints > 0;
  if (isTouchDevice) {
    textContent.addEventListener("contextmenu", e => e.preventDefault());
  }

  // File upload logic – only if buttons exist (no buttons in assigned-audiobook flow)
  if (audioBtn && audioInput) {
    audioBtn.addEventListener("click", () => audioInput.click());

    audioInput.addEventListener("change", e => {
      const file = e.target.files[0];
      if (!file) return;
      audioPlayer.src = URL.createObjectURL(file);
      audioPlayer.style.display = "block";
    });
  }

if (textBtn && textInput) {
  textBtn.addEventListener("click", () => textInput.click());

  textInput.addEventListener("change", e => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onload = () => {
      try {
        // Explicit UTF-8 decode from bytes
        const decoder = new TextDecoder("utf-8");
        const text = decoder.decode(reader.result);
        textContent.textContent = text;
        textContent.style.display = "block";
      } catch (err) {
        console.error("Error decoding text file:", err);
        textContent.textContent = "Erro ao ler o arquivo de texto (codificação).";
        textContent.style.display = "block";
      }
    };

    // Read raw bytes, we’ll decode ourselves
    reader.readAsArrayBuffer(file);
  });
}

  // Selection event for desktop and mobile
  textContent.addEventListener("mouseup", handleSelection);
  textContent.addEventListener("touchend", handleSelection, { passive: true });

  async function handleSelection() {
    const selection = window.getSelection().toString().trim();
    if (!selection) return;

    toggleSelection(true);

    const csrfToken = document
      .querySelector('meta[name="csrf-token"]')
      .getAttribute("content");

    const response = await fetch("/audiobook/translate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken
      },
      body: JSON.stringify({ text: selection })
    });

    if (!response.ok) {
      toggleSelection(false);
      showFlash("Translation failed. Try again.", "error");
      return;
    }

    const { translation } = await response.json();
    showModal(selection, translation);
    toggleSelection(false);
  }

  function showModal(original, translation) {
    const modal  = document.getElementById("custom-modal");
    const qEl    = document.getElementById("modal-question");
    const aEl    = document.getElementById("modal-answer");
    const yesBtn = document.getElementById("yesBtn");
    const noBtn  = document.getElementById("noBtn");
    const flipBtn= document.getElementById("flipBtn");

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
      const answer   = aEl.value.trim();
      if (!question || !answer) {
        showFlash("Both question and answer are required.", "error");
        return;
      }
      addFlashcard(question, answer);
      modal.style.display = "none";
      toggleSelection(false);
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

    const csrfToken = document
      .querySelector('meta[name="csrf-token"]')
      ?.getAttribute("content");

    try {
      const response = await fetch("/flashcard/addcards", {
        method: "POST",
        headers: {
          ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
          "X-Requested-With": "XMLHttpRequest", // optional but consistent
        },
        body: formData,
      });

      // 🔴 Inactive user → server returned inactive_user.html with 403
      if (response.status === 403) {
        const html = await response.text();
        document.open();
        document.write(html);
        document.close();
        return;
      }

      // ✅ Active user → JSON with status/message
      const result = await response.json();

      showFlash(
        result.message || "Unexpected response.",
        result.status === "success" ? "success" : "error"
      );
    } catch (err) {
      console.error("Error adding flashcard from audiobook.js:", err);
      showFlash("Erro ao adicionar o flashcard. Tente novamente.", "error");
    }
  }


  function showFlash(msg, kind = "success") {
    const flashDiv = document.createElement("div");
    flashDiv.className = `flashcard-${kind}-message`;
    flashDiv.textContent = msg;
    document
      .getElementById("flash-message-container")
      .appendChild(flashDiv);
    setTimeout(() => flashDiv.remove(), 3000);
  }
});
