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
  textContent.addEventListener("touchend", handleSelection);R

  async function handleSelection() {
    const selection = window.getSelection().toString().trim();
    if (!selection) return;

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
    const response = await fetch("/audiobook/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json",
        "X-CSRFToken": csrfToken 
      },
      body: JSON.stringify({ text: selection })
    });

    const { translation } = await response.json();
    showModal(selection, translation);
  }

  function showModal(original, translation) {
    const modal = document.getElementById("custom-modal");
    const content = document.getElementById("modal-content");
    const yesBtn = document.getElementById("yesBtn");
    const noBtn = document.getElementById("noBtn");

    content.textContent = `English → ${original}\n\nPortuguese → ${translation}\n\nAdicionar flashcard?`;
    modal.style.display = "block";

    yesBtn.onclick = () => {
      addFlashcard(original, translation);
      modal.style.display = "none";
    };
    noBtn.onclick = () => {
      modal.style.display = "none";
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
    const flashDiv = document.createElement("div");
    flashDiv.className = `flashcard-${result.status}-message`;
    flashDiv.textContent = result.message;
    document.getElementById("flash-message-container").appendChild(flashDiv);
    setTimeout(() => flashDiv.remove(), 3000);
  }
});
