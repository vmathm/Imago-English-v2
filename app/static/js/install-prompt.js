let deferredPrompt;
const installButton = document.getElementById("install-button");

window.addEventListener("beforeinstallprompt", (e) => {
  // Prevent the default browser mini-infobar
  e.preventDefault();
  deferredPrompt = e;

  // Show your custom install button
  installButton.style.display = "inline-block";
});

installButton.addEventListener("click", async () => {
  if (!deferredPrompt) return;

  // Show the browser’s native install prompt
  deferredPrompt.prompt();

  // Wait for user response
  const { outcome } = await deferredPrompt.userChoice;
  console.log(`User response: ${outcome}`);

  // Hide the button again
  installButton.style.display = "none";

  // Reset prompt so it doesn't fire twice
  deferredPrompt = null;
});

window.addEventListener("appinstalled", () => {
  console.log("App installed!");
  installButton.style.display = "none";
});
