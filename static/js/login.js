// Login Page Interactive Controls
document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("togglePassword");
  const passwordInput = document.getElementById("password");
  const loginForm = document.getElementById("loginForm");
  const submitBtn = document.getElementById("loginSubmitBtn");

  if (toggleBtn && passwordInput) {
    toggleBtn.addEventListener("click", () => {
      const isPassword = passwordInput.type === "password";
      passwordInput.type = isPassword ? "text" : "password";
      toggleBtn.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
      toggleBtn.classList.toggle("active", isPassword);
    });
  }

  if (loginForm && submitBtn) {
    loginForm.addEventListener("submit", () => {
      if (!passwordInput.value || !document.getElementById("username")?.value.trim()) {
        return;
      }
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span>Verifying credentials...</span>`;
    });
  }
});
