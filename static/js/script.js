/* ========================================
   ATM Management System – script.js
   ======================================== */

document.addEventListener('DOMContentLoaded', function () {

  // ── SIDEBAR TOGGLE ──────────────────────────────────────
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar       = document.getElementById('sidebar');
  const mainWrapper   = document.getElementById('mainWrapper');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle('open');
      } else {
        document.body.classList.toggle('sidebar-collapsed');
      }
    });

    // Close sidebar on outside click (mobile)
    document.addEventListener('click', function (e) {
      if (window.innerWidth <= 768 &&
          sidebar.classList.contains('open') &&
          !sidebar.contains(e.target) &&
          e.target !== sidebarToggle) {
        sidebar.classList.remove('open');
      }
    });
  }

  // ── TOPBAR CLOCK ────────────────────────────────────────
  const timeEl = document.getElementById('topbarTime');
  if (timeEl) {
    function updateClock() {
      const now = new Date();
      timeEl.textContent = now.toLocaleTimeString('en-IN', {
        hour: '2-digit', minute: '2-digit', second: '2-digit'
      });
    }
    updateClock();
    setInterval(updateClock, 1000);
  }

  // ── AUTO-DISMISS FLASH MESSAGES ─────────────────────────
  const alerts = document.querySelectorAll('.alert-custom');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });

  // ── ACTIVE NAV HIGHLIGHT ────────────────────────────────
  const navItems = document.querySelectorAll('.nav-item');
  const currentPath = window.location.pathname;
  navItems.forEach(function (item) {
    if (item.getAttribute('href') === currentPath) {
      item.classList.add('active');
    }
  });

  // ── FORM VALIDATION: Register ───────────────────────────
  const registerForm = document.querySelector('form[action*="register"]');
  if (registerForm) {
    registerForm.addEventListener('submit', function (e) {
      const pw  = document.querySelector('input[name="password"]');
      const cpw = document.querySelector('input[name="confirm_password"]');
      const mob = document.querySelector('input[name="mobile"]');

      if (pw && cpw && pw.value !== cpw.value) {
        e.preventDefault();
        showInlineError(cpw, 'Passwords do not match.');
        return;
      }
      if (mob && !/^\d{10}$/.test(mob.value)) {
        e.preventDefault();
        showInlineError(mob, 'Enter a valid 10-digit mobile number.');
        return;
      }
      if (pw && pw.value.length < 6) {
        e.preventDefault();
        showInlineError(pw, 'Password must be at least 6 characters.');
      }
    });
  }

  // ── NUMERIC INPUTS: prevent negatives ───────────────────
  document.querySelectorAll('input[type="number"]').forEach(function (inp) {
    inp.addEventListener('keydown', function (e) {
      if (e.key === '-' || e.key === 'e') e.preventDefault();
    });
  });

  // ── MOBILE INPUT: digits only ───────────────────────────
  document.querySelectorAll('input[name="mobile"]').forEach(function (inp) {
    inp.addEventListener('input', function () {
      this.value = this.value.replace(/\D/g, '').slice(0, 10);
    });
  });

  // ── INPUT FOCUS ANIMATIONS ──────────────────────────────
  document.querySelectorAll('.input-custom').forEach(function (inp) {
    inp.addEventListener('focus', function () {
      this.closest('.input-icon-wrap')?.classList.add('focused');
    });
    inp.addEventListener('blur', function () {
      this.closest('.input-icon-wrap')?.classList.remove('focused');
    });
  });

  // ── CARD HOVER RIPPLE ───────────────────────────────────
  document.querySelectorAll('.action-card, .stat-card, .feature-card').forEach(function (card) {
    card.addEventListener('click', function (e) {
      const ripple = document.createElement('span');
      const rect   = card.getBoundingClientRect();
      const size   = Math.max(rect.width, rect.height);
      ripple.style.cssText = `
        position:absolute;width:${size}px;height:${size}px;
        border-radius:50%;background:rgba(255,255,255,0.08);
        left:${e.clientX - rect.left - size/2}px;
        top:${e.clientY - rect.top - size/2}px;
        transform:scale(0);animation:rippleAnim 0.5s ease;
        pointer-events:none;z-index:10;
      `;
      card.style.position = 'relative';
      card.style.overflow = 'hidden';
      card.appendChild(ripple);
      ripple.addEventListener('animationend', () => ripple.remove());
    });
  });

  // ── TABLE ROW HOVER EFFECT ──────────────────────────────
  document.querySelectorAll('.txn-row').forEach(function (row) {
    row.addEventListener('mouseenter', function () {
      this.style.transform = 'scale(1.002)';
    });
    row.addEventListener('mouseleave', function () {
      this.style.transform = '';
    });
  });

  // ── AMOUNT FORMATTING DISPLAY ───────────────────────────
  function formatINR(num) {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency', currency: 'INR', minimumFractionDigits: 2
    }).format(num);
  }

  // ── CONFIRM DIALOGS ─────────────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(this.dataset.confirm)) e.preventDefault();
    });
  });

  // ── COPY ACCOUNT NUMBER ─────────────────────────────────
  document.querySelectorAll('.copy-acc').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const text = this.dataset.acc;
      navigator.clipboard.writeText(text).then(() => {
        const original = this.innerHTML;
        this.innerHTML = '<i class="fas fa-check"></i>';
        setTimeout(() => { this.innerHTML = original; }, 1500);
      });
    });
  });

  // ── SCROLL REVEAL ───────────────────────────────────────
  const revealEls = document.querySelectorAll(
    '.stat-card, .action-card, .feature-card, .transaction-card, .profile-card'
  );
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.style.animation = 'fadeInUp 0.4s ease forwards';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    revealEls.forEach(el => observer.observe(el));
  }

  // ── HELPER: show inline error ────────────────────────────
  function showInlineError(inputEl, message) {
    const existing = inputEl.parentElement.parentElement.querySelector('.inline-error');
    if (existing) existing.remove();
    const err = document.createElement('div');
    err.className = 'inline-error';
    err.style.cssText = 'color:#f5576c;font-size:0.78rem;margin-top:0.35rem;display:flex;align-items:center;gap:0.3rem';
    err.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    inputEl.parentElement.parentElement.appendChild(err);
    inputEl.focus();
    setTimeout(() => err.remove(), 4000);
  }

  // ── INJECT RIPPLE KEYFRAMES ──────────────────────────────
  if (!document.getElementById('rippleStyle')) {
    const style = document.createElement('style');
    style.id = 'rippleStyle';
    style.textContent = `
      @keyframes rippleAnim {
        to { transform:scale(2.5); opacity:0; }
      }
      @keyframes fadeInUp {
        from { opacity:0; transform:translateY(16px); }
        to   { opacity:1; transform:translateY(0); }
      }
      .input-icon-wrap.focused > i:first-child { color: var(--accent) !important; }
    `;
    document.head.appendChild(style);
  }

  // ── LANDING PAGE: smooth scroll ──────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // ── BALANCE PAGE: count-up animation ─────────────────────
  const balanceAmountEl = document.querySelector('.balance-amount');
  if (balanceAmountEl) {
    const raw = balanceAmountEl.textContent.replace(/[₹,]/g, '').trim();
    const target = parseFloat(raw) || 0;
    let current = 0;
    const duration = 1000;
    const step = target / (duration / 16);
    const timer = setInterval(function () {
      current = Math.min(current + step, target);
      balanceAmountEl.textContent = '₹' + current.toLocaleString('en-IN', { minimumFractionDigits: 2 });
      if (current >= target) clearInterval(timer);
    }, 16);
  }

  // ── STAT CARD COUNT-UP ────────────────────────────────────
  document.querySelectorAll('.stat-value').forEach(function (el) {
    const text = el.textContent.trim();
    // Only animate plain integers
    if (/^\d+$/.test(text)) {
      const target = parseInt(text, 10);
      let current = 0;
      const step = Math.ceil(target / 40) || 1;
      const timer = setInterval(function () {
        current = Math.min(current + step, target);
        el.textContent = current.toLocaleString('en-IN');
        if (current >= target) clearInterval(timer);
      }, 25);
    }
  });

  // ── TRANSFER: enable submit only when receiver valid ──────
  const submitBtn = document.getElementById('submitBtn');
  const receiverInput = document.getElementById('receiverAcc');
  const amountInput   = document.getElementById('transferAmount');
  if (submitBtn && receiverInput && amountInput) {
    function checkTransferReady() {
      // submitBtn enabling is handled in inline script; this is a fallback
    }
    amountInput.addEventListener('input', checkTransferReady);
  }

  // ── HISTORY: highlight search term ───────────────────────
  const searchInput = document.querySelector('.filter-input');
  if (searchInput && searchInput.value) {
    const term = searchInput.value.toLowerCase();
    document.querySelectorAll('.txn-table tbody td').forEach(function (td) {
      if (td.textContent.toLowerCase().includes(term)) {
        const re = new RegExp(`(${term})`, 'gi');
        td.innerHTML = td.innerHTML.replace(re, '<mark style="background:rgba(124,131,253,0.3);color:white;border-radius:2px;padding:0 2px">$1</mark>');
      }
    });
  }

  // ── TOOLTIP INIT ─────────────────────────────────────────
  document.querySelectorAll('[title]').forEach(function (el) {
    el.setAttribute('data-tooltip', el.getAttribute('title'));
    el.removeAttribute('title');
  });

});
