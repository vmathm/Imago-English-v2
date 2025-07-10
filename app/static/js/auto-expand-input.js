document.addEventListener("DOMContentLoaded", function () {
  const expandAreas = document.querySelectorAll(".auto-expand");
  expandAreas.forEach(textarea => {
    textarea.style.overflow = "hidden";
    textarea.style.resize = "none";
    textarea.rows = 1;  // ensure it's just 1 line by default

    const autoResize = () => {
      textarea.style.height = "auto";
      const scrollHeight = textarea.scrollHeight;
      // Only grow if user types
      if (textarea.value.trim() === "") {
        textarea.style.height = "1.5em"; // match single-line height
      } else {
        textarea.style.height = scrollHeight + "px";
      }
    };

    textarea.addEventListener("input", autoResize);
    autoResize(); // run once on load
  });
});
