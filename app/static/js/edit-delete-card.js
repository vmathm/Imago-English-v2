document.addEventListener('DOMContentLoaded', () => {
  const forms = document.querySelectorAll('.flashcard-form');
  

  // 1) Normal submit listener
  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      const submitter = e.submitter || null;
      e.preventDefault();
      performRequest(form, submitter);
    });
  });

  // 2) Fallback: event delegation for clicks on action buttons
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('button[name="action"]');
    if (!btn) return;

    const form = btn.closest('form.flashcard-form');
    if (!form) return;

    e.preventDefault(); 
    performRequest(form, btn);
  });
});

async function performRequest(form, submitter) {
  if (!form || form.dataset.busy === '1') return;
  form.dataset.busy = '1';

  try {
    const formData = new FormData(form);

    if (submitter && submitter.name) {
      formData.append(submitter.name, submitter.value);
    }

    const actionType = (submitter && submitter.value) || formData.get('action');
   
    const response = await fetch(form.getAttribute('action'), {
      method: 'POST',
      body: formData
    });

    let result;
    try {
      result = await response.json();
    } catch (err) {
      console.error('[edit-delete-card] JSON parse error', err);
      showFlash('error', 'Unexpected server response.');
      return;
    }

    showFlash(result.status, result.message || (result.status === 'success' ? 'Done.' : 'Something went wrong.'));

    if (result.status !== 'success') return;

    const cardEl   = form.closest('.flashcard');
    const statusEl = cardEl ? cardEl.querySelector('.tc-status') : null;

    if (actionType === 'delete') {
      const container = form.closest('.section-box') || cardEl || form;
      if (container) container.remove();
      return;
    }

    if (actionType === 'mark_reviewed_tc') {
      if (statusEl) statusEl.textContent = '✅ Teacher reviewed';
      if (submitter) {
        submitter.remove();     
      }
      return;
    }

    if (actionType === 'edit') {
      // If backend auto-marked as reviewed, reflect it
      if (result.reviewed_by_tc === true && statusEl) {
        statusEl.textContent = '✅ Teacher reviewed';
      }
      return;
    }
  } catch (err) {
    console.error('[edit-delete-card] network/error', err);
    showFlash('error', 'Network error. Try again.');
  } finally {
    delete form.dataset.busy;
  }
}

function showFlash(status, message) {
  const host = document.getElementById('flash-message-container');
  const div  = document.createElement('div');
  div.className = `flashcard-${status}-message`;
  div.textContent = message;
  host.appendChild(div);
  setTimeout(() => div.remove(), 1500);
}

