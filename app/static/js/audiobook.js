document.addEventListener("DOMContentLoaded", () => {
  const audioBtn = document.getElementById("load-audio");
  const textBtn  = document.getElementById("load-text");
  const audioInput = document.getElementById("audio-input");
  const textInput  = document.getElementById("text-input");
  const audioPlayer = document.getElementById("audio-player");
  const textContent = document.getElementById("text-content");

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

  textContent.addEventListener("mouseup", handleSelection);
  textContent.addEventListener("touchend", handleSelection); // ← removed stray "R"

  async function handleSelection() {
    const selection = window.getSelection().toString().trim();
    if (!selection) return;

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

    // Pre-fill fields
    qEl.value = `${original}`;
    aEl.value = `${translation}`;

    modal.style.display = "block";
    // Focus question for quick edits
    setTimeout(() => qEl.focus(), 0);

    // Wire up actions (overwrites previous handlers safely)
    flipBtn.onclick = () => {
      const q = qEl.value;
      qEl.value = aEl.value;
      aEl.value = q;
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
    };

    noBtn.onclick = () => {
      modal.style.display = "none";
    };

    // Optional: close on outside click
    window.onclick = (evt) => {
      if (evt.target === modal) modal.style.display = "none";
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
