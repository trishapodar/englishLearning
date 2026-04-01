/* js/guide_core.js */

let isScrolling = false;
window.addEventListener('scroll', function() {
    if (isScrolling) return;
    isScrolling = true;
    requestAnimationFrame(() => {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    
    const progressFill = document.getElementById('progress-fill');
    if (progressFill) progressFill.style.width = pct + '%';
    
    const btt = document.getElementById('btt');
    if (btt) {
        if (scrollTop > 400) btt.classList.add('visible');
        else btt.classList.remove('visible');
    }
    updateActiveSidebar();
        isScrolling = false;
    });
});

function updateActiveSidebar() {
    const sections = Array.from(document.querySelectorAll('section.topic-section'));
    const scrollTop = window.pageYOffset + 100;
    let activeId = sections.length > 0 ? sections[0].id : '';

    for (let i = 0; i < sections.length; i++) {
        if (sections[i].offsetTop <= scrollTop) {
            activeId = sections[i].id;
        }
    }

    const items = document.querySelectorAll('.sid-item');
    items.forEach(item => {
        const onclick = item.getAttribute('onclick') || '';
        if (onclick.includes(`'${activeId}'`)) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

function goTo(id) {
    const el = document.getElementById(id);
    if (!el) return;
    const top = el.getBoundingClientRect().top + window.pageYOffset - 72;
    window.scrollTo({ top: top, behavior: 'smooth' });
    if (window.innerWidth <= 860) {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.remove('open');
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('open');
}

document.addEventListener('click', function(e) {
    if (window.innerWidth > 860) return;
    const sb = document.getElementById('sidebar');
    const btn = document.getElementById('menu-toggle');
    if (sb && !sb.contains(e.target) && e.target !== btn) {
        sb.classList.remove('open');
    }
});

/* Staggered Section Animations */
if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08 });

    document.querySelectorAll('.topic-section').forEach((el) => {
        el.style.animationPlayState = 'paused';
        observer.observe(el);
    });
}