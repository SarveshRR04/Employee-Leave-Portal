
const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("overlay");
const menuBtn = document.getElementById("menu-btn");

function toggleSidebar() {
  sidebar.classList.toggle("open");
  overlay.classList.toggle("show");
}
if (menuBtn) {
  menuBtn.addEventListener("click", toggleSidebar);
  overlay.addEventListener("click", toggleSidebar);
}


document.querySelectorAll(".alert:not(.alert-static)").forEach(function (alert) {
  alert.querySelector(".alert-close").addEventListener("click", function () {
    alert.remove();
  });
  setTimeout(function () { alert.remove(); }, 5000);
});

const modal = document.getElementById("reject-modal");
if (modal) {
  const form = document.getElementById("reject-form");
  const who = document.getElementById("reject-employee");

  document.querySelectorAll("[data-reject-url]").forEach(function (button) {
    button.addEventListener("click", function () {
      form.action = button.dataset.rejectUrl;   
      who.textContent = button.dataset.employee;
      modal.classList.add("open");
      form.querySelector("textarea").focus();
    });
  });

  document.querySelectorAll("[data-close-modal]").forEach(function (button) {
    button.addEventListener("click", function () { modal.classList.remove("open"); });
  });
}


const badge = document.getElementById("pending-badge");
if (badge) {
  setInterval(function () {
    fetch(badge.dataset.url)
      .then(function (response) { return response.json(); })
      .then(function (data) {
        badge.textContent = data.pending;
        badge.classList.toggle("hidden", data.pending === 0);
      })
      .catch(function () { /* ignore network errors, try again next time */ });
  }, 15000);
}
