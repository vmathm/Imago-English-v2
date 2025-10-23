// app/static/js/study.js  — FINAL BUFFERED VERSION

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
        const rating = btn.dataset.value;
        const cardDiv = btn.closest(".section-box");
        const cardId = cardDiv.dataset.cardId;

        await fetch("/flashcard/review_flashcard", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ card_id: cardId, rating, student_id: studentId }),
        });

        if (rating === "2" || rating === "3") {
          cardDiv.remove();
          updateCounter();
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

    // ✅ BUFFER RULE:
    // use reviewPool when it has 5 or more cards,
    // or when queue is empty but reviewPool still has some
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
          const rating = btn.dataset.value;

          await fetch("/flashcard/review_flashcard", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ card_id: card.id, rating }),
          });

          if (rating === "1") {
            // Add to review pool if not already there
            if (!reviewPool.some(c => c.id === card.id)) reviewPool.push(card);

            // Move to end if already looping in review pool
            if (useReview && reviewPool.length > 1) reviewPool.push(reviewPool.shift());
            else if (!useReview) index++;

          } else {
            // Rating 2 or 3
            if (useReview) {
              // Graduates out of review pool
              reviewPool.shift();
            } else {
              index++;
              // Remove from review pool if present
              reviewPool = reviewPool.filter(c => c.id !== card.id);
            }
          }

          // Safety clamp
          if (index > queue.length) index = queue.length;

          // After success, check if we can resume new cards
          // (if <5 failures left and still queue to show)
          const backToQueue = (reviewPool.length < 5) && (index < queue.length);
          if (backToQueue) {
            // resume pulling new cards
            showNext();
          } else if (reviewPool.length > 0) {
            // continue looping failed cards
            showNext();
          } else {
            // all done
            showNext();
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
