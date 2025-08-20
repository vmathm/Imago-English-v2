document.addEventListener("DOMContentLoaded", () => {
  shuffle(flashcards);
  const queue = flashcards;
  const container = document.getElementById("flashcard-container");
  let index = 0;

  function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
  }



let selectedVoice;

// Initialize voices
function initializeVoices() {
  const voices = window.speechSynthesis.getVoices();
  selectedVoice = voices.find(voice => voice.lang.startsWith('en')) || null;
}

window.speechSynthesis.onvoiceschanged = initializeVoices;
if (window.speechSynthesis.getVoices().length > 0) {
  initializeVoices();
}

// Speak helper
function speakText(text, element) {
  const speechSynthesis = window.speechSynthesis;

  // Cancel any current speech
  if (speechSynthesis.speaking || speechSynthesis.pending) {
    speechSynthesis.cancel();
  }

  let speechText = new SpeechSynthesisUtterance(text);
  speechText.lang = 'en-GB';
  speechText.rate = 0.8;
  speechText.pitch = 1.1;

  if (selectedVoice) {
    speechText.voice = selectedVoice;
  }

  // Add visual feedback
  if (element) {
    element.classList.add('speaking');
    speechText.onend = () => element.classList.remove('speaking');
  }

  speechSynthesis.speak(speechText);
}




if (typeof studentId !== 'undefined' && studentId !== null) {
  container.innerHTML = ""; // Clear the container

  queue.forEach((card) => {
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

  document.querySelectorAll(".rate-btn").forEach((btn) => {
    btn.onclick = async () => {
      const rating = btn.dataset.value;
      const cardDiv = btn.closest(".section-box");
      const cardId = cardDiv.dataset.cardId;

      await fetch("/flashcard/review_flashcard", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ card_id: cardId, rating: rating, student_id: studentId })
      });

      if (rating === "2" || rating === "3") {
        cardDiv.remove(); // Remove flashcard from the view
      }
    };
  });
  
}else {
  
  function showNext() {
    if (index >= queue.length) {
      container.innerHTML = "<p>Você estudou todos os flashcards!</p>";
      return;
    }

    
    container.classList.remove("fade-in");
    container.classList.add("fade-out");

    setTimeout(() => {
      const card = queue[index];

    container.innerHTML = `
      <div class="section-box">
        <p>${card.question} 
          <button class="speak-btn" data-text="${card.question}">🔊</button></p>
        <button id="toggle-answer" class="btn btn-secondary mb-3">Mostrar Resposta</button>
        <p id="answer" style="display:none;">${card.answer}
          <button class="speak-btn" data-text="${card.answer}">🔊</button></p>
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
        const showing = answer.style.display === "block";
        answer.style.display = showing ? "none" : "block";
      };

      document.querySelectorAll(".rate-btn").forEach((btn) => {
        btn.onclick = async () => {
          const rating = btn.dataset.value;

      
        
          await fetch("/flashcard/review_flashcard", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ card_id: card.id, rating: rating })
          });

          if (rating === "1") {
            queue.push(card);
          }
          index++;
          showNext();
        };
      });
    }, 150);
  }

  showNext();
}

  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("speak-btn")) {
      const text = e.target.dataset.text;
      speakText(text, e.target);
    }
  });
});
