
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

#### 🌚 Dark Mode (DISABLED)
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

* When no cards remain, the message **“  todos os flashcards!”** is shown.

* If Study Mode is being used by a teacher from `manage_student_cards.html`, then all cards are rendered to the page with level information, and rating **1** does not remove them.

* Each question and answer also includes a **🔊 button** that uses the Web Speech API for text-to-speech. The script initializes an English voice, provides playback with adjustable rate and pitch, and highlights the button with a smooth animation while speaking.


### Theme Toggle Script (DISABLED)

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

#### Extra features:

* Mobile touch support with contextmenu prevention to hide the copy/share popup on Chrome and iOS.

* Dynamically enable/disable text selection depending on whether the modal is open using toggleSelection()


## Dashboard (`dashboard.html`)

The dashboard is the main landing page after login. It adapts to the current user's role (`student`, `teacher`, or `@dmin!`) and aggregates shortcuts, alerts, and personal stats.

### PWA install button

At the bottom-right corner of the screen there is a floating PWA install button:

- Element: `#install-button`
- Initially hidden (`display:none`) and only shown when `install-prompt.js` fires the custom install event.
- Label: `📲 Instalar App`
- Purpose: allow users to install Imago English as a Progressive Web App on supported devices.

### Header and username management

At the top of the dashboard:

- Welcomes the user by `current_user.user_name`.
- Shows the current role in bold: `({{ current_user.role }})`.

There is a collapsible section to change the username:

- Triggered by a small link-button: “Change username (alterar nome de usuário)”.
- When expanded, it shows a form (`user_name_form`) that:
  - Prefills the field with `suggested_username`.
  - Submits to `dashboard.set_username`.
- Validation errors are displayed below the field in small red text.

If the user has an assigned teacher (`current_user.assigned_teacher_id`):

- Shows:  
  `Professor (Teacher): <teacher name>`.

### Flashcards section

The dashboard always shows the user’s flashcard status.

#### Due flashcards alert

If `due_flashcards > 0`:

- Renders a green alert (`alert alert-success`) with:
  - English message:  
    “You have **N** flashcard(s) to study today!”
  - Portuguese translation in `<small>`:  
    “Você tem **N** flashcard(s) para estudar hoje!” with a 📚 emoji.
- Includes a “Study (Estudar)” button:
  - Submits a `GET` form to `flashcard.study`.

#### No due flashcards message

If `due_flashcards == 0`:

- Shows an info alert (`alert alert-info`) with:
  - “No due flashcards”
  - Translation: “Nenhum flashcard pendente” with a 🎉 emoji.

### Audiobook alert

If the user has an audiobook linked via `current_user.audiobook`:

- Renders a green alert (`alert alert-success`) right after the flashcard alerts.
- Content:
  - English:  
    `📖🎧 You have a new audiobook activity: <title>.`
  - Portuguese translation in `<small>`:  
    “Você tem uma nova atividade de audiobook: **<title>**. Confira na seção de audiobooks.”
- Includes an “Audiobook” button:
  - Submits a `GET` form to `audiobook.audiobooks`.
  - For students, this opens **their own** audiobook page.

If `current_user.audiobook` is `None`, this block is not rendered.

### Role-specific dashboards

Below the alerts, the dashboard injects different partials based on user role:

- `teacher` → includes `partials/teacher_dashboard.html`
- `@dmin!` → includes `partials/admin_dashboard.html`
- Students see only the personal stats boxes described below.

---

## Teacher Dashboard (`partials/teacher_dashboard.html`)

Visible only when `current_user.role == 'teacher'`.

### Calendar shortcut

At the top, teachers have a quick access button:

- Form: `GET` to `calendar.teacher_calendar` with `user_name=current_user.user_name`.
- Button label: `Check Calendar`.

### Assigned students accordion

If `assigned_students` is not empty:

- Shows a “Assigned Students” section.
- Uses a Bootstrap accordion (`#studentsAccordion`) where each item represents a student.
- Header:
  - Displays `student.name`.
  - If there are unreviewed flashcards (`unreviewed_counts.get(student.id)`), shows a red badge:  
    `<N> unreviewed`.
  - The header button is highlighted (`bg-warning-subtle`) when the student has unreviewed cards.

Inside each student’s accordion body:

1. **Student info**
   - Email, role, ID, and level shown in a small muted paragraph.

2. **Manage flashcards**
   - Button: “Manage flashcards”.
   - Link to `flashcard.manage_student(student_id=student.id)`.

