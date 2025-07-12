
## Stylesheet Update: Bootstrap-Compatible Theming (Light + Dark Modes)

### ✅ Purpose
This update to `styles.css` modernizes the project’s design system by:

- Enabling full support for Bootstrap 5.3’s native dark mode via `data-bs-theme`
- Making all custom components adapt automatically to theme changes
- Improving maintainability through use of Bootstrap’s color variables

---

### 🌓 Theme-Specific Styling

#### 🌞 Light Mode
- `html[data-bs-theme="light"]` uses a **linear gradient** background as originally designed
- Global text is white for maximum contrast
- `.section-box`, `.card`, `.alert`, and `.message-box` use a translucent white overlay (`rgba(255, 255, 255, 0.2)`) on top of the gradient
- Navbar text is manually forced to white using:
  ```css
  html[data-bs-theme="light"] .navbar-nav .nav-link {
    color: white !important;
  }
  ```

#### 🌚 Dark Mode
- `html[data-bs-theme="dark"]` switches to a solid black background and disables the gradient
- All key components inherit Bootstrap’s `--bs-body-bg` and `--bs-body-color`
- No manual overrides are needed for text readability

---

### 🎨 Bootstrap Variable-Based Colors

To ensure consistency across both themes and easier customization, the following variables were used in place of hardcoded values:

| Bootstrap Token        | Usage Example               | Replaces            |
|------------------------|-----------------------------|---------------------|
| `--bs-danger`          | Red alert / button          | `#F37765`, `#902102`|
| `--bs-warning`         | Yellow feedback button      | `#F9F871`           |
| `--bs-success`         | Green button                | `#2FAB63`           |
| `--bs-primary`         | Primary buttons, alerts     | `#006EA8`, `#1A8784`|
| `--bs-body-bg`         | Background of dark sections | `rgba(0,0,0,0.9)`   |
| `--bs-body-color`      | Text color                  | `white`, `#000`     |

---

### 🛠️ Transition Effects

To improve the UX when toggling themes, a smooth transition was added:

```css
html {
  transition: background-color 0.4s ease, color 0.4s ease;
}
```

---

### 📌 Next Steps
- Replace remaining hardcoded colors like `#FFB559`, `#B8E067` (will be done when study route is created.)

## JavaScript Overview

### Add Flashcard Script
Handles asynchronous submission of the "Add Flashcard" form.

- File: `app/static/js/add-card.js`  
- Loaded from: `layout.html` or any page containing the `#add-card-form`
- Listens for `submit` events with `id="add-card-form"`
- Sends the request to `form.getAttribute('action')` via `fetch`
- Shows the returned message inside `#flash-message-container`
- Reset form

### Edit/Delete Flashcard Script
Provides asynchronous editing and deleting of flashcards.

- File: `app/static/js/edit-delete-card.js`
- Loaded from `layout.html`
- Listens for `submit` events on elements with the `.flashcard-form` class
- Adds the clicked button’s `name` and `value` to the `FormData` so Flask receives the `action` field
- Sends the request to `form.getAttribute('action')` via `fetch`
- Shows the returned message inside `#flash-message-container`
- If deletion succeeds, removes the corresponding card element from the page

### Search & Highlight Flashcard Script
Enables real-time search filtering, highlighting, and bringing forward matched cards.

- File: app/static/js/flashcard-search.js

- Loaded from: manage_student_cards.html and edit_cards.html

- Selects:

  #flashcard-search-input (the main search text input)

  #search-question and #search-answer (checkboxes to include question and/or answer in search)

  .flashcard (cards to be searched and reordered)

- Listens for input and change events to trigger filtering

- Checks whether each flashcard’s question or answer contains the search query

- Adds the highlight class to matched cards 

- Reorders flashcards so matches appear first, by appending them back into the container

- Displays match count in the #match-count element below the search bar

### Study Mode Script

`flashcards/study.html` template loads an empty container and makes the
card list available to JavaScript at `app/static/js/study.js`. 

- File:`app/static/js/study.js`
- shuffles the cards and displays them one by one (Fisher–Yates shuffle algorithm); 
- uses the `fade-in` and `fade-out` classes to change the oppacity of the flashcard container `id=flashcard-container`
- toggles the answer when the user clicks “Mostrar Resposta”.
- Buttons 1, 2, and 3 send the chosen rating to `/flashcard/review_flashcard`.
- A rating of 1 moves the card to the end of the queue; otherwise it is removed.
- When no cards remain, the message `“Você estudou todos os flashcards!”` is shown.

### Theme Toggle Script

Handles dark mode switching using Bootstrap 5.3’s `data-bs-theme` attribute.

- File: `app/static/js/theme-toggle.js`
- Loads on every page via `<script>` in `layout.html`
- Saves user preference in `localStorage`
- Automatically re-applies the saved theme on page load
- Connected to the checkbox input with `id="dark-mode-toggle"`






 

### Auto Expand Input Script
Used to auto-resize textarea inputs in flashcard forms based on their content.

- File: app/static/js/auto-expand-input.js

- Targets any <textarea> with the class auto-expand

- Sets the initial height to one line using rows=1 and min-height: 1.5em

- Listens for input events and adjusts height based on scrollHeight

- If empty, the height is reset to the default single-line height (1.5em)

- Disables manual resize (resize: none) and hides scrollbars


## Spaced Repitition Algorithm
This system blends spaced repetition with gamified rewards. While based on SuperMemo(SM-2), it has been customized to support:

- Real-time retry logic: cards rated 1 go back to the end of the queue. 
- Role-sensitive scoring: Teachers can review flashcards with students during class and rating will award the points to the student. 
- Simplified ease/interval management: Intervals are days and not hours, as the goal is a daily review of available cards.

