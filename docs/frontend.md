
## Stylesheet Update: Bootstrap-Compatible Theming (Light + Dark Modes)

### Purpose
This update to `styles.css` modernizes the project’s design system by:

* Enabling full support for Bootstrap 5.3’s native dark mode via `data-bs-theme`
* Making all custom components adapt automatically to theme changes
* Improving maintainability through use of Bootstrap’s color variables

---

### Theme-Specific Styling

#### Light Mode
* `html[data-bs-theme="light"]` uses a **linear gradient** background as originally designed
* Global text is white for maximum contrast
* `.section-box`, `.card`, `.alert`, and `.message-box` use a translucent white overlay (`rgba(255, 255, 255, 0.2)`) on top of the gradient
* Navbar text is manually forced to white using:
  ```css
  html[data-bs-theme="light"] .navbar-nav .nav-link {
    color: white !important;
  }
  ```

#### 🌚 Dark Mode
* `html[data-bs-theme="dark"]` switches to a solid black background and disables the gradient
* All key components inherit Bootstrap’s `--bs-body-bg` and `--bs-body-color`
* No manual overrides are needed for text readability

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

### Transition Effects

To improve the UX when toggling themes, a smooth transition was added:

```css
html {
  transition: background-color 0.4s ease, color 0.4s ease;
}
```

---

###  Next Steps
* Replace remaining hardcoded colors like `#FFB559`, `#B8E067` (will be done when study route is created.)

## JavaScript Overview

### Add Flashcard Script
Handles asynchronous submission of the "Add Flashcard" form.

* File: `app/static/js/add-card.js`  
* Loaded from: `layout.html` or any page containing the `#add-card-form`
* Listens for `submit` events with `id="add-card-form"`
* Sends the request to `form.getAttribute('action')` via `fetch`
* Shows the returned message inside `#flash-message-container`
* Reset form

### Edit/Delete/Review Flashcard Script

Provides asynchronous editing, deleting, and teacher review of flashcards without page reload.

* File: `app/static/js/edit-delete-card.js`
* Loaded from: `layout.html`
* Targets: each `<form class="flashcard-form" …>` rendered per flashcard

#### What it does

* Attaches listeners after `DOMContentLoaded`, ensuring forms exist.
* Adds a document-level **click delegation** fallback for `button[name="action"]` (Defensive coding for unlikely old browser usage or future features that allows attaching flashcards to the DOM via js)
* Uses a `data-busy` flag to block duplicate form submissions.
* Ensures the clicked button’s `name`/`value` are included in `FormData` so Flask receives the `action` field
* Sends `POST` to `form.getAttribute('action')` via `fetch`
* Expects JSON `{ status: "success"|"error", message: "...", ... }`
* Shows the server message inside `#flash-message-container` 
* Applies per-action UI updates:
  - `action="edit"` → on success, if `reviewed_by_tc: true` is returned (i.e. the teacher edited it) , flips the on-card status to *✅Teacher reviewed*, otherwise removes a previously *✅Teacher reviewed* status.
  - `action="delete"` → removes the card container from the DOM
  - `action="mark_reviewed_tc"` → flips the on-card status to *✅Teacher reviewed* and removes clicked button  

#### Required HTML hooks

* Each flashcard form:
  - Has class `flashcard-form` and an `action` pointing to the edit endpoint
  - Includes CSRF via `{{ forms[card.id].hidden_tag() }}`
  - Contains buttons with `name="action"` and values: `edit`, `delete`, `mark_reviewed_tc`

* Each card container includes a status element:
  - `Teacher reviewed: <span class="tc-status">{{ '✅Teacher reviewed' if card.reviewed_by_tc }}</span>`
* Global flash host:
  - `<div id="flash-message-container"></div>` 


#### Backend contract (expected responses)

* Success (any action): `{"status":"success","message":"...", "card_id": <int>, "reviewed_by_tc": <bool optional>}`
* Error (validation/authorization/not found): `{"status":"error","message":"..."}` with appropriate HTTP status code





### Search & Highlight Flashcard Script
Enables real-time search filtering, highlighting, and bringing forward matched cards.

* File: `app/static/js/flashcard-search.js`

* Loaded from: `manage_student_cards.html` and `edit_cards.html`

