
## 🎨 Stylesheet Update: Bootstrap-Compatible Theming (Light + Dark Modes)

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

## 🧠 JavaScript Overview
###  Edit/Delete Flashcard Script
Provides asynchronous editing and deleting of flashcards.

- File: `app/static/js/edit-delete-card.js`
- Loaded from `layout.html` on the edit cards page
- Listens for `submit` events on elements with the `.flashcard-form` class
- Adds the clicked button’s `name` and `value` to the `FormData` so Flask receives the `action` field
- Sends the request to `form.getAttribute('action')` via `fetch`
- Shows the returned message inside `#flash-message-container`
- If deletion succeeds, removes the corresponding card element from the page

###  Theme Toggle Script

Handles dark mode switching using Bootstrap 5.3’s `data-bs-theme` attribute.

- File: `app/static/js/theme-toggle.js`
- Loads on every page via `<script>` in `layout.html`
- Saves user preference in `localStorage`
- Automatically re-applies the saved theme on page load
- Connected to the checkbox input with `id="dark-mode-toggle"`