3. **Audiobook management**
   - Button: “Audiobook” — opens a small modal for that specific student:
     - `data-bs-target="#audiobookModal-{{ student.id }}"`
   - Below the button, current audiobook info:
     - If `student.audiobook` exists:
       - Shows a “Current audiobook” label and a clickable title:
         - Link: `url_for('audiobook.audiobooks', user_id=student.id)`
         - Styled as muted, no underline.
         - When clicked, opens the audiobook page **for that student**, using the logic in `audiobook.routes.audiobooks`.
     - If no audiobook:
       - Displays “No audiobook assigned” in muted text.

   - The upload modal for each student:
     - Form: `POST` to `audiobook.assign_audiobook(user_id=student.id)`.
     - Two fields:
       - `text_file` (expected `.txt`).
       - `audio_file` (expected `.mp3`).
     - Help text: max ~10 MB total, `.txt` for text and `.mp3` for audio.
     - Footer with “Cancel” and “Upload” buttons.

4. **Learning language selector**
   - Form posting to `admin.set_language(student_id=student.id)`.
   - Select menu with:
     - `English` (`en`)
     - `Brazilian Portuguese` (`pt-BR`)
   - Current value is selected based on `student.learning_language`.

5. **Update level**
   - Form posting to `admin.update_student_level`.
   - Uses `change_student_level_form` with:
     - Hidden `student_id`
     - `level` select
     - Submit button (“Update”) in a small input group.

If there are no assigned students:

- Shows: “No students assigned yet.”

Below the student management area, the page continues with “Personal User Information” (teacher’s own profile details).

---

## Admin Dashboard (`partials/admin_dashboard.html`)

Visible only when `current_user.role == '@dmin!'`.

Rendered inside a `section-box` styled container with a title “Admin Controls” and a Bootstrap accordion (`#adminAccordion`).

### Admin actions

Each accordion item wraps a form:

1. **Assign Student to Teacher**
   - Form: `admin.assign_student`
   - Fields:
     - `assign_form.student_id` (select)
     - `assign_form.teacher_id` (select)
   - Submit: primary button (“Assign”).

2. **Unassign Student**
   - Form: `admin.unassign_student`
   - Field:
     - `unassign_form.student_id` (select)
   - Submit: warning button (“Unassign”).

3. **Change User Role**
   - Form: `admin.change_role`
   - Fields:
     - `change_role_form.user_id` (select)
     - `change_role_form.role` (select)
   - Submit: secondary button (“Change role”).

4. **Activate / Deactivate User**
   - Form: `admin.toggle_active_status`
   - Field:
     - `toggle_active_status_form.user_id` (select)
   - Submit: primary button (“Toggle active”).

5. **Hard Delete User**
   - Form: `admin.delete_user` with JS confirm:
     - `onsubmit="return confirm('Are you sure you want to delete this user?');"`
   - Field:
     - `delete_user_form.user_id` (select)
   - Submit: danger button (“Hard Delete User”).

Below the admin controls, there is a “Personal User Information” section showing the admin’s own details.

---

## Personal stats boxes

At the bottom of the dashboard, there are small “section-box” panels showing user stats:

1. **Total cards studied**
   - Label in English and Portuguese.
   - Value: `current_user.flashcards_studied` with 🃏 emoji.

2. **Study streak**
   - Label: “Study streak (Sequência de estudos)”.
   - Shows `current_user.study_streak` and pluralizes “day(s)” in both languages.


3. **Max study streak** (teachers only)
   - Label: “Max study streak (Máxima sequência de estudos)”.
   - Shows `current_user.max_study_streak` with day(s) in pt/en.


4. **Rate 3 percentage** (teachers only)
   - Label: “Rate 3 percentage (Percentual de notas 3)”.
   - Calculates:
     - `studied = current_user.flashcards_studied or 0`
     - `r3 = current_user.rate_three_count or 0`
     - `pct = (r3 / studied * 100)` if both > 0, else a fallback (85% for some seeded demo IDs, otherwise 0).
   - Displays `pct` as a percentage.


## Leaderboard Page

The `/leaderboard` route displays three rankings using DataTables:

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


## Progressive Web App: Web App Manifest

The app is installable as a PWA and exposes a standard Web App Manifest.

**File:** `static/manifest.webmanifest` (served from `/manifest.webmanifest`)

Key fields:

- `name` / `short_name`  
  Used for the install prompt and the app label on devices.

- `start_url` and `scope`

  ```json
  "start_url": "/dashboard/",
  "scope": "/dashboard/"

* The PWA is intentionally scoped only to `/dashboard/…`.
  Auth and OAuth routes (e.g. `/auth/...`, `/login/google/authorized`) live outside this scope so that Google login always runs in the regular browser context. (More about this in [architecture.md](architecture.md))


