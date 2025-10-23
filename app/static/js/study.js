// app/static/js/study.js

document.addEventListener("DOMContentLoaded", () => {
  if (!flashcards || flashcards.length === 0) {
    const container = document.getElementById("flashcard-container");
    container.innerHTML = "<p>Você não tem flashcards para estudar.</p>";
    return;
  }

  // ---------- Setup ----------
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

  // ---------- Counter helper ----------
  function updateCounter() {
    const remaining = (queue.length - index) + reviewPool.length;
    if (!counterEl) return;
    if (remaining > 0) {
      counterEl.textContent = remaining;
      counterEl.parentElement.style.display = "block";
    } else {
      counterEl.parentElement.style.display = "none";
    }
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
  }

  // ---------- STUDENT MODE ----------
  else {
    function showNext() {
      const hasQueue = index < queue.length;
      const hasReview = reviewPool.length > 0;

      // end condition
      if (!hasQueue && !hasReview) {
        container.innerHTML =
          '<div class="section-box"><p>Você estudou todos os flashcards! 🔥</p></div>';
        updateCounter();
        return;
      }

      updateCounter();

      // only use reviewPool when queue is fully done
      const useReview = !hasQueue && hasReview;
      const card = useReview ? reviewPool[0] : queue[index];

      // clear previous DOM (kills old listeners)
      container.replaceChildren();
      container.classList.remove("fade-in");
      container.classList.add("fade-out");

      setTimeout(() => {
        // build current card UI
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

        // fade back in
        container.classList.remove("fade-out");
        void container.offsetWidth;
        container.classList.add("fade-in");

        // toggle answer
        const answer = document.getElementById("answer");
        document.getElementById("toggle-answer").onclick = () => {
          const showing = answer.style.display === "block";
          answer.style.display = showing ? "none" : "block";
        };

        // handle rating buttons
        document.querySelectorAll(".rate-btn").forEach(btn => {
          btn.onclick = async () => {
            const rating = btn.dataset.value;

            await fetch("/flashcard/review_flashcard", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ card_id: card.id, rating }),
            });

            if (rating === "1") {
              // add to reviewPool if not already there
              if (!reviewPool.some(c => c.id === card.id)) reviewPool.push(card);

              if (useReview && reviewPool.length > 1) {
                // if already in review pool, move it to end
                reviewPool.push(reviewPool.shift());
              } else if (!useReview) {
                // continue main queue
                index++;
              }
            } else {
              // ratings 2 or 3
              if (useReview) {
                // remove once from review pool
                reviewPool.shift();
              } else {
                index++;
                // ensure it's not in reviewPool anymore
                reviewPool = reviewPool.filter(c => c.id !== card.id);
              }
            }

            // safety clamp
            if (index > queue.length) index = queue.length;

            showNext();
          };
        });
      }, 150);
    }

    showNext();
  }

  // ---------- Text-to-Speech Listener ----------
  document.addEventListener("click", e => {
    if (e.target.classList.contains("speak-btn")) {
      const text = e.target.dataset.text;
      speakText(text, e.target);
    }
  });

  updateCounter();
});
