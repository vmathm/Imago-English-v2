// flashcards_study.js — safe DOM (no innerHTML), redirect on completion, anti-spam rating throttle

document.addEventListener("DOMContentLoaded", () => {
  // ====== Inputs from template ======
  // Cards can be injected as `flashcards` or `window.flashcards`
  const cards =
    (typeof flashcards !== "undefined" && Array.isArray(flashcards)) ? flashcards.slice() :
    (Array.isArray(window.flashcards)) ? window.flashcards.slice() :
    [];

  // Student review mode if `studentId` is defined (teacher reviewing a student's cards)
  const hasStudent = (typeof studentId !== "undefined" && studentId !== null);

  // Dashboard URL injected by template (fallback to "/")
  const DASHBOARD_URL = (typeof window.DASHBOARD_URL === "string" && window.DASHBOARD_URL) || "/";

  // ====== DOM ======
  const container = document.getElementById("flashcard-container");
  const counterEl = document.getElementById("remaining-count");
  if (!container) return;

  // ====== Early exit (no cards) ======
  if (cards.length === 0) {
    if (counterEl) counterEl.textContent = "0";
    container.replaceChildren();
    const p = document.createElement("p");
    p.textContent = "Você não tem flashcards para estudar.";
    container.appendChild(p);
    return;
  }

  // ====== State ======
  let index = 0;
  let reviewPool = [];
  const queue = [...cards];
  let isProcessing = false; // prevents overlapping async calls

  // Anti-rapid-rating throttle
  const MIN_RATING_INTERVAL_MS = 700;
  let lastRatingAt = 0;

  // ====== Utils ======
  function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
  }
  shuffle(queue);

  function csrf() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
  }

  function setButtonsEnabled(enabled) {
    document.querySelectorAll(".rate-btn, #toggle-answer").forEach(b => {
      b.style.pointerEvents = enabled ? "auto" : "none";
      b.style.opacity = enabled ? "1" : "0.6";
    });
  }

  function updateCounter() {
    if (!counterEl) return;
    let remaining;
    if (hasStudent) {
      // Count currently rendered cards in teacher mode
      remaining = container.querySelectorAll(".section-box").length;
    } else {
      // Student mode: items left + review buffer
      remaining = (queue.length - index) + reviewPool.length;
    }
    remaining = Math.max(0, remaining);
    counterEl.textContent = String(remaining);
    if (counterEl.parentElement) {
      counterEl.parentElement.style.display = remaining > 0 ? "block" : "none";
    }
  }

  // Speech synthesis
  let selectedVoice;
  function initializeVoices() {
    const voices = window.speechSynthesis.getVoices();
    selectedVoice = voices.find(v => v.lang && v.lang.startsWith("en")) || null;
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

  // Element helpers
  function makeBtn({ text, className, dataset = {}, id, onClick }) {
    const b = document.createElement("button");
    if (id) b.id = id;
    if (className) b.className = className;
    b.textContent = text;
    Object.entries(dataset).forEach(([k, v]) => b.dataset[k] = v);
    if (onClick) b.onclick = onClick;
    return b;
  }

  function makeSpeakBtn(content) {
    const b = document.createElement("button");
    b.className = "speak-btn";
    b.textContent = "🔊";
    b.setAttribute("data-text", content); // safe
    return b;
  }

  // ====== Completion redirect (shared) ======
// Prevent multiple redirects if the user double-clicks
let __redirectingCompleted = false;

async function redirectToDashboardCompleted() {
  if (__redirectingCompleted) return;
  __redirectingCompleted = true;

  const DEFAULT_MSG  = "You studied all your flashcards! 🔥";
  const DEFAULT_KIND = "success";

  // small timeout so a flaky endpoint doesn't block the redirect
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 2000);

  try {
    const token = document.querySelector('meta[name="csrf-token"]')?.content || "";
    const res = await fetch("/flashcard/completed_study", {
      method: "POST",
      headers: {
        // Flask-WTF accepts either header name
        "X-CSRF-Token": token,
        "X-CSRFToken": token
      },
      credentials: "same-origin",
      cache: "no-store",
      signal: ctrl.signal
    });

    clearTimeout(t);

    // Handle 204 or non-JSON gracefully
    let data = null;
    try { data = await res.json(); } catch { /* no body or non-json */ }

    const msg  = (data && data.message) || DEFAULT_MSG;
    const kind = (data && data.status === "success") ? "success" : DEFAULT_KIND;

    sessionStorage.setItem("flash_msg", msg);
    sessionStorage.setItem("flash_kind", kind);
  } catch {
    // Network/timeout: fall back to default client message
    sessionStorage.setItem("flash_msg", DEFAULT_MSG);
    sessionStorage.setItem("flash_kind", DEFAULT_KIND);
  } finally {
    // Always redirect
    window.location.href = DASHBOARD_URL; // defined in your template
  }
}


  // ===================== TEACHER MODE =====================
  if (hasStudent) {
    container.replaceChildren();

    queue.forEach(card => {
      const cardElement = document.createElement("div");
      cardElement.className = "section-box";
      cardElement.dataset.cardId = card.id;

      // Q
      const qP = document.createElement("p");
      const qLabel = document.createElement("strong");
      qLabel.textContent = "Q: ";
      const qText = document.createTextNode(card.question);
      const qBtn = makeSpeakBtn(card.question);
      qP.append(qLabel, qText, document.createTextNode(" "), qBtn);

      // A
      const aP = document.createElement("p");
      const aLabel = document.createElement("strong");
      aLabel.textContent = "A: ";
      const aText = document.createTextNode(card.answer);
      const aBtn = makeSpeakBtn(card.answer);
      aP.append(aLabel, aText, document.createTextNode(" "), aBtn);

      // Level
      const lvlP = document.createElement("p");
      const lvlLabel = document.createElement("strong");
      lvlLabel.textContent = "Nível: ";
      const lvlText = document.createTextNode(card.level || "—");
      lvlP.append(lvlLabel, lvlText);

      // Rate buttons
      const btnWrap = document.createElement("div");
      ["1", "2", "3"].forEach(v => {
        const cls = v === "1" ? "btn btn-danger rate-btn"
                  : v === "2" ? "btn btn-warning rate-btn"
                  : "btn btn-success rate-btn";
        const b = makeBtn({ text: v, className: cls, dataset: { value: v } });
        btnWrap.appendChild(b);
      });

      cardElement.append(qP, aP, lvlP, btnWrap);
      container.appendChild(cardElement);
    });

    updateCounter();

    // Rate handlers with throttle
    container.querySelectorAll(".rate-btn").forEach(btn => {
      btn.onclick = async () => {
        const now = Date.now();
        if (now - lastRatingAt < MIN_RATING_INTERVAL_MS) return; // too fast
        lastRatingAt = now;

        if (isProcessing) return;
        isProcessing = true;
        setButtonsEnabled(false);

        const rating = btn.dataset.value;
        const cardDiv = btn.closest(".section-box");
        const cardId = cardDiv.dataset.cardId;

        try {
          const res = await fetch("/flashcard/review_flashcard", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRF-Token": csrf()
            },
            credentials: "same-origin",
            body: JSON.stringify({ card_id: cardId, rating, student_id: studentId })
          });

          if (!res.ok) return;

          if (rating === "2" || rating === "3") {
            cardDiv.remove();
            updateCounter();
            // If teacher finished reviewing everything, redirect with success
            if (container.querySelectorAll(".section-box").length === 0) {
              redirectToDashboardCompleted();
              return;
            }
          }
        } finally {
          isProcessing = false;
          setButtonsEnabled(true);
        }
      };
    });

  // ===================== STUDENT MODE =====================
  } else {

    function renderCard(card, useReview) {
      container.replaceChildren();

      const box = document.createElement("div");
      box.className = "section-box";

      // Question + speak
      const qP = document.createElement("p");
      const qText = document.createTextNode(card.question);
      const qBtn = makeSpeakBtn(card.question);
      qP.append(qText, document.createTextNode(" "), qBtn);

      // Toggle answer
      const toggleBtn = makeBtn({
        id: "toggle-answer",
        text: "Show answer (Mostrar Resposta)",
        className: "btn btn-secondary mb-3"
      });

      // Answer + speak (hidden)
      const aP = document.createElement("p");
      aP.id = "answer";
      aP.style.display = "none";
      const aText = document.createTextNode(card.answer);
      const aBtn = makeSpeakBtn(card.answer);
      aP.append(aText, document.createTextNode(" "), aBtn);

      // Rate buttons
      const btnWrap = document.createElement("div");
      ["1", "2", "3"].forEach(v => {
        const cls = v === "1" ? "btn btn-danger rate-btn"
                  : v === "2" ? "btn btn-warning rate-btn"
                  : "btn btn-success rate-btn";
        const b = makeBtn({ text: v, className: cls, dataset: { value: v } });
        btnWrap.appendChild(b);
      });

      box.append(qP, toggleBtn, aP, btnWrap);
      container.appendChild(box);

      // Simple fade
      container.classList.remove("fade-in");
      container.classList.add("fade-out");
      void container.offsetWidth; // reflow
      container.classList.remove("fade-out");
      container.classList.add("fade-in");

      const answer = document.getElementById("answer");
      toggleBtn.onclick = () => {
        answer.style.display = (answer.style.display === "block") ? "none" : "block";
      };

      container.querySelectorAll(".rate-btn").forEach(btn => {
        btn.onclick = async () => {
          const now = Date.now();
          if (now - lastRatingAt < MIN_RATING_INTERVAL_MS) return; // too fast
          lastRatingAt = now;

          if (isProcessing) return;
          isProcessing = true;
          setButtonsEnabled(false);

          const rating = btn.dataset.value;

          try {
            const res = await fetch("/flashcard/review_flashcard", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf()
              },
              credentials: "same-origin",
              body: JSON.stringify({ card_id: card.id, rating })
            });

            if (!res.ok) return;

            if (rating === "1") {
              if (!reviewPool.some(c => c.id === card.id)) reviewPool.push(card);
              if (useReview && reviewPool.length > 1) {
                // rotate review pool: move current to the end
                reviewPool.push(reviewPool.shift());
              } else if (!useReview) {
                index++;
              }
            } else {
              if (useReview) {
                reviewPool.shift();
              } else {
                index++;
                reviewPool = reviewPool.filter(c => c.id !== card.id);
              }
            }

            if (index > queue.length) index = queue.length;

            showNext();
          } finally {
            isProcessing = false;
            setButtonsEnabled(true);
          }
        };
      });
    }

    function showNext() {
      const hasQueue = index < queue.length;
      const hasReview = reviewPool.length > 0;

      // Finished: redirect to dashboard and flash success
      if (!hasQueue && !hasReview) {
        redirectToDashboardCompleted();
        return;
      }

      updateCounter();

      // BUFFER RULE: use reviewPool when 5+ or when queue empty
      const useReview = (reviewPool.length >= 5) || (!hasQueue && hasReview);
      const card = useReview ? reviewPool[0] : queue[index];

      renderCard(card, useReview);
    }

    showNext();
  }

  // ----- Text-to-Speech (event delegation for both modes) -----
  document.addEventListener("click", e => {
    if (e.target.classList.contains("speak-btn")) {
      const text = e.target.dataset.text || "";
      speakText(text, e.target);
    }
  });

  updateCounter();
});
