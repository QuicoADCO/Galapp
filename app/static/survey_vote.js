// Obtener el ID de la encuesta desde la URL  (/encuesta/5 → 5)
const surveyId = parseInt(window.location.pathname.split('/').pop(), 10);
const token    = localStorage.getItem('token');

if (!token) {
    // Redirigir al login guardando la página actual como destino
    window.location.href = `/login?siguiente=/encuesta/${surveyId}`;
}

function authHdr() {
    return { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token };
}

// ── NOTIFICACIÓN ──
function toast(msg, type = 'success') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = 'toast show ' + type;
    setTimeout(() => { el.className = 'toast'; }, 3500);
}

function esc(s) {
    return String(s)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;')
        .replace(/'/g,'&#x27;');
}

// ── CABECERA ──
function renderHeader() {
    const actionsEl = document.getElementById('header-actions');
    if (token) {
        try {
            const pl = JSON.parse(atob(token.split('.')[1]));
            actionsEl.innerHTML = `
                <span class="header-user">👤 ${esc(pl.username || '')}</span>
                <a href="/dashboard" class="btn-header">Panel</a>
                <button class="btn-header btn-header-outline" id="btn-logout-hdr">Salir</button>`;
            document.getElementById('btn-logout-hdr').addEventListener('click', () => {
                localStorage.removeItem('token');
                window.location.href = '/login';
            });
        } catch { /* token malformado */ }
    } else {
        actionsEl.innerHTML = `<a href="/login?siguiente=/encuesta/${surveyId}" class="btn-header">Iniciar sesión</a>`;
    }
}

// ── CARGAR Y RENDERIZAR ENCUESTA ──
async function cargarEncuesta() {
    renderHeader();

    const container = document.getElementById('vote-container');

    // Datos de la encuesta
    const res = await fetch(`/api/surveys/${surveyId}`, { headers: authHdr() });
    if (res.status === 401) {
        window.location.href = `/login?siguiente=/encuesta/${surveyId}`;
        return;
    }
    if (!res.ok) {
        container.innerHTML = `
            <div class="error-state">
                <div class="error-icon">❌</div>
                <h2>Encuesta no encontrada</h2>
                <p>Es posible que haya sido eliminada o el enlace sea incorrecto.</p>
                <a href="/dashboard" class="btn-primary-lg">Ir al panel</a>
            </div>`;
        return;
    }

    const data      = await res.json();
    const survey    = data.survey;
    const questions = data.questions || [];

    // Votos previos del usuario
    const votesRes = await fetch(`/api/surveys/${surveyId}/my-votes`, { headers: authHdr() });
    const myVotes  = votesRes.ok ? await votesRes.json() : [];

    const votedMap = {};
    for (const v of myVotes) {
        if (!votedMap[v.question_id]) votedMap[v.question_id] = new Set();
        votedMap[v.question_id].add(v.option_id);
    }

    // ── HTML de la encuesta ──
    const coverHtml = survey.image_url
        ? `<div class="sv-cover"><img src="${esc(survey.image_url)}" alt="${esc(survey.title)}" loading="lazy"></div>`
        : '';

    const questionsHtml = questions.map((q, idx) => {
        const inputType    = q.type === 'multiple' ? 'checkbox' : 'radio';
        const alreadyVoted = votedMap[q.id] && votedMap[q.id].size > 0;
        const typeLbl      = q.type === 'single' ? 'Única' : 'Múltiple';

        const optionsHtml = q.options.map(o => {
            const checked  = votedMap[q.id] && votedMap[q.id].has(o.id);
            const disabled = alreadyVoted ? 'disabled' : '';
            return `
            <label class="sv-option${checked ? ' voted' : ''}${o.image_url ? ' has-image' : ''}">
                <input type="${inputType}" name="svq_${q.id}" value="${o.id}" ${checked ? 'checked' : ''} ${disabled}>
                ${o.image_url ? `<img src="${esc(o.image_url)}" class="sv-opt-img" alt="${esc(o.text)}" loading="lazy">` : ''}
                <span class="sv-opt-label">${esc(o.text)}</span>
            </label>`;
        }).join('');

        const footer = alreadyVoted
            ? `<div class="sv-voted-badge"><span>✓</span> Ya votaste</div>`
            : `<button type="button" class="sv-vote-btn" data-qid="${q.id}">Votar esta pregunta</button>`;

        return `
        <div class="sv-question" data-qid="${q.id}" data-idx="${idx}">
            <div class="sv-q-meta">
                <span class="sv-q-num">Pregunta ${idx + 1}</span>
                <span class="sv-q-type ${q.type}">${typeLbl}</span>
            </div>
            <div class="sv-q-text">${esc(q.text)}</div>
            <div class="sv-options">${optionsHtml}</div>
            <div class="sv-q-footer">${footer}</div>
        </div>`;
    }).join('');

    container.innerHTML = `
        ${coverHtml}
        <div class="sv-header">
            <h1 class="sv-title">${esc(survey.title)}</h1>
            ${survey.description ? `<p class="sv-desc">${esc(survey.description)}</p>` : ''}
        </div>
        <div class="sv-questions">${questionsHtml || '<p class="sv-empty">Esta encuesta aún no tiene preguntas.</p>'}</div>
        <div class="sv-bottom">
            <a href="/dashboard" class="sv-link">← Volver al panel</a>
        </div>`;

    // Event delegation para los botones de voto
    container.addEventListener('click', e => {
        const btn = e.target.closest('.sv-vote-btn');
        if (btn) enviarVoto(btn);
    });
}

async function enviarVoto(btn) {
    const questionId = +btn.dataset.qid;
    const qBlock     = btn.closest('.sv-question');
    const inputs     = qBlock.querySelectorAll(`input[name="svq_${questionId}"]`);
    const selected   = Array.from(inputs).filter(i => i.checked);

    if (selected.length === 0) {
        toast('Selecciona al menos una opción.', 'error');
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Enviando…';

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
        selected.forEach(i => i.closest('.sv-option').classList.add('voted'));
        qBlock.querySelector('.sv-q-footer').innerHTML =
            `<div class="sv-voted-badge"><span>✓</span> Ya votaste</div>`;
        toast('¡Voto registrado!');
    } else {
        btn.disabled = false;
        btn.textContent = 'Votar esta pregunta';
    }
}

cargarEncuesta();
