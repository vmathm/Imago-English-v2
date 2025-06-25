console.log("Script loaded")
document.querySelectorAll('.flashcard-form').forEach(form => {
  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const cardId = form.dataset.cardId;
    const formData = new FormData(form);
    const action = formData.get('action');

    const response = await fetch(`edit_card/${cardId}`, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();

    // Show flash message
    const flashDiv = document.createElement('div');
    flashDiv.className = `flashcard-${result.status}-message`;
    flashDiv.textContent = result.message;
    document.getElementById('flash-message-container').appendChild(flashDiv);

    setTimeout(() => flashDiv.remove(), 3000);

    if (action === "delete" && result.status === "success") {
      document.getElementById(`card-${cardId}`).remove();
    }
  });
});
