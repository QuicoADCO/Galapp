const token = localStorage.getItem('token');
if (!token) window.location.href = '/login';

// ── STATE ──────────────────────────────────────────────────────────────────
let coverFile = null;
const optionImages = new WeakMap(); // optionRow DOM element → File

// ── AUTH HEADER ────────────────────────────────────────────────────────────
function authHdr() {
    return { 'Authorization': 'Bearer ' + token };
}

// ── BANNER ─────────────────────────────────────────────────────────────────
function showBanner(msg, type = 'error') {
    const el = document.getElementById('banner');
    el.textContent = msg;
    el.className = 'banner ' + type;
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
function hideBanner() {
    document.getElementById('banner').className = 'banner';
}

// ── CHARACTER COUNTERS ─────────────────────────────────────────────────────
function setupCounter(inputId, countId, max) {
    const input   = document.getElementById(inputId);
    const counter = document.getElementById(countId);
    input.addEventListener('input', () => {
        const len = input.value.length;
        counter.textContent = `${len} / ${max}`;
        counter.className = 'char-count' +
            (len >= max ? ' at-limit' : len >= max * 0.9 ? ' near-limit' : '');
    });
}
setupCounter('f-title', 'title-count', 200);
setupCounter('f-desc',  'desc-count',  500);

// ── COVER IMAGE ────────────────────────────────────────────────────────────
const dropZone    = document.getElementById('drop-zone');
const fileInput   = document.getElementById('image-input');
const preview     = document.getElementById('image-preview');
const dropContent = document.getElementById('drop-content');
const btnRemove   = document.getElementById('btn-remove-img');

function setCover(file) {
    if (!file) return;
    const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowed.includes(file.type)) { showBanner('Tipo de archivo no permitido. Usa JPG, PNG, GIF o WEBP.'); return; }
    if (file.size > 4 * 1024 * 1024)  { showBanner('La imagen supera el límite de 4 MB.'); return; }
    hideBanner();
    coverFile = file;
    const reader = new FileReader();
    reader.onload = e => {
        preview.src = e.target.result;
        preview.classList.remove('hidden');
        dropContent.style.display = 'none';
        btnRemove.classList.remove('hidden');
        dropZone.classList.add('has-image');
    };
    reader.readAsDataURL(file);
}

function removeCover() {
    coverFile = null;
    preview.src = '';
    preview.classList.add('hidden');
    dropContent.style.display = '';
    btnRemove.classList.add('hidden');
    dropZone.classList.remove('has-image');
    fileInput.value = '';
}

dropZone.addEventListener('click',     () => { if (!dropZone.classList.contains('has-image')) fileInput.click(); });
fileInput.addEventListener('change',   () => { if (fileInput.files[0]) setCover(fileInput.files[0]); });
btnRemove.addEventListener('click',    e  => { e.stopPropagation(); removeCover(); });
dropZone.addEventListener('dragenter', e  => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragover',  e  => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', ()  => { dropZone.classList.remove('drag-over'); });
dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files[0]) setCover(e.dataTransfer.files[0]);
});

// ── QUESTIONS ─────────────────────────────────────────────────────────────
let questionCounter = 0;

document.getElementById('btn-add-question').addEventListener('click', addQuestion);

