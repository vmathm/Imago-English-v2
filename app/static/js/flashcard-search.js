document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('flashcard-search-input');
  const searchQuestion = document.getElementById('search-question');
  const searchAnswer = document.getElementById('search-answer');
  const cards = document.querySelectorAll('.flashcard');

function runSearch() {
  const rawQuery = input.value.toLowerCase();
  const query = rawQuery; // keep spaces!
  const hasRealQuery = rawQuery.trim().length > 0;

  let matchCount = 0;

  const container = cards[0]?.parentElement;
  const matchedCards = [];
  const unmatchedCards = [];

  cards.forEach(card => {
    card.classList.remove('highlight');
    const questionField = card.querySelector('[name$="question"]');
    const answerField   = card.querySelector('[name$="answer"]');

    const questionText = questionField ? questionField.value.toLowerCase() : "";
    const answerText   = answerField   ? answerField.value.toLowerCase()   : "";

    let match = false;
    if (hasRealQuery) {
      if (
        searchQuestion.checked &&
        questionField &&
        questionText.includes(query)
      ) {
        match = true;
      }
      if (
        searchAnswer.checked &&
        answerField &&
        answerText.includes(query)
      ) {
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
    [...matchedCards, ...unmatchedCards].forEach(card => {
      container.appendChild(card);
    });
  }

  document.getElementById('match-count').textContent =
    hasRealQuery ? `${matchCount} match${matchCount !== 1 ? 'es' : ''} found` : '';
}



  input.addEventListener('input', runSearch);
  searchQuestion.addEventListener('change', runSearch);
  searchAnswer.addEventListener('change', runSearch);
});
