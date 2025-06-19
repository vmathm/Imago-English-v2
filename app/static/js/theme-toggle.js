// Function to toggle dark mode

function toggleDarkMode() {

  const html = document.documentElement;
  const newTheme = html.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
  html.setAttribute("data-bs-theme", newTheme);
  localStorage.setItem("imago-theme", newTheme);
}

// Set saved theme on load + checkbox sync
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("dark-mode-toggle");
  const saved = localStorage.getItem("imago-theme") || "light";
  
  // Apply saved theme
  document.documentElement.setAttribute("data-bs-theme", saved);

  // Update toggle position
  if (toggle) {
    toggle.checked = saved === "dark";

    // Attach change listener
    toggle.addEventListener("change", () => {
      toggleDarkMode();
    });
  }
});
