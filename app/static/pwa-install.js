let deferredPrompt = null;

document.addEventListener("DOMContentLoaded", () => {
  const banner = document.getElementById("pwa-install-banner");
  const title = banner?.querySelector(".pwa-install-banner__text strong");
  const text = banner?.querySelector(".pwa-install-banner__text p");
  const installBtn = document.getElementById("pwa-install-btn");
  const closeBtn = document.getElementById("pwa-close-btn");

  if (!banner || !title || !text || !installBtn || !closeBtn) {
    return;
  }

  function isBannerDismissed() {
    return localStorage.getItem("pwaBannerDismissed") === "true";
  }

  function isAppInstalled() {
    return window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  }

  function isIos() {
    return /iphone|ipad|ipod/i.test(window.navigator.userAgent);
  }

  function isSafari() {
    const ua = window.navigator.userAgent;
    return /safari/i.test(ua) && !/crios|fxios|edgios|opr|opera|android/i.test(ua);
  }

  function showAndroidBanner() {
    title.textContent = "Installer Zack & Snack";
    text.textContent = "Ajoute l’application à ton écran d’accueil pour un accès rapide.";
    installBtn.style.display = "";
    banner.classList.remove("hidden");
  }

  function showIosBanner() {
    title.textContent = "Installer Zack & Snack";
    text.innerHTML = 'Dans Safari, touche <b>Partager</b> puis <b>Ajouter à l’écran d’accueil</b>.';
    installBtn.style.display = "none";
    banner.classList.remove("hidden");
  }

  if (isAppInstalled()) {
    return;
  }

  closeBtn.addEventListener("click", () => {
    banner.classList.add("hidden");
    localStorage.setItem("pwaBannerDismissed", "true");
  });

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

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredPrompt = event;

    if (!isBannerDismissed()) {
      showAndroidBanner();
    }
  });

  window.addEventListener("appinstalled", () => {
    banner.classList.add("hidden");
    deferredPrompt = null;
    localStorage.removeItem("pwaBannerDismissed");
  });

  // Fallback iOS Safari
  if (isIos() && isSafari() && !isBannerDismissed()) {
    showIosBanner();
  }
});