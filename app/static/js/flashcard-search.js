document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('flashcard-search-input');
  const searchQuestion = document.getElementById('search-question');
  const searchAnswer = document.getElementById('search-answer');
  const cards = document.querySelectorAll('.flashcard');

function runSearch() {
  const query = input.value.trim().toLowerCase();
  let matchCount = 0;

  const container = cards[0]?.parentElement; 
  const matchedCards = [];
  const unmatchedCards = [];

  cards.forEach(card => {
    card.classList.remove('highlight');
    const questionField = card.querySelector('[name$="question"]');
    const answerField = card.querySelector('[name$="answer"]');

    let match = false;
    if (query) {
      if (searchQuestion.checked && questionField &&
          questionField.value.toLowerCase().includes(query)) {
        match = true;
      }
      if (searchAnswer.checked && answerField &&
          answerField.value.toLowerCase().includes(query)) {
        match = true;
      }
    }

    if (match) {
 
      card.classList.add('highlight');
      matchedCards.push(card);
      matchCount++;
    } else {
      unmatchedCards.push(card);
    }
  });

  if (container) {
    // Clear and re-append in desired order
    [...matchedCards, ...unmatchedCards].forEach(card => {
      container.appendChild(card); // Moves the node to the end of container
    });
  }

  document.getElementById('match-count').textContent =
    query ? `${matchCount} match${matchCount !== 1 ? 'es' : ''} found` : '';
}

  input.addEventListener('input', runSearch);
  searchQuestion.addEventListener('change', runSearch);
  searchAnswer.addEventListener('change', runSearch);
});
