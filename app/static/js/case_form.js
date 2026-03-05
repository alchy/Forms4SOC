/**
 * Forms4SOC – dynamický renderer JSON dokumentu incidentu
 *
 * Každá sekce JSON šablony má svůj typ (type), podle kterého se zvolí
 * příslušná renderovací funkce. Analytik vyplňuje hodnoty přímo v DOM;
 * při ukládání se zpětně serializují do caseDocument.data.
 */

// ---------------------------------------------------------------------------
// Hlavní dispatcher
// ---------------------------------------------------------------------------

function renderSections(sections, container) {
    container.innerHTML = '';
    sections.forEach(section => {
        const el = renderSection(section);
        if (el) container.appendChild(el);
    });
}

function renderSection(section) {
    const wrapper = document.createElement('div');
    wrapper.className = 'case-section card border shadow-sm mb-3';
    wrapper.id = `sec-${section.id}`;

    const header = document.createElement('div');
    header.className = 'card-header d-flex align-items-center justify-content-between';
    header.innerHTML = `
        <span class="fw-semibold">${section.title}</span>
        ${section.description ? `<small class="text-muted ms-3 d-none d-md-block" style="max-width:60%">${section.description}</small>` : ''}
    `;
    wrapper.appendChild(header);

    const body = document.createElement('div');
    body.className = 'card-body';

    switch (section.type) {
        case 'playbook_header':  body.appendChild(renderPlaybookHeader(section)); break;
        case 'classification':   body.appendChild(renderClassification(section)); break;
        case 'contact_table':    body.appendChild(renderContactTable(section)); break;
        case 'section_group':    body.appendChild(renderSectionGroup(section)); break;
        case 'form':
        case 'closure_form':     body.appendChild(renderForm(section.fields || [])); break;
        case 'assets_table':     body.appendChild(renderAssetsTable(section)); break;
        case 'checklist':        body.appendChild(renderChecklist(section)); break;
        case 'action_table':     body.appendChild(renderActionTable(section)); break;
        case 'notification_table': body.appendChild(renderNotificationTable(section)); break;
        case 'raci_table':       body.appendChild(renderRaciTable(section)); break;
        default:
            body.innerHTML = `<pre class="text-secondary small mb-0">${JSON.stringify(section, null, 2)}</pre>`;
    }

    wrapper.appendChild(body);
    return wrapper;
}

// ---------------------------------------------------------------------------
// Pomocné funkce pro tvorbu prvků
// ---------------------------------------------------------------------------

function el(tag, cls, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    return e;
}

function renderFieldInput(field) {
    if (!field.editable) {
        return el('span', 'text-secondary fst-italic',
            field.value !== null && field.value !== undefined ? field.value : '–');
    }

    switch (field.type) {
        case 'textarea': {
            const ta = el('textarea', 'form-control form-control-sm bg-light');
            ta.rows = 3;
            ta.placeholder = field.example || field.hint || '';
            ta.value = field.value || '';
            ta.dataset.fieldKey = field.key;
            ta.addEventListener('change', () => { field.value = ta.value; });
            return ta;
        }
        case 'select': {
            const sel = el('select', 'form-select form-select-sm');
            sel.dataset.fieldKey = field.key;
            const emptyOpt = document.createElement('option');
            emptyOpt.value = '';
            emptyOpt.textContent = '– vyberte –';
            sel.appendChild(emptyOpt);
            (field.options || []).forEach(opt => {
                const o = document.createElement('option');
                o.value = opt;
                o.textContent = opt;
                if (field.value === opt) o.selected = true;
                sel.appendChild(o);
            });
            sel.addEventListener('change', () => { field.value = sel.value || null; });
            // Nápověda pod select
            if (field.option_hints) {
                const hint = el('div', 'form-text text-secondary small mt-1');
                const updateHint = () => {
                    hint.textContent = sel.value && field.option_hints[sel.value]
                        ? field.option_hints[sel.value] : '';
                };
                sel.addEventListener('change', updateHint);
                updateHint();
                const wrap = el('div');
                wrap.appendChild(sel);
                wrap.appendChild(hint);
                return wrap;
            }
            return sel;
        }
        case 'datetime': {
            const inp = el('input', 'form-control form-control-sm');
            inp.type = 'datetime-local';
            inp.dataset.fieldKey = field.key;
            if (field.value) inp.value = field.value.substring(0, 16);
            inp.addEventListener('change', () => { field.value = inp.value || null; });
            return inp;
        }
        default: {
            const inp = el('input', 'form-control form-control-sm');
            inp.type = 'text';
            inp.placeholder = field.example || field.hint || '';
            inp.dataset.fieldKey = field.key;
            inp.value = field.value || '';
            inp.addEventListener('change', () => { field.value = inp.value || null; });
            return inp;
        }
    }
}

