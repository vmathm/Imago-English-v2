document.querySelectorAll('.flashcard-form').forEach(form => {
  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData(form);

    // Add the clicked button's name/value if present
    if (e.submitter && e.submitter.name) {
      formData.append(e.submitter.name, e.submitter.value);
    }

    const actionType = formData.get('action');
    
    
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

    if (actionType === "delete" && result.status === "success") {
      form.closest(".section-box").remove();
    }
  });
});
