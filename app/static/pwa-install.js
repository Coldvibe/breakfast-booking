let deferredPrompt = null;

document.addEventListener("DOMContentLoaded", () => {
  const banner = document.getElementById("pwa-install-banner");
  const installBtn = document.getElementById("pwa-install-btn");
  const closeBtn = document.getElementById("pwa-close-btn");

  if (!banner || !installBtn || !closeBtn) {
    return;
  }

  function isBannerDismissed() {
    return localStorage.getItem("pwaBannerDismissed") === "true";
  }

  function isAppInstalled() {
    return window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  }

  // Si l'app est déjà installée, on ne montre rien
  if (isAppInstalled()) {
    return;
  }

  // Fermeture manuelle du bandeau
  closeBtn.addEventListener("click", () => {
    banner.classList.add("hidden");
    localStorage.setItem("pwaBannerDismissed", "true");
  });

  // Clic sur le bouton Installer
  installBtn.addEventListener("click", async () => {
    if (!deferredPrompt) {
      return;
    }

    deferredPrompt.prompt();

    const choiceResult = await deferredPrompt.userChoice;

    if (choiceResult.outcome === "accepted") {
      banner.classList.add("hidden");
    }

    deferredPrompt = null;
  });

  // Android Chrome : événement d'installation disponible
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredPrompt = event;

    if (!isBannerDismissed()) {
      banner.classList.remove("hidden");
    }
  });

  // App installée
  window.addEventListener("appinstalled", () => {
    banner.classList.add("hidden");
    deferredPrompt = null;
    localStorage.removeItem("pwaBannerDismissed");
  });
});