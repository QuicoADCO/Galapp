const token = localStorage.getItem('token');
if (!token) window.location.href = '/login';

function parseJwt(t) {
    try { return JSON.parse(atob(t.split('.')[1])); } catch { return {}; }
}

const pl       = parseJwt(token);
const username = pl.username || '?';
const role     = pl.role || 'usuario';

document.getElementById('avatar').textContent     = username[0].toUpperCase();
document.getElementById('sb-username').textContent = username;
document.getElementById('sb-role').textContent    = role;
document.getElementById('st-role').textContent    = role;

if (role === 'admin') {
    document.body.classList.add('admin-theme');
    document.querySelector('.sidebar-logo').innerHTML = 'Gal<span>app</span> · Admin';
    document.getElementById('topbar-title').textContent = 'Panel de Administración';
}

function authHdr() {
    return { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token };
}

// ── NOTIFICACIÓN ──
function toast(msg, type = 'success') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = 'toast show ' + type;
    setTimeout(() => { el.className = 'toast'; }, 3000);
}

// ── SECCIONES ──
function showSection(_name, btn) {
    document.getElementById('sec-surveys').style.display = '';
    document.getElementById('topbar-title').textContent  = 'Encuestas';
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}

// ── COMPARTIR ──
function compartirEncuesta(surveyId) {
    const url = `${window.location.origin}/encuesta/${surveyId}`;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(() => {
            toast('¡Enlace copiado al portapapeles!');
        }).catch(() => {
            toast(`Enlace: ${url}`, 'success');
        });
    } else {
        toast(`Enlace: /encuesta/${surveyId}`, 'success');
    }
}

// ── CARGAR ENCUESTAS ──
async function loadSurveys() {
    const res = await fetch('/api/surveys', { headers: authHdr() });
    if (res.status === 401) { localStorage.removeItem('token'); window.location.href = '/login'; return; }

    const surveys = await res.json();
    document.getElementById('st-surveys').textContent = surveys.length;

    const grid = document.getElementById('surveys-grid');

    if (surveys.length === 0) {
        grid.innerHTML = `
            <div class="empty">
                <div class="icon">📋</div>
                <h3>Aún no hay encuestas</h3>
                <p>Crea la primera con el botón de arriba</p>
            </div>`;
        document.getElementById('st-options').textContent = '0';
        return;
    }

    const cards = await Promise.all(surveys.map(buildCard));
    const total  = cards.reduce((s, c) => s + c.n, 0);
    document.getElementById('st-options').textContent = total;

    grid.innerHTML = '';
    cards.forEach(c => grid.appendChild(c.el));
}

async function buildCard(survey) {
    const detailRes  = await fetch(`/api/surveys/${survey.id}`, { headers: authHdr() });
    const detail     = await detailRes.json();
    const questions  = detail.questions || [];
    const imageUrl   = detail.survey.image_url || null;

    const votesRes = await fetch(`/api/surveys/${survey.id}/my-votes`, { headers: authHdr() });
    const myVotes  = votesRes.ok ? await votesRes.json() : [];

    const votedMap = {};
    for (const v of myVotes) {
        if (!votedMap[v.question_id]) votedMap[v.question_id] = new Set();
        votedMap[v.question_id].add(v.option_id);
    }

    let totalOpts = 0;
    for (const q of questions) totalOpts += q.options.length;

    const questionsHtml = questions.map(q => {
        const inputType    = q.type === 'multiple' ? 'checkbox' : 'radio';
        const alreadyVoted = votedMap[q.id] && votedMap[q.id].size > 0;

        const optionsHtml = q.options.map(o => {
            const checked  = votedMap[q.id] && votedMap[q.id].has(o.id);
            const disabled = alreadyVoted ? 'disabled' : '';
            return `
            <label class="vote-option${checked ? ' voted' : ''}${o.image_url ? ' has-image' : ''}">
                <input type="${inputType}" name="q${survey.id}_${q.id}" value="${o.id}" ${checked ? 'checked' : ''} ${disabled}>
                ${o.image_url ? `<img src="${esc(o.image_url)}" class="opt-img" alt="${esc(o.text)}" loading="lazy">` : ''}
                <span class="opt-label">${esc(o.text)}</span>
            </label>`;
        }).join('');

        const footer = alreadyVoted
            ? `<div class="voted-indicator"><span>✓</span> Votado</div>`
            : `<button type="button" class="btn btn-success btn-sm vote-btn"
                   data-survey-id="${survey.id}" data-question-id="${q.id}">
                   Votar
               </button>`;

        const typeLbl = q.type === 'single' ? 'Única' : 'Múltiple';

        return `
        <div class="question-block" data-qid="${q.id}">
            <div class="q-meta">
                <span class="q-num">P${q.order + 1}</span>
                <span class="q-type-badge ${q.type}">${typeLbl}</span>
            </div>
            <div class="q-text">${esc(q.text)}</div>
            <div class="q-options">${optionsHtml || '<p class="q-empty">Sin opciones todavía.</p>'}</div>
            <div class="q-footer">${footer}</div>
        </div>`;
    }).join('');

    const el = document.createElement('div');
    el.className = 'survey-card';
    el.innerHTML = `
        ${imageUrl ? `<div class="card-cover"><img src="${esc(imageUrl)}" alt="${esc(survey.title)}" loading="lazy"></div>` : ''}
        <div class="card-top-row">
            <div class="survey-tag">Encuesta #${survey.id}</div>
            <div class="card-actions">
                <button class="btn-results-survey" data-results-id="${survey.id}" title="Ver resultados en vivo">
                    📊 Resultados
                </button>
                <button class="btn-share-survey" data-share-id="${survey.id}" title="Copiar enlace para compartir">
                    🔗 Compartir
                </button>
            </div>
        </div>
        <div class="survey-title">${esc(survey.title)}</div>
        ${survey.description ? `<div class="survey-desc">${esc(survey.description)}</div>` : ''}
        <div class="survey-questions">
            ${questions.length === 0
                ? '<p style="font-size:13px;color:var(--muted)">Sin preguntas todavía.</p>'
                : questionsHtml}
        </div>`;

    el.addEventListener('click', e => {
        const resultsBtn = e.target.closest('.btn-results-survey');
        if (resultsBtn) { openResults(+resultsBtn.dataset.resultsId, esc(survey.title)); return; }

        const shareBtn = e.target.closest('.btn-share-survey');
        if (shareBtn) { compartirEncuesta(+shareBtn.dataset.shareId); return; }

        const voteBtn = e.target.closest('.vote-btn');
        if (voteBtn) submitVote(voteBtn);
    });

    return { el, n: totalOpts };
}