function addQuestion() {
    questionCounter++;
    const list  = document.getElementById('questions-list');
    const block = document.createElement('div');
    block.className = 'question-block';
    block.dataset.qid = questionCounter;

    block.innerHTML = `
        <div class="question-header">
            <span class="question-num">Pregunta ${list.children.length + 1}</span>
            <div class="type-toggle">
                <button type="button" class="type-btn active" data-type="single">Opción única</button>
                <button type="button" class="type-btn" data-type="multiple">Opción múltiple</button>
            </div>
            <button type="button" class="btn-remove-q" aria-label="Eliminar pregunta">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        </div>
        <div class="form-group q-text-group">
            <input type="text" class="q-text" placeholder="¿Qué quieres preguntar?" maxlength="500">
            <span class="char-count q-char-count">0 / 500</span>
        </div>
        <div class="q-options-list"></div>
        <button type="button" class="btn-add-opt-q">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Añadir opción
        </button>`;

    // Character counter for question text
    const qInput   = block.querySelector('.q-text');
    const qCounter = block.querySelector('.q-char-count');
    qInput.addEventListener('input', () => {
        const len = qInput.value.length;
        qCounter.textContent = `${len} / 500`;
        qCounter.className = 'char-count q-char-count' +
            (len >= 500 ? ' at-limit' : len >= 450 ? ' near-limit' : '');
    });

    // Type toggle
    block.querySelectorAll('.type-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            block.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    // Remove question
    block.querySelector('.btn-remove-q').addEventListener('click', () => {
        if (document.querySelectorAll('.question-block').length <= 1) return;
        block.remove();
        updateQuestionNumbers();
    });

    // Add option button
    block.querySelector('.btn-add-opt-q').addEventListener('click', () => addOption(block));

    list.appendChild(block);
    updateQuestionNumbers();

    // Start with 2 default options
    addOption(block);
    addOption(block);
    qInput.focus();
}

function updateQuestionNumbers() {
    document.querySelectorAll('.question-block').forEach((block, i) => {
        block.querySelector('.question-num').textContent = `Question ${i + 1}`;
    });
}

// ── OPTIONS ────────────────────────────────────────────────────────────────
function addOption(block) {
    const list  = block.querySelector('.q-options-list');
    const count = list.children.length + 1;
    const row   = document.createElement('div');
    row.className = 'option-row';
    row.innerHTML = `
        <span class="opt-num">${count}</span>
        <input type="text" class="opt-text" placeholder="Option ${count}" maxlength="300">
        <div class="opt-img-wrap">
            <label class="opt-img-trigger" title="Attach image (optional)">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
                    <polyline points="21 15 16 10 5 21"/>
                </svg>
                <input type="file" class="opt-img-input file-input-hidden" accept="image/jpeg,image/png,image/gif,image/webp">
            </label>
            <div class="opt-thumb-wrap hidden">
                <img class="opt-thumb" alt="">
                <button type="button" class="opt-thumb-remove" title="Remove image">×</button>
            </div>
        </div>
        <button type="button" class="btn-remove-opt" aria-label="Remove option">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
        </button>`;

    const imgInput   = row.querySelector('.opt-img-input');
    const thumbWrap  = row.querySelector('.opt-thumb-wrap');
    const thumbImg   = row.querySelector('.opt-thumb');
    const thumbRm    = row.querySelector('.opt-thumb-remove');

    imgInput.addEventListener('change', () => {
        const file = imgInput.files[0];
        if (!file) return;
        const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
        if (!allowed.includes(file.type)) { showBanner('Tipo de imagen no permitido.'); return; }
        if (file.size > 4 * 1024 * 1024)  { showBanner('La imagen de la opción supera 4 MB.'); return; }
        optionImages.set(row, file);
        const reader = new FileReader();
        reader.onload = e => { thumbImg.src = e.target.result; thumbWrap.classList.remove('hidden'); };
        reader.readAsDataURL(file);
    });

    thumbRm.addEventListener('click', () => {
        optionImages.delete(row);
        thumbImg.src = '';
        thumbWrap.classList.add('hidden');
        imgInput.value = '';
    });

    row.querySelector('.btn-remove-opt').addEventListener('click', () => {
        if (list.children.length <= 2) return;
        optionImages.delete(row);
        row.remove();
        updateOptNumbers(list);
    });

    list.appendChild(row);
    updateOptNumbers(list);
}

function updateOptNumbers(list) {
    list.querySelectorAll('.option-row').forEach((row, i) => {
        row.querySelector('.opt-num').textContent = i + 1;
        row.querySelector('.opt-text').placeholder = `Option ${i + 1}`;
    });
}

// ── SUBMIT ─────────────────────────────────────────────────────────────────
document.getElementById('survey-form').addEventListener('submit', async e => {
    e.preventDefault();
    hideBanner();

    const title = document.getElementById('f-title').value.trim();
    const desc  = document.getElementById('f-desc').value.trim();

    if (!title) { showBanner('El título es obligatorio.'); return; }

    const questionBlocks = document.querySelectorAll('.question-block');
    if (questionBlocks.length === 0) { showBanner('Añade al menos una pregunta.'); return; }

    for (const block of questionBlocks) {
        const qText = block.querySelector('.q-text').value.trim();
        if (!qText) {
            showBanner('Todas las preguntas deben tener texto.');
            block.querySelector('.q-text').focus();
            return;
        }
        const optRows = block.querySelectorAll('.option-row');
        if (optRows.length < 2) {
            showBanner('Cada pregunta necesita al menos 2 opciones.');
            return;
        }
        for (const row of optRows) {
            if (!row.querySelector('.opt-text').value.trim()) {
                showBanner('Todas las opciones deben tener texto.');
                row.querySelector('.opt-text').focus();
                return;
            }
        }
    }

    const btn     = document.getElementById('btn-submit');
    const btnText = document.getElementById('btn-text');
    const spinner = document.getElementById('btn-spinner');
    btn.disabled = true;
    btnText.textContent = 'Creando…';
    spinner.classList.remove('hidden');

    try {
        // 1. Create survey (multipart for optional cover image)
        const surveyForm = new FormData();
        surveyForm.append('title', title);
        surveyForm.append('description', desc);
        if (coverFile) surveyForm.append('image', coverFile);

        const surveyRes  = await fetch('/api/surveys', { method: 'POST', headers: authHdr(), body: surveyForm });
        const surveyData = await surveyRes.json();
        if (!surveyRes.ok) { showBanner(surveyData.error || 'Error al crear la encuesta.'); return; }

        const surveyId = surveyData.id;

        // 2. Create each question then its options
        for (const block of questionBlocks) {
            const qText = block.querySelector('.q-text').value.trim();
            const qType = block.querySelector('.type-btn.active').dataset.type;

            const qRes  = await fetch(`/api/surveys/${surveyId}/questions`, {
                method: 'POST',
                headers: { ...authHdr(), 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: qText, type: qType }),
            });
            const qData = await qRes.json();
            if (!qRes.ok) { showBanner(qData.error || 'Error al añadir la pregunta.'); return; }

            const questionId = qData.id;

            for (const row of block.querySelectorAll('.option-row')) {
                const optText = row.querySelector('.opt-text').value.trim();
                const imgFile = optionImages.get(row) || null;

                const optForm = new FormData();
                optForm.append('text', optText);
                if (imgFile) optForm.append('image', imgFile);

                const optRes = await fetch(`/api/questions/${questionId}/options`, {
                    method: 'POST',
                    headers: authHdr(),
                    body: optForm,
                });
                if (!optRes.ok) {
                    const d = await optRes.json();
                    showBanner(d.error || 'Error adding option.');
                    return;
                }
            }
        }

        showBanner('¡Encuesta creada! Redirigiendo…', 'success');
        setTimeout(() => { window.location.href = '/dashboard'; }, 1200);

    } catch {
        showBanner('Error de red. Comprueba tu conexión.');
    } finally {
        btn.disabled = false;
        btnText.textContent = 'Crear encuesta';
        spinner.classList.add('hidden');
    }
});

// Start with one question by default
addQuestion();
