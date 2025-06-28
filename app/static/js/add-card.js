// Handle AJAX add-card form submission
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('add-card-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const response = await fetch(form.getAttribute('action'), {
      method: 'POST',
      body: formData
    });

    const result = await response.json();

    const flashDiv = document.createElement('div');
    flashDiv.className = `flashcard-${result.status}-message`;
    flashDiv.textContent = result.message;
    document.getElementById('flash-message-container').appendChild(flashDiv);

    setTimeout(() => flashDiv.remove(), 3000);

    if (result.status === 'success') {
      form.reset();
    }
  });
});
