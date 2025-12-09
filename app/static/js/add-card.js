document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('add-card-form');
  if (!form) return;

  const csrfToken = document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute('content');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(form);

    try {
      const response = await fetch(form.getAttribute('action'), {
        method: 'POST',
        headers: {
          ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
          'X-Requested-With': 'XMLHttpRequest',
          // 'Accept': 'application/json',  // optional now
        },
        body: formData,
      });

      // 🔴 inactive user: server returned inactive_user.html with 403
      if (response.status === 403) {
        const html = await response.text();
        document.open();
        document.write(html);
        document.close();
        return;
      }

      // ✅ normal flow: parse JSON and show flash
      const result = await response.json();

      if (typeof showFlash === 'function') {
        const kind = result.status === 'success' ? 'success' : 'error';
        showFlash(result.message || 'Unexpected response.', kind);
      }

      if (result.status === 'success') {
        form.reset();
      }
    } catch (err) {
      console.error('Error submitting add-card form:', err);
      if (typeof showFlash === 'function') {
        showFlash('Erro ao adicionar o flashcard. Tente novamente.', 'error');
      }
    }
  });
});
