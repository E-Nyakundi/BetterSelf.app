/* ==========================================================================
   Site-wide micro-interactions
   Small, tasteful motion that makes the app feel alive without getting in
   the way: things settle into place as you scroll, numbers count up instead
   of just appearing, buttons ripple, and a job well done gets a tiny spark
   of celebration. Everything respects prefers-reduced-motion.
   ========================================================================== */
(function () {
    'use strict';

    var reduceMotion = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

    document.addEventListener('DOMContentLoaded', function () {

        // ---- Page entrance: the whole content area settles in on load ----
        var content = document.querySelector('.app-content-inner');
        if (content && !reduceMotion) {
            content.classList.add('page-enter');
            window.requestAnimationFrame(function () {
                content.classList.add('page-enter-active');
            });
        }

        // ---- Scroll reveal for cards, rows, and sections ----
        var revealSelectors = [
            '.bs-card', '.entry-card', '.inventory-stats section',
            '.bs-empty', '.capture-field', '.category-icon-grid li',
            '.inventory-table tbody tr'
        ];
        var revealEls = document.querySelectorAll(revealSelectors.join(','));

        if (reduceMotion || !('IntersectionObserver' in window)) {
            revealEls.forEach(function (el) { el.classList.add('is-visible'); });
        } else {
            revealEls.forEach(function (el) { el.classList.add('reveal-item'); });

            // Stagger siblings that reveal together (table rows, grid tiles, cards)
            var parentGroups = new Map();
            revealEls.forEach(function (el) {
                var p = el.parentElement;
                if (!parentGroups.has(p)) parentGroups.set(p, []);
                parentGroups.get(p).push(el);
            });
            parentGroups.forEach(function (siblings) {
                siblings.forEach(function (el, i) {
                    el.style.transitionDelay = Math.min(i * 45, 360) + 'ms';
                });
            });

            var observer = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('is-visible');
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

            revealEls.forEach(function (el) { observer.observe(el); });
        }

        // ---- Count-up numbers (dashboard stats) ----
        var counters = document.querySelectorAll('[data-count-up]');
        function animateCount(el) {
            var target = parseFloat(el.getAttribute('data-count-up'), 10);
            if (isNaN(target)) return;
            if (reduceMotion) { el.textContent = target; return; }
            var duration = 700;
            var start = null;
            function step(timestamp) {
                if (!start) start = timestamp;
                var progress = Math.min((timestamp - start) / duration, 1);
                var eased = 1 - Math.pow(1 - progress, 3);
                el.textContent = Math.round(target * eased);
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                } else {
                    el.textContent = target;
                }
            }
            window.requestAnimationFrame(step);
        }
        if (counters.length) {
            if ('IntersectionObserver' in window) {
                var countObserver = new IntersectionObserver(function (entries) {
                    entries.forEach(function (entry) {
                        if (entry.isIntersecting) {
                            animateCount(entry.target);
                            countObserver.unobserve(entry.target);
                        }
                    });
                }, { threshold: 0.3 });
                counters.forEach(function (el) { countObserver.observe(el); });
            } else {
                counters.forEach(animateCount);
            }
        }

        // ---- Ripple on buttons ----
        document.addEventListener('click', function (e) {
            var btn = e.target.closest && e.target.closest('.bs-btn, .capture-btn, .capture-shutter, .icon-tile');
            if (!btn || reduceMotion) return;
            var rect = btn.getBoundingClientRect();
            var ripple = document.createElement('span');
            ripple.className = 'ripple-effect';
            var size = Math.max(rect.width, rect.height) * 1.4;
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
            ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
            btn.appendChild(ripple);
            window.setTimeout(function () { ripple.remove(); }, 600);
        });

        // ---- Celebrate success toasts with a tiny confetti burst ----
        var successMsg = document.querySelector('.messages p.success');
        if (successMsg && !reduceMotion) {
            burstConfetti(successMsg);
        }

        function burstConfetti(anchor) {
            var rect = anchor.getBoundingClientRect();
            var colors = ['#C4582F', '#4D6A82', '#3F6B4F', '#B8923D', '#8B5E7A'];
            for (var i = 0; i < 14; i++) {
                var piece = document.createElement('span');
                piece.className = 'confetti-piece';
                piece.style.background = colors[i % colors.length];
                piece.style.left = (rect.left + rect.width * Math.random()) + 'px';
                piece.style.top = (rect.top + rect.height / 2) + 'px';
                var dx = (Math.random() - 0.5) * 160;
                var dy = -(60 + Math.random() * 80);
                piece.style.setProperty('--dx', dx + 'px');
                piece.style.setProperty('--dy', dy + 'px');
                piece.style.animationDelay = (Math.random() * 80) + 'ms';
                document.body.appendChild(piece);
                window.setTimeout(function (el) { return function () { el.remove(); }; }(piece), 1100);
            }
        }

        // ---- Category icon picker: animated selection ----
        document.querySelectorAll('.category-icon-grid').forEach(function (grid) {
            grid.addEventListener('click', function (e) {
                var tile = e.target.closest('.icon-tile');
                if (!tile) return;
                grid.querySelectorAll('.icon-tile').forEach(function (t) { t.classList.remove('just-selected'); });
                window.requestAnimationFrame(function () { tile.classList.add('just-selected'); });
            });
        });
    });
})();