async function submitVote(btn) {
    const surveyId   = +btn.dataset.surveyId;
    const questionId = +btn.dataset.questionId;
    const qBlock     = btn.closest('.question-block');
    const inputs     = qBlock.querySelectorAll(`input[name="q${surveyId}_${questionId}"]`);
    const selected   = Array.from(inputs).filter(i => i.checked);

    if (selected.length === 0) {
        toast('Selecciona al menos una opción.', 'error');
        return;
    }

    btn.disabled = true;

    let allOk = true;
    for (const inp of selected) {
        const res = await fetch('/api/votes', {
            method:  'POST',
            headers: authHdr(),
            body:    JSON.stringify({ question_id: questionId, option_id: +inp.value }),
        });
        if (!res.ok) {
            const d = await res.json();
            toast(d.error || 'Error al votar', 'error');
            allOk = false;
            break;
        }
    }

    if (allOk) {
        inputs.forEach(i => i.disabled = true);
        selected.forEach(i => i.closest('.vote-option').classList.add('voted'));
        qBlock.querySelector('.q-footer').innerHTML =
            `<div class="voted-indicator"><span>✓</span> Votado</div>`;
        toast('¡Voto registrado!');
    } else {
        btn.disabled = false;
    }
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}

// ── RESULTADOS ──
let _resultsTimer = null;

async function openResults(surveyId, surveyTitle) {
    const overlay = document.getElementById('results-overlay');
    document.getElementById('results-title').textContent = surveyTitle;
    overlay.classList.add('open');
    overlay.dataset.surveyId = surveyId;

    await refreshResults(surveyId);

    _resultsTimer = setInterval(() => refreshResults(surveyId), 5000);
}

function closeResults() {
    clearInterval(_resultsTimer);
    _resultsTimer = null;
    document.getElementById('results-overlay').classList.remove('open');
    document.getElementById('results-overlay').dataset.surveyId = '';
}

async function refreshResults(surveyId) {
    const res = await fetch(`/api/surveys/${surveyId}/results`, { headers: authHdr() });
    if (res.status === 401) { localStorage.removeItem('token'); window.location.href = '/login'; return; }
    if (!res.ok) { return; }

    const data = await res.json();
    const body = document.getElementById('results-body');

    if (!data.questions || data.questions.length === 0) {
        body.innerHTML = '<p class="r-empty">Esta encuesta aún no tiene preguntas.</p>';
        return;
    }

    body.innerHTML = data.questions.map((q, qi) => {
        const total = q.total_votes;
        const optionsHtml = q.options.map(o => {
            const pct  = o.percentage;
            const isWinner = total > 0 && o.votes === Math.max(...q.options.map(x => x.votes));
            return `
            <div class="r-option${isWinner && total > 0 ? ' r-winner' : ''}">
                <div class="r-opt-top">
                    ${o.image_url
                        ? `<img src="${esc(o.image_url)}" class="r-opt-img" alt="${esc(o.text)}" loading="lazy">`
                        : ''}
                    <span class="r-opt-label">${esc(o.text)}</span>
                    <span class="r-opt-pct">${pct}%</span>
                </div>
                <div class="r-bar-track">
                    <div class="r-bar-fill" style="width:${pct}%"></div>
                </div>
                <div class="r-opt-votes">${o.votes} ${o.votes === 1 ? 'voto' : 'votos'}</div>
            </div>`;
        }).join('');

        return `
        <div class="r-question">
            <div class="r-q-header">
                <span class="q-num">P${qi + 1}</span>
                <span class="r-q-text">${esc(q.text)}</span>
                <span class="r-total">${total} ${total === 1 ? 'voto' : 'votos'}</span>
            </div>
            <div class="r-options">${optionsHtml}</div>
        </div>`;
    }).join('');
}

function esc(s) {
    return String(s)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;')
        .replace(/'/g,'&#x27;');
}

// ── RESULTADOS: cerrar con botón y con clic en el fondo ──
document.getElementById('results-close-btn').addEventListener('click', closeResults);
document.getElementById('results-overlay').addEventListener('click', function(e) {
    if (e.target === this) closeResults();
});

loadSurveys();