// ---------------------------------------------------------------------------
// Formulář (form, closure_form)
// ---------------------------------------------------------------------------

function renderForm(fields) {
    const wrap = el('div');
    fields.forEach(field => {
        const row = el('div', 'row mb-2 align-items-center');
        const labelCol = el('div', 'col-md-4');
        labelCol.innerHTML = `<label class="form-label text-secondary small mb-0">${field.label}${field.editable ? '' : ''}</label>
            ${field.hint && field.type !== 'select' ? `<div class="form-text text-secondary" style="font-size:0.75rem">${field.hint}</div>` : ''}`;
        const inputCol = el('div', 'col-md-8');
        inputCol.appendChild(renderFieldInput(field));
        row.appendChild(labelCol);
        row.appendChild(inputCol);
        wrap.appendChild(row);
    });
    return wrap;
}

// ---------------------------------------------------------------------------
// Hlavička playbooku (read-only metadata panel)
// ---------------------------------------------------------------------------

function renderPlaybookHeader(section) {
    const wrap = el('div');

    // Editovatelná pole (case_title apod.) zobrazit prominentně nahoře
    const editableFields = (section.fields || []).filter(f => f.editable);
    const readonlyFields = (section.fields || []).filter(f => !f.editable);

    editableFields.forEach(field => {
        const row = el('div', 'row mb-3 align-items-center');
        const labelCol = el('div', 'col-md-4');
        labelCol.innerHTML = `<label class="form-label fw-semibold small mb-0">${field.label}</label>
            ${field.hint ? `<div class="form-text text-muted" style="font-size:0.75rem">${field.hint}</div>` : ''}`;
        const inputCol = el('div', 'col-md-8');
        inputCol.appendChild(renderFieldInput(field));
        row.appendChild(labelCol);
        row.appendChild(inputCol);
        wrap.appendChild(row);
    });

    if (readonlyFields.length > 0) {
        const infoGrid = el('div', 'row g-2 mt-1 pt-2 border-top');
        readonlyFields.forEach(field => {
            const col = el('div', 'col-md-4 col-lg-3');
            col.innerHTML = `
                <div class="d-flex flex-column">
                    <span class="text-muted small">${field.label}</span>
                    <span class="small fw-semibold">${field.value !== null && field.value !== undefined ? field.value : '–'}</span>
                </div>`;
            infoGrid.appendChild(col);
        });
        wrap.appendChild(infoGrid);
    }

    return wrap;
}

// ---------------------------------------------------------------------------
// Klasifikace (read-only MITRE + kategorie panel)
// ---------------------------------------------------------------------------

function renderClassification(section) {
    const wrap = el('div');
    const row = el('div', 'row g-2 mb-2');

    (section.fields || []).filter(f => f.key !== 'data_sources').forEach(field => {
        const col = el('div', 'col-md-6 col-lg-4');
        col.innerHTML = `
            <div class="d-flex flex-column">
                <span class="text-muted small">${field.label}</span>
                <span class="fw-semibold">${field.value !== null && field.value !== undefined ? field.value : '–'}</span>
            </div>`;
        row.appendChild(col);
    });
    wrap.appendChild(row);

    // Data sources jako badge seznam
    const dsField = (section.fields || []).find(f => f.key === 'data_sources');
    if (dsField && dsField.value) {
        const sources = Array.isArray(dsField.value) ? dsField.value : [dsField.value];
        const dsWrap = el('div', 'mt-2');
        dsWrap.appendChild(el('span', 'text-muted small me-2', dsField.label + ':'));
        sources.forEach(src => {
            dsWrap.appendChild(el('span', 'badge bg-secondary-subtle text-secondary border border-secondary-subtle me-1', src));
        });
        wrap.appendChild(dsWrap);
    }

    return wrap;
}

