const token = localStorage.getItem('token');
if (!token) window.location.href = '/login';

function parseJwt(t) {
    try { return JSON.parse(atob(t.split('.')[1])); } catch { return {}; }
}

const pl       = parseJwt(token);
const username = pl.username || '?';
const role     = pl.role || 'user';

// Populate sidebar & stats
document.getElementById('avatar').textContent     = username[0].toUpperCase();
document.getElementById('sb-username').textContent = username;
document.getElementById('sb-role').textContent    = role;
document.getElementById('st-role').textContent    = role;

function authHdr() {
    return { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token };
}

// ── TOAST ──
function toast(msg, type = 'success') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = 'toast show ' + type;
    setTimeout(() => { el.className = 'toast'; }, 3000);
}

// ── SECTIONS ──
function showSection(_name, btn) {
    document.getElementById('sec-surveys').style.display = '';
    document.getElementById('topbar-title').textContent  = 'Surveys';
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}

// ── LOAD SURVEYS ──
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
                <h3>No surveys yet</h3>
                <p>Create the first one with the button above</p>
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
    const res  = await fetch(`/api/surveys/${survey.id}`, { headers: authHdr() });
    const data = await res.json();
    const opts = data.options || [];

    const el = document.createElement('div');
    el.className = 'survey-card';
    el.innerHTML = `
        <div class="survey-tag">Survey #${survey.id}</div>
        <div class="survey-title">${esc(survey.title)}</div>
        <div class="survey-desc">${esc(survey.description || '')}</div>
        <form class="options-vote" onsubmit="vote(event, ${survey.id})">
            ${opts.map(o => `
            <label class="vote-option">
                <input type="radio" name="o${survey.id}" value="${o.id}" required>
                ${esc(o.option_text)}
            </label>`).join('')}
            ${opts.length === 0
                ? '<p style="font-size:13px;color:var(--muted)">No options yet.</p>'
                : ''}
            <div class="card-footer">
                <span class="card-meta">${opts.length} option${opts.length !== 1 ? 's' : ''}</span>
                ${opts.length > 0
                    ? `<button type="submit" class="btn btn-success btn-sm">🗳️ Vote</button>`
                    : ''}
            </div>
        </form>`;
    return { el, n: opts.length };
}

async function vote(e, surveyId) {
    e.preventDefault();
    const sel = e.target.querySelector(`input[name="o${surveyId}"]:checked`);
    if (!sel) return;

    const res  = await fetch('/api/votes', {
        method: 'POST',
        headers: authHdr(),
        body: JSON.stringify({ survey_id: surveyId, option_id: +sel.value })
    });
    const data = await res.json();

    if (res.ok) {
        toast('Vote recorded!');
        e.target.querySelectorAll('input').forEach(i => i.disabled = true);
        const btn = e.target.querySelector('button[type="submit"]');
        btn.textContent = '✓ Voted';
        btn.disabled = true;
        btn.style.opacity = '0.6';
    } else {
        toast(data.error || 'Vote failed', 'error');
    }
}

// ── CREATE SURVEY ──
function openModal()  { document.getElementById('modal').classList.add('open'); }
function closeModal() { document.getElementById('modal').classList.remove('open'); }

function addOpt() {
    const list  = document.getElementById('opt-list');
    const count = list.children.length + 1;
    const row   = document.createElement('div');
    row.className = 'option-row';
    row.innerHTML = `<input type="text" placeholder="Option ${count}">
                     <button class="btn-remove" onclick="removeOpt(this)">×</button>`;
    list.appendChild(row);
}

function removeOpt(btn) {
    const list = document.getElementById('opt-list');
    if (list.children.length > 1) btn.parentElement.remove();
}

async function createSurvey() {
    const title  = document.getElementById('f-title').value.trim();
    const desc   = document.getElementById('f-desc').value.trim();
    const opts   = Array.from(document.querySelectorAll('#opt-list .option-row input'))
                        .map(i => i.value.trim()).filter(Boolean);

    if (!title)          { toast('Title is required', 'error'); return; }
    if (opts.length < 2) { toast('Add at least 2 options', 'error'); return; }

    const res  = await fetch('/api/surveys', {
        method: 'POST',
        headers: authHdr(),
        body: JSON.stringify({ title, description: desc })
    });
    const data = await res.json();
    if (!res.ok) { toast(data.error || 'Error creating survey', 'error'); return; }

    for (const opt of opts) {
        await fetch(`/api/surveys/${data.id}/options`, {
            method: 'POST',
            headers: authHdr(),
            body: JSON.stringify({ option_text: opt })
        });
    }

    closeModal();
    toast('Survey created!');

    // Reset form
    document.getElementById('f-title').value = '';
    document.getElementById('f-desc').value  = '';
    document.getElementById('opt-list').innerHTML = `
        <div class="option-row"><input type="text" placeholder="Option 1"><button class="btn-remove" onclick="removeOpt(this)">×</button></div>
        <div class="option-row"><input type="text" placeholder="Option 2"><button class="btn-remove" onclick="removeOpt(this)">×</button></div>`;

    loadSurveys();
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}

function esc(s) {
    return String(s)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

loadSurveys();
