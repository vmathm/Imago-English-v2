document.addEventListener("DOMContentLoaded", () => {
  if (!flashcards || flashcards.length === 0) {
    const container = document.getElementById("flashcard-container");
    container.innerHTML = "<p>Você não tem flashcards para estudar.</p>";
    return;
  }

  const container = document.getElementById("flashcard-container");
  const counterEl = document.getElementById("remaining-count");
  let index = 0;
  let reviewPool = [];
  const queue = [...flashcards];
  let isProcessing = false; // prevents double clicks during async call

  // Fisher–Yates shuffle
  function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
  }
  shuffle(queue);

  // Counter
  function updateCounter() {
    const remaining = (queue.length - index) + reviewPool.length;
    if (!counterEl) return;
    counterEl.textContent = remaining > 0 ? remaining : 0;
    counterEl.parentElement.style.display = remaining > 0 ? "block" : "none";
  }

  // ---------- Voice setup ----------
  let selectedVoice;
  function initializeVoices() {
    const voices = window.speechSynthesis.getVoices();
    selectedVoice = voices.find(v => v.lang.startsWith("en")) || null;
  }
  window.speechSynthesis.onvoiceschanged = initializeVoices;
  if (window.speechSynthesis.getVoices().length > 0) initializeVoices();

  function speakText(text, element) {
    const synth = window.speechSynthesis;
    if (synth.speaking || synth.pending) synth.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-GB";
    utterance.rate = 0.8;
    utterance.pitch = 1.1;
    if (selectedVoice) utterance.voice = selectedVoice;
    if (element) {
      element.classList.add("speaking");
      utterance.onend = () => element.classList.remove("speaking");
    }
    synth.speak(utterance);
  }

  // ---------- Disable buttons softly ----------
  function setButtonsEnabled(enabled) {
    document.querySelectorAll(".rate-btn, #toggle-answer").forEach(b => {
      b.style.pointerEvents = enabled ? "auto" : "none";
      b.style.opacity = enabled ? "1" : "0.6";
    });
  }

  // ---------- TEACHER MODE ----------
  if (typeof studentId !== "undefined" && studentId !== null) {
    container.innerHTML = "";
    queue.forEach(card => {
      const cardElement = document.createElement("div");
      cardElement.className = "section-box";
      cardElement.dataset.cardId = card.id;
      cardElement.innerHTML = `
        <p><strong>Q:</strong> ${card.question}
          <button class="speak-btn" data-text="${card.question}">🔊</button></p>
        <p><strong>A:</strong> ${card.answer}
          <button class="speak-btn" data-text="${card.answer}">🔊</button></p>
        <p><strong>Nível:</strong> ${card.level || "—"}</p>
        <div>
          <button class="btn btn-danger rate-btn" data-value="1">1</button>
          <button class="btn btn-warning rate-btn" data-value="2">2</button>
          <button class="btn btn-success rate-btn" data-value="3">3</button>
        </div>
      `;
      container.appendChild(cardElement);
    });

    updateCounter();

    document.querySelectorAll(".rate-btn").forEach(btn => {
      btn.onclick = async () => {
        if (isProcessing) return;
        isProcessing = true;
        setButtonsEnabled(false);

        const rating = btn.dataset.value;
        const cardDiv = btn.closest(".section-box");
        const cardId = cardDiv.dataset.cardId;

        try {
          await fetch("/flashcard/review_flashcard", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ card_id: cardId, rating, student_id: studentId }),
          });
          if (rating === "2" || rating === "3") {
            cardDiv.remove();
            updateCounter();
          }
        } finally {
          isProcessing = false;
          setButtonsEnabled(true);
        }
      };
    });
    return;
  }

  // ---------- STUDENT MODE ----------
  function showNext() {
    const hasQueue = index < queue.length;
    const hasReview = reviewPool.length > 0;

    if (!hasQueue && !hasReview) {
      container.innerHTML =
        '<div class="section-box"><p>Você estudou todos os flashcards! 🔥</p></div>';
      updateCounter();
      return;
    }

    updateCounter();

    // BUFFER RULE: use reviewPool when 5+ or when queue empty
    const useReview = (reviewPool.length >= 5) || (!hasQueue && hasReview);
    const card = useReview ? reviewPool[0] : queue[index];

    container.replaceChildren();
    container.classList.remove("fade-in");
    container.classList.add("fade-out");

    setTimeout(() => {
      container.innerHTML = `
        <div class="section-box">
          <p>${card.question}
            <button class="speak-btn" data-text="${card.question}">🔊</button>
          </p>
          <button id="toggle-answer" class="btn btn-secondary mb-3">Mostrar Resposta</button>
          <p id="answer" style="display:none;">
            ${card.answer}
            <button class="speak-btn" data-text="${card.answer}">🔊</button>
          </p>
          <div>
            <button class="btn btn-danger rate-btn" data-value="1">1</button>
            <button class="btn btn-warning rate-btn" data-value="2">2</button>
            <button class="btn btn-success rate-btn" data-value="3">3</button>
          </div>
        </div>
      `;

      container.classList.remove("fade-out");
      void container.offsetWidth;
      container.classList.add("fade-in");

      const answer = document.getElementById("answer");
      document.getElementById("toggle-answer").onclick = () => {
        answer.style.display = answer.style.display === "block" ? "none" : "block";
      };

      document.querySelectorAll(".rate-btn").forEach(btn => {
        btn.onclick = async () => {
          if (isProcessing) return;
          isProcessing = true;
          setButtonsEnabled(false);

          const rating = btn.dataset.value;

          try {
            const res = await fetch("/flashcard/review_flashcard", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ card_id: card.id, rating }),
            });

            if (!res.ok) return;

            if (rating === "1") {
              if (!reviewPool.some(c => c.id === card.id)) reviewPool.push(card);
              if (useReview && reviewPool.length > 1) reviewPool.push(reviewPool.shift());
              else if (!useReview) index++;
            } else {
              if (useReview) {
                reviewPool.shift();
              } else {
                index++;
                reviewPool = reviewPool.filter(c => c.id !== card.id);
              }
            }

            if (index > queue.length) index = queue.length;

            // decide next move
            const backToQueue = (reviewPool.length < 5) && (index < queue.length);
            if (backToQueue || reviewPool.length > 0 || (!hasQueue && hasReview)) {
              showNext();
            } else {
              showNext();
            }
          } finally {
            isProcessing = false;
            setButtonsEnabled(true);
          }
        };
      });
    }, 150);
  }

  showNext();

  // ---------- Text-to-Speech ----------
  document.addEventListener("click", e => {
    if (e.target.classList.contains("speak-btn")) {
      const text = e.target.dataset.text;
      speakText(text, e.target);
    }
  });

  updateCounter();
});