// ---------------------------------------------------------------------------
// Kontaktní tabulka
// ---------------------------------------------------------------------------

function renderContactTable(section) {
    const wrap = el('div', 'table-responsive');
    const table = el('table', 'table table-sm table-bordered mb-0');

    const thead = document.createElement('thead');
    const hr = document.createElement('tr');
    (section.columns || []).forEach(col => {
        const th = el('th', 'text-muted small', section.column_labels?.[col] || col);
        hr.appendChild(th);
    });
    thead.appendChild(hr);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    (section.rows || []).forEach(row => {
        const tr = document.createElement('tr');
        (section.columns || []).forEach(col => {
            const td = document.createElement('td');
            const editable = (section.editable_columns || []).includes(col);
            if (editable) {
                const inp = el('input', 'form-control form-control-sm border-0 p-0');
                inp.type = 'text';
                inp.value = row[col] || '';
                inp.placeholder = row[col + '_example'] || '';
                inp.style.background = 'transparent';
                inp.addEventListener('change', () => { row[col] = inp.value || null; });
                td.appendChild(inp);
            } else {
                td.className = 'small align-middle';
                td.textContent = row[col] || '–';
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    return wrap;
}

// ---------------------------------------------------------------------------
// Section group (podsekce)
// ---------------------------------------------------------------------------

function renderSectionGroup(section) {
    const wrap = el('div');
    const acc = el('div', 'accordion accordion-flush');
    acc.id = `acc-${section.id}`;

    (section.subsections || []).forEach((sub, idx) => {
        const item = el('div', 'accordion-item border mb-2');
        const headerId = `sh-${section.id}-${sub.id}`;
        const bodyId = `sb-${section.id}-${sub.id}`;
        const isFirst = idx === 0;

        item.innerHTML = `
            <h2 class="accordion-header" id="${headerId}">
                <button class="accordion-button ${isFirst ? '' : 'collapsed'}"
                        type="button" data-bs-toggle="collapse"
                        data-bs-target="#${bodyId}" aria-expanded="${isFirst}">
                    ${sub.title}
                    ${sub.note ? `<small class="text-muted ms-3">${sub.note}</small>` : ''}
                </button>
            </h2>
            <div id="${bodyId}" class="accordion-collapse collapse ${isFirst ? 'show' : ''}" data-bs-parent="#${acc.id}">
                <div class="accordion-body pt-2" id="body-${bodyId}"></div>
            </div>`;

        acc.appendChild(item);

        // Render obsahu podsekce po přidání do DOMu
        requestAnimationFrame(() => {
            const bodyEl = document.getElementById(`body-${bodyId}`);
            if (!bodyEl) return;
            switch (sub.type) {
                case 'form':        bodyEl.appendChild(renderForm(sub.fields || [])); break;
                case 'assets_table': bodyEl.appendChild(renderAssetsTable(sub)); break;
                default:            bodyEl.appendChild(renderForm(sub.fields || []));
            }
        });
    });

    wrap.appendChild(acc);
    return wrap;
}

// ---------------------------------------------------------------------------
// Tabulka assetů (dynamické přidávání řádků)
// ---------------------------------------------------------------------------

function renderAssetsTable(section) {
    const wrap = el('div');

    if (section.hint) {
        wrap.appendChild(el('div', 'alert alert-warning alert-sm py-2 small mb-3',
            `<i class="bi bi-exclamation-triangle me-1"></i>${section.hint}`));
    }

    const tableWrap = el('div', 'table-responsive');
    const table = el('table', 'table table-sm table-bordered mb-2');

    const thead = document.createElement('thead');
    const hr = document.createElement('tr');
    (section.columns || []).forEach(col => {
        hr.appendChild(el('th', 'text-secondary small', section.column_labels?.[col] || col));
    });
    hr.appendChild(el('th', 'text-secondary small', ''));
    thead.appendChild(hr);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    tbody.id = `assets-body-${section.id}`;

    const renderAssetRow = (row) => {
        const tr = document.createElement('tr');
        (section.columns || []).forEach(col => {
            const td = document.createElement('td');
            const opts = section.column_options?.[col];
            if (opts) {
                const sel = el('select', 'form-select form-select-sm border-0');
                opts.forEach(o => {
                    const opt = document.createElement('option');
                    opt.value = o; opt.textContent = o;
                    if (row[col] === o) opt.selected = true;
                    sel.appendChild(opt);
                });
                sel.addEventListener('change', () => { row[col] = sel.value; });
                td.appendChild(sel);
            } else {
                const inp = el('input', 'form-control form-control-sm border-0');
                inp.type = 'text';
                inp.value = row[col] || '';
                inp.addEventListener('change', () => { row[col] = inp.value || null; });
                td.appendChild(inp);
            }
            tr.appendChild(td);
        });
        const delTd = document.createElement('td');
        const delBtn = el('button', 'btn btn-link btn-sm text-danger p-0',
            '<i class="bi bi-trash"></i>');
        delBtn.addEventListener('click', () => {
            const idx = section.rows.indexOf(row);
            if (idx > -1) section.rows.splice(idx, 1);
            tr.remove();
        });
        delTd.appendChild(delBtn);
        tr.appendChild(delTd);
        return tr;
    };

    (section.rows || []).forEach(row => tbody.appendChild(renderAssetRow(row)));
    table.appendChild(tbody);
    tableWrap.appendChild(table);
    wrap.appendChild(tableWrap);

    const addBtn = el('button', 'btn btn-outline-secondary btn-sm',
        '<i class="bi bi-plus me-1"></i>Přidat asset');
    addBtn.addEventListener('click', () => {
        const newRow = {};
        (section.columns || []).forEach(col => { newRow[col] = null; });
        if (!section.rows) section.rows = [];
        section.rows.push(newRow);
        tbody.appendChild(renderAssetRow(newRow));
    });
    wrap.appendChild(addBtn);
    return wrap;
}

// ---------------------------------------------------------------------------
// Checklist (triage, investigation)
// ---------------------------------------------------------------------------

function renderChecklist(section) {
    const wrap = el('div');

    (section.step_groups || []).forEach(group => {
        const groupEl = el('div', 'mb-4');
        const titleEl = el('div', 'd-flex align-items-center gap-2 mb-2');
        titleEl.innerHTML = `<span class="fw-semibold">${group.title}</span>
            ${group.note ? `<small class="text-muted">(${group.note})</small>` : ''}`;
        groupEl.appendChild(titleEl);

        (group.hints || []).forEach(hint => {
            groupEl.appendChild(el('div', 'alert alert-secondary py-1 px-2 small mb-2',
                `<i class="bi bi-info-circle me-1"></i>${hint}`));
        });

        const stepsEl = el('div', 'border border-secondary rounded');
        (group.steps || []).forEach((step, idx) => {
            const stepEl = el('div',
                `p-3 ${idx < group.steps.length - 1 ? 'border-bottom border-secondary' : ''}`);
            stepEl.innerHTML = `
                <div class="d-flex gap-3">
                    <div class="flex-shrink-0 mt-1">
                        <input type="checkbox" class="form-check-input step-check"
                               id="chk-${step.id}" ${step.done ? 'checked' : ''}>
                    </div>
                    <div class="flex-grow-1">
                        <label for="chk-${step.id}" class="small mb-2 d-block" style="cursor:pointer">
                            ${step.action}
                        </label>
                        <textarea class="form-control form-control-sm bg-light"
                                  rows="2" placeholder="${step.example || 'Poznámka analytika...'}"
                                  data-step-id="${step.id}">${step.analyst_note || ''}</textarea>
                    </div>
                </div>`;

            const chk = stepEl.querySelector('.step-check');
            chk.addEventListener('change', () => { step.done = chk.checked; });

            const ta = stepEl.querySelector('textarea');
            ta.addEventListener('change', () => { step.analyst_note = ta.value || null; });

            stepsEl.appendChild(stepEl);
        });
        groupEl.appendChild(stepsEl);
        wrap.appendChild(groupEl);
    });

    // Výsledek (result) sekce
    if (section.result) {
        const resEl = el('div', 'mt-4');
        resEl.appendChild(el('div', 'fw-semibold mb-2',
            `<i class="bi bi-flag me-2 text-danger"></i>${section.result.title}`));

        if (section.result.notifications) {
            const notifEl = el('div', 'alert alert-info small mb-3');
            notifEl.innerHTML = '<strong>Notifikace:</strong><ul class="mb-0 mt-1">'
                + section.result.notifications.map(n => `<li>${n}</li>`).join('') + '</ul>';
            resEl.appendChild(notifEl);
        }

        resEl.appendChild(renderForm(section.result.fields || []));
        wrap.appendChild(resEl);
    }

    return wrap;
}

// ---------------------------------------------------------------------------
// Tabulka akcí (containment_remediation)
// ---------------------------------------------------------------------------

function renderActionTable(section) {
    const wrap = el('div', 'table-responsive');
    const table = el('table', 'table table-sm table-bordered mb-0');

    const thead = document.createElement('thead');
    const hr = document.createElement('tr');
    (section.columns || []).forEach(col => {
        hr.appendChild(el('th', 'text-muted small', section.column_labels?.[col] || col));
    });
    thead.appendChild(hr);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    (section.rows || []).forEach(row => {
        const tr = document.createElement('tr');
        (section.columns || []).forEach(col => {
            const td = document.createElement('td');
            td.className = 'small';
            const editable = (section.editable_columns || []).includes(col);
            if (editable && section.status_options) {
                const sel = el('select', 'form-select form-select-sm border-0');
                const emptyOpt = document.createElement('option');
                emptyOpt.value = ''; emptyOpt.textContent = '–';
                sel.appendChild(emptyOpt);
                section.status_options.forEach(opt => {
                    const o = document.createElement('option');
                    o.value = opt; o.textContent = opt;
                    if (row[col] === opt) o.selected = true;
                    sel.appendChild(o);
                });
                sel.addEventListener('change', () => { row[col] = sel.value || null; });
                td.appendChild(sel);
            } else {
                td.className = 'small align-middle';
                td.textContent = row[col] || '–';
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);

    if (section.hints) {
        section.hints.forEach(hint => {
            wrap.appendChild(el('div', 'form-text text-secondary small mt-2',
                `<i class="bi bi-info-circle me-1"></i>${hint}`));
        });
    }
    return wrap;
}

// ---------------------------------------------------------------------------
// Tabulka notifikací (communication)
// ---------------------------------------------------------------------------

function renderNotificationTable(section) {
    return renderActionTable(section);  // stejná struktura, jen jiná data
}

// ---------------------------------------------------------------------------
// RACI tabulka (pouze pro čtení)
// ---------------------------------------------------------------------------

function renderRaciTable(section) {
    const wrap = el('div');

    if (section.legend) {
        wrap.appendChild(el('div', 'text-secondary small mb-2',
            `<i class="bi bi-info-circle me-1"></i>${section.legend}`));
    }

    const tableWrap = el('div', 'table-responsive');
    const table = el('table', 'table table-sm table-bordered mb-0');

    const thead = document.createElement('thead');
    const hr = document.createElement('tr');
    (section.columns || []).forEach(col => {
        hr.appendChild(el('th', 'text-muted small', section.column_labels?.[col] || col));
    });
    thead.appendChild(hr);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    (section.rows || []).forEach(row => {
        const tr = document.createElement('tr');
        (section.columns || []).forEach(col => {
            const td = el('td', 'small align-middle');
            const val = row[col] || '–';
            if (val.includes('R')) td.innerHTML = `<strong class="text-danger">${val}</strong>`;
            else td.textContent = val;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    tableWrap.appendChild(table);
    wrap.appendChild(tableWrap);
    return wrap;
}
