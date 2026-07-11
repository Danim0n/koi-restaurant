/* ============================================================
   KOI · Interactividad de la web pública
   ============================================================ */
(function () {
    'use strict';

    // ---- Navbar: efecto al hacer scroll ----
    const navbar = document.getElementById('navbar');
    function actualizarNavbar() {
        if (!navbar) return;
        if (window.scrollY > 40) navbar.classList.add('is-scrolled');
        else navbar.classList.remove('is-scrolled');
    }
    window.addEventListener('scroll', actualizarNavbar, { passive: true });
    actualizarNavbar();

    // ---- Menú hamburguesa móvil ----
    const toggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    if (toggle && navMenu) {
        toggle.addEventListener('click', function () {
            toggle.classList.toggle('is-open');
            navMenu.classList.toggle('is-open');
        });
        // Cerrar al pulsar un enlace
        navMenu.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                toggle.classList.remove('is-open');
                navMenu.classList.remove('is-open');
            });
        });
    }

    // ---- Smooth scroll para anclas ----
    document.querySelectorAll('a[href^="/#"], a[href^="#"]').forEach(function (link) {
        link.addEventListener('click', function (e) {
            const hash = link.getAttribute('href').split('#')[1];
            const target = hash ? document.getElementById(hash) : null;
            if (target) {
                e.preventDefault();
                const y = target.getBoundingClientRect().top + window.scrollY - 70;
                window.scrollTo({ top: y, behavior: 'smooth' });
            }
        });
    });

    // ---- Animaciones de entrada (Intersection Observer) ----
    const reveals = document.querySelectorAll('.reveal');
    if ('IntersectionObserver' in window && reveals.length) {
        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });

        reveals.forEach(function (el) {
            // El hero se anima con su propia animación CSS
            if (!el.closest('.hero')) observer.observe(el);
        });
    } else {
        reveals.forEach(function (el) { el.classList.add('is-visible'); });
    }

    // ---- Año dinámico del footer ----
    const yearEl = document.getElementById('year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();
})();
