// Prevent redeclaration if this script is ever executed twice
if (!window.hasOwnProperty("deferredPrompt")) {
  window.deferredPrompt = null;

  // Cache the install button once
  const installButton = document.getElementById("install-button");

  if (installButton) {
    // Hide it initially
    installButton.style.display = "none";

    window.addEventListener("beforeinstallprompt", (e) => {
      // Stop the automatic mini-infobar
      e.preventDefault();
      window.deferredPrompt = e;

      // Show your custom install button
      installButton.style.display = "inline-block";
    });

    installButton.addEventListener("click", async () => {
      if (!window.deferredPrompt) return;

      // Show the browser’s native install prompt
      window.deferredPrompt.prompt();

      // Wait for user response
      const { outcome } = await window.deferredPrompt.userChoice;
      console.log(`User response: ${outcome}`);

      // Hide the button again
      installButton.style.display = "none";

      // Reset prompt so it doesn't fire twice
      window.deferredPrompt = null;
    });

    window.addEventListener("appinstalled", () => {
      console.log("App installed!");
      installButton.style.display = "none";
    });
  } else {
    console.warn("Install button not found in DOM.");
  }
}
