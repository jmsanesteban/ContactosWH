'use strict';

// ── Sidebar toggle ──────────────────────────────────────────────────────
const sidebar   = document.getElementById('sidebar');
const openBtn   = document.getElementById('sidebarOpen');
const closeBtn  = document.getElementById('sidebarClose');
const overlay   = document.getElementById('sidebarOverlay');

function openSidebar()  { sidebar && sidebar.classList.add('open'); overlay && overlay.classList.add('visible'); }
function closeSidebar() { sidebar && sidebar.classList.remove('open'); overlay && overlay.classList.remove('visible'); }

openBtn  && openBtn.addEventListener('click', openSidebar);
closeBtn && closeBtn.addEventListener('click', closeSidebar);
overlay  && overlay.addEventListener('click', closeSidebar);

// ── CSRF token helper ───────────────────────────────────────────────────
function getCsrfToken() {
  const el = document.querySelector('meta[name="csrf-token"]') ||
             document.querySelector('input[name="csrf_token"]');
  return el ? (el.getAttribute('content') || el.value) : '';
}

// ── Auto-dismiss alerts ─────────────────────────────────────────────────
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    alert.style.transition = 'opacity .4s';
    alert.style.opacity = '0';
    setTimeout(() => alert.remove(), 400);
  }, 6000);
});

// ── Confirm on data-confirm elements ───────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', e => {
    if (!confirm(el.dataset.confirm)) e.preventDefault();
  });
});