* Selects:

  `#flashcard-search-input` (the main search text input)

  `#search-question` and `#search-answer` (checkboxes to include question and/or answer in search)

  `.flashcard` (cards to be searched and reordered)

* Listens for input and change events to trigger filtering

* Checks whether each flashcard’s question or answer contains the search query

* Adds the highlight class to matched cards 

* Reorders flashcards so matches appear first, by appending them back into the container

* Displays match count in the `#match-count` element below the search bar

### Study Mode Script

`flashcards/study.html` template loads an empty container and makes the
card list available to JavaScript at `app/static/js/study.js`.

* File: `app/static/js/study.js`

* Shuffles the cards and displays them one by one (Fisher–Yates shuffle algorithm).

* Uses the `fade-in` and `fade-out` classes to change the opacity of the flashcard container (`id=flashcard-container`).
* Toggles the answer when the user clicks **“Mostrar Resposta”**.

* Buttons **1, 2, and 3** send the chosen rating to `/flashcard/review_flashcard`.
Note: The review logic follows the customized spaced repetition algorithm (see `docs/architecture.md`).

* A rating of **1** moves the card to the end of the queue; otherwise it is removed.

* When no cards remain, the message **“Você estudou todos os flashcards!”** is shown.

* If Study Mode is being used by a teacher from `manage_student_cards.html`, then all cards are rendered to the page with level information, and rating **1** does not remove them.

* Each question and answer also includes a **🔊 button** that uses the Web Speech API for text-to-speech. The script initializes an English voice, provides playback with adjustable rate and pitch, and highlights the button with a smooth animation while speaking.


### Theme Toggle Script

Handles dark mode switching using Bootstrap 5.3’s `data-bs-theme` attribute.

* File: `app/static/js/theme-toggle.js`
* Loads on every page via `<script>` in `layout.html`
* Saves user preference in `localStorage`
* Automatically re-applies the saved theme on page load
* Connected to the checkbox input with `id="dark-mode-toggle"`






 

### Auto Expand Input Script
Used to auto-resize textarea inputs in flashcard forms based on their content.

* File: `app/static/js/auto-expand-input.js`

* Targets any <textarea> with the class auto-expand

* Sets the initial height to one line using rows=1 and min*height: 1.5em

* Listens for input events and adjusts height based on scrollHeight

* If empty, the height is reset to the default single*line height (1.5em)

* Disables manual resize (resize: none) and hides scrollbars

### Audiobook Script 
* File: `app/static/js/audiobook.js`

* Loaded by: `audiobook/audiobooks.html`

* Handles text selection on the audiobook page, calls the `/audiobook/translate` endpoint (which uses `services/translate.py → translate_text(text, target_language="pt")`), and prompts the user to create a flashcard.

* Opens a modal with two editable fields (`Question` and `Answer`).

* Provides a **Flip** button to swap the contents of question and answer.

* On confirm, posts the values to `/flashcard/addcards`.

* Shows success/error messages in `#flash-message-container`.




## Ranking Page

The `/ranking` route displays three leaderboards using DataTables:

1. **Top 3 Students of All Time** – Sorted by each user’s highest `max_points`.
2. **Student Ranking** – Lists all students ordered by a computed `Total` value (`points` × `study_streak` when `study_streak > 0`).
3. **Teacher Ranking** – Same structure as the student table, but for users with the `teacher` role.

`ranking.html` loads the DataTables CSS/JS and uses a helper
function to initialize each table. The first column is auto-numbered whenever the
table is sorted or searched. All tables disable searching, paging and info to the benefit of a cleaner page. 


## Calendar

  The calendar section uses a custom Jinja filter for **dateformat** `@bp.app_template_filter('dateformat')`
  *File:* `app/calendar/routes.py`  
  *Usage:* `{{ start|dateformat }} - {{ end|dateformat }}`
  Formats Python `datetime` objects inside calendar templates.  
  Default format is `'%H:%M'` (hour:minute).  

## CSRF Protection
All Flask-WTF forms include:
 {{ form.hidden_tag() }} - ensures CSRF tokens are submitted properly in forms.

JS (AJAX) requests:  
<meta name="csrf-token" content="{{ csrf_token() }}">  
This exposes the CSRF token to JavaScript so it can be included in the `X-CSRFToken` header when making `fetch` (AJAX) calls.
