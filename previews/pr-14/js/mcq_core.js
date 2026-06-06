/* js/mcq_core.js */

let QUESTIONS = [];
let RD = {};
let S = {
    chosen: [],
    checked: [],
    skipped: [],
    score: 0, ok: 0, bad: 0, skip: 0
};


window.addEventListener('DOMContentLoaded', function() {
    const qDataEl = document.getElementById('qdata');
    const rdDataEl = document.getElementById('rddata');
    
    try {
        if (qDataEl && qDataEl.textContent.trim()) {
            QUESTIONS = JSON.parse(qDataEl.textContent);
        }
        if (rdDataEl && rdDataEl.textContent.trim()) {
            RD = JSON.parse(rdDataEl.textContent);
        }
    } catch (e) {
        console.error("MCQ Core: Failed to parse JSON data. Ensure #qdata and #rddata contain valid JSON.", e);
    }
    
    if (QUESTIONS.length > 0) {
        S.chosen = new Array(QUESTIONS.length).fill(null);
        S.checked = new Array(QUESTIONS.length).fill(false);
        S.skipped = new Array(QUESTIONS.length).fill(false);
    }
    
    buildDots();
    buildCards();
});

function buildDots() {
    let h = '';
    for (let i = 0; i < QUESTIONS.length; i++) {
        h += `<button class="dot" id="dot-${i}" data-qi="${i}">${i + 1}</button>`;
    }
    const dw = document.getElementById('dots-wrap');
    if (!dw) return;
    dw.innerHTML = h;
    dw.addEventListener('click', function(e) {
        const b = e.target.closest('.dot');
        if (b) {
            const el = document.getElementById('card-' + b.getAttribute('data-qi'));
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
}

function updateDot(qi) {
    const d = document.getElementById('dot-' + qi);
    if (!d) return;
    d.className = 'dot';
    if (S.skipped[qi]) { d.classList.add('d-skip'); return; }
    if (!S.checked[qi]) return;
    d.classList.add(S.chosen[qi] === QUESTIONS[qi].correct ? 'd-ok' : 'd-bad');
}

function buildCards() {
    let h = '';
    for (let i = 0; i < QUESTIONS.length; i++) h += cardHTML(QUESTIONS[i], i);
    const qw = document.getElementById('quiz-wrap');
    if (!qw) return;
    qw.innerHTML = h;
    qw.addEventListener('click', function(e) {
        let b;
        b = e.target.closest('.opt');
        if (b && !b.classList.contains('locked')) {
            pick(parseInt(b.getAttribute('data-qi')), b.getAttribute('data-lbl')); return;
        }
        b = e.target.closest('.btn-check');
        if (b && !b.disabled) { checkQ(parseInt(b.getAttribute('data-qi'))); return; }
        b = e.target.closest('.btn-skip');
        if (b) { skipQ(parseInt(b.getAttribute('data-qi'))); }
    });
}

function cardHTML(q, i) {
    let oh = '';
    for (let j = 0; j < q.options.length; j++) {
        const o = q.options[j];
        oh += `<button class="opt" id="opt-${i}-${o.label}" data-qi="${i}" data-lbl="${o.label}">
                <span class="opt-lt">${o.label}</span>
                <span>${xe(o.text)}</span>
               </button>`;
    }
    return `<div class="card" id="card-${i}">
        <div class="q-hdr"><div class="q-num">${i + 1}</div>
        <div class="q-tags"><div class="q-sub">${xe(q.subtopic)}</div>
        <div class="q-diff">${q.difficulty}</div></div></div>
        <div class="q-stem">${q.stem}</div>
        <div class="options">${oh}</div>
        <div class="action-row">
            <button class="btn btn-check" id="chk-${i}" data-qi="${i}" disabled>Check Answer</button>
            <button class="btn btn-skip" id="skp-${i}" data-qi="${i}">Skip</button>
        </div><div id="exp-${i}"></div></div>`;
}

function pick(qi, lbl) {
    if (S.checked[qi] || S.skipped[qi]) return;
    S.chosen[qi] = lbl;
    const opts = QUESTIONS[qi].options;
    for (let j = 0; j < opts.length; j++) {
        const b = document.getElementById(`opt-${qi}-${opts[j].label}`);
        if (opts[j].label === lbl) b.classList.add('sel'); else b.classList.remove('sel');
    }
    const chkBtn = document.getElementById('chk-' + qi);
    if (chkBtn) chkBtn.disabled = false;
}

function checkQ(qi) {
    if (S.checked[qi]) return;
    S.checked[qi] = true;
    const q = QUESTIONS[qi];
    const ch = S.chosen[qi];
    const ok = (ch === q.correct);
    if (ok) { S.score += 1; S.ok++; } else { S.score -= 0.25; S.bad++; }
    for (let j = 0; j < q.options.length; j++) {
        const b = document.getElementById(`opt-${qi}-${q.options[j].label}`);
        b.classList.add('locked'); b.classList.remove('sel');
        if (q.options[j].label === q.correct) b.classList.add('c-ok');
        else if (q.options[j].label === ch && !ok) b.classList.add('c-bad');
        else b.classList.add('c-dim');
    }
    document.getElementById('chk-' + qi).style.display = 'none';
    document.getElementById('skp-' + qi).style.display = 'none';
    renderExp(qi, ch, ok, q); bar(); updateDot(qi);
}

function skipQ(qi) {
    if (S.checked[qi] || S.skipped[qi]) return;
    S.skipped[qi] = true; S.skip++;
    const opts = QUESTIONS[qi].options;
    for (let j = 0; j < opts.length; j++)
        document.getElementById(`opt-${qi}-${opts[j].label}`).classList.add('locked', 'c-dim');
    document.getElementById('chk-' + qi).style.display = 'none';
    document.getElementById('skp-' + qi).style.display = 'none';
    bar(); updateDot(qi);
    document.getElementById('exp-' + qi).innerHTML =
        `<div class="exp-wrap"><div class="exp-hdr">
        <span class="exp-verdict">— Skipped · No mark</span>
        <span class="exp-delta d-zero">0</span></div>
        <div class="exp-body" style="padding:12px 18px;"><p style="font-size:.88rem;color:var(--ink-muted);font-style:italic;">
        Correct answer: <strong style="color:var(--gold)">${xe(QUESTIONS[qi].correct)}</strong></p></div></div>`;
}

function renderExp(qi, ch, ok, q) {
    const verdict = ok ? '✓ Correct — +1 mark' : '✗ Incorrect — Correct answer: ' + q.correct;
    const dt = ok ? '+1' : '−0.25', dc = ok ? 'd-pos' : 'd-neg';
    let oh = '';
    for (let j = 0; j < q.options.length; j++) {
        const o = q.options[j];
        const isCor = (o.label === q.correct), isWrg = (o.label === ch && !isCor);
        const cls = isCor ? 'oe oe-ok' : (isWrg ? 'oe oe-bad' : 'oe');
        const ico = isCor ? '✓' : (isWrg ? '✗' : '·');
        oh += `<div class="${cls}"><div class="oe-lbl"><span class="oe-ltr">${ico} ${o.label}.</span> 
                ${xe(o.text)}</div><div style="margin-top:3px">${xe(o.explanation)}</div></div>`;
}
    document.getElementById('exp-' + qi).innerHTML =
        `<div class="exp-wrap"><div class="exp-hdr">
        <span class="exp-verdict">${verdict}</span>
        <span class="exp-delta ${dc}">${dt}</span></div>
        <div class="exp-body"><div class="opt-exps">${oh}</div>
        <div class="insight-row">
        <div class="insight i-top"><div class="ins-title">★ Topper's Rule</div>
        <div class="ins-text">${xe(q.topperRule)}</div></div>
        <div class="insight i-err"><div class="ins-title">⚠ Common Mistake</div>
        <div class="ins-text">${xe(q.commonMistake)}</div></div>
        </div></div></div>`;
}

function bar() {
    const scoreEl = document.getElementById('lv-s');
    const okEl = document.getElementById('lv-ok');
    const badEl = document.getElementById('lv-bad');
    const skEl = document.getElementById('lv-sk');
    if (scoreEl) scoreEl.textContent = S.score.toFixed(2);
    if (okEl) okEl.textContent = S.ok;
    if (badEl) badEl.textContent = S.bad;
    if (skEl) skEl.textContent = S.skip;
}

function finishTest() {
    for (let i = 0; i < QUESTIONS.length; i++) if (!S.checked[i] && !S.skipped[i]) skipQ(i);
    document.getElementById('quiz-wrap').style.display = 'none';
    document.getElementById('dots-wrap').style.display = 'none';
    const finishWrap = document.querySelector('.finish-wrap');
    if (finishWrap) finishWrap.style.display = 'none';
    const res = document.getElementById('results');
    if (!res) return;
    res.style.display = 'block';
    res.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const pct = (S.score / QUESTIONS.length) * 100;
    let grade, lbl;
    if (pct >= 90) { grade = 'A+'; lbl = 'Outstanding — Examiner Standard'; }
    else if (pct >= 75) { grade = 'A'; lbl = 'Excellent — Well Prepared'; }
    else if (pct >= 60) { grade = 'B'; lbl = 'Good — Minor Gaps to Address'; }
    else if (pct >= 40) { grade = 'C'; lbl = 'Average — Focused Revision Required'; }
    else if (pct >= 20) { grade = 'D'; lbl = 'Below Average — Revise Fundamentals'; }
    else { grade = 'F'; lbl = 'Needs Comprehensive Revision'; }
    document.getElementById('r-grade').textContent = grade;
    document.getElementById('r-lbl').textContent = lbl;
    document.getElementById('r-sc').textContent = S.score.toFixed(2);
    document.getElementById('r-ok').textContent = S.ok;
    document.getElementById('r-bad').textContent = S.bad;
    document.getElementById('r-skip').textContent = S.skip;
    buildBars(); buildRoadmap();
}

function buildBars() {
    const map = {};
    for (let i = 0; i < QUESTIONS.length; i++) {
        const st = QUESTIONS[i].subtopic;
        if (!map[st]) map[st] = { total: 0, correct: 0 };
        map[st].total++;
        if (S.checked[i] && S.chosen[i] === QUESTIONS[i].correct) map[st].correct++;
    }
    window._stMap = map;
    const keys = Object.keys(map);
    let h = '';
    for (let k = 0; k < keys.length; k++) {
        const nm = keys[k], d = map[nm];
        const p = d.total ? Math.round((d.correct / d.total) * 100) : 0;
        const fc = p >= 70 ? 'f-hi' : p >= 40 ? 'f-mid' : 'f-lo';
        h += `<div><div class="st-top"><span class="st-nm">${xe(nm)}</span>
             <span class="st-sc">${d.correct}/${d.total} (${p}%)</span></div>
             <div class="st-track"><div class="st-fill ${fc}" style="width:0%" data-t="${p}"></div></div></div>`;
    }
    const barsEl = document.getElementById('st-bars');
    if (barsEl) barsEl.innerHTML = h;
    setTimeout(function() {
        const els = document.querySelectorAll('.st-fill[data-t]');
        els.forEach(el => el.style.width = el.getAttribute('data-t') + '%');
    }, 120);
}

function buildRoadmap() {
    const map = window._stMap || {};
    const keys = Object.keys(map).sort(function(a, b) {
        const pa = map[a].total ? map[a].correct / map[a].total : 0;
        const pb = map[b].total ? map[b].correct / map[b].total : 0;
        return pa - pb;
    });
    let h = '';
    for (let k = 0; k < keys.length; k++) {
        const nm = keys[k], d = map[nm];
        const p = d.total ? d.correct / d.total : 0;
        const pri = p < 0.5 ? 'High' : p < 0.75 ? 'Medium' : 'Low';
        const pc = pri === 'High' ? 'rp-hi' : pri === 'Medium' ? 'rp-mid' : 'rp-lo';
        const bc = pri === 'High' ? 'bh' : pri === 'Medium' ? 'bm' : 'bl';
        const rd = RD[nm] || { w: '—', tips: [], traps: [] };
        let tips = '', traps = '';
        for (let t = 0; t < rd.tips.length; t++) tips += `<li>${xe(rd.tips[t])}</li>`;
        for (let t = 0; t < rd.traps.length; t++) traps += `<li>${xe(rd.traps[t])}</li>`;
        h += `<div class="rm ${pc}">
             <div class="rm-top">${xe(nm)}<span class="rm-badge ${bc}">${pri} Priority</span></div>
             <div class="rm-w">Exam Weight: ${xe(rd.w)}</div>
             <div class="rm-grid">
             <div><div class="rm-ct">Study Tips</div><ul class="rm-list">${tips}</ul></div>
             <div><div class="rm-ct">Examiner Traps</div><ul class="rm-list">${traps}</ul></div>
             </div></div>`;
    }
    const roadmapEl = document.getElementById('roadmap');
    if (roadmapEl) roadmapEl.innerHTML = h;
}

function xe(s) {
    if (typeof s !== 'string') return '';
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}