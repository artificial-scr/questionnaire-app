// Questionnaire builder: edits an in-memory document that follows
// questionnaire-1.0.schema.json and saves it through the REST API.
(function () {
  'use strict';

  const TYPES = {
    text: 'Text',
    number: 'Number',
    single_choice: 'Single choice',
    multiple_choice: 'Multiple choice',
    boolean: 'Yes / No',
    date: 'Date',
    scale: 'Scale',
  };
  const COMMON_KEYS = ['id', 'type', 'text', 'help', 'required'];
  const TYPE_KEYS = {
    text: ['multiline', 'maxLength'],
    number: ['min', 'max', 'integer'],
    single_choice: ['options'],
    multiple_choice: ['options', 'minSelections', 'maxSelections'],
    boolean: [],
    date: [],
    scale: ['min', 'max', 'minLabel', 'maxLabel'],
  };

  const $ = (sel) => document.querySelector(sel);
  const readJson = (id) => JSON.parse(document.getElementById(id).textContent);

  let pk = readJson('questionnaire-pk');
  const doc = readJson('questionnaire-data') || {
    schemaVersion: '1.0',
    id: '',
    title: '',
    questions: [],
  };

  // ---- helpers -----------------------------------------------------------

  function el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (key === 'class') node.className = value;
      else if (key === 'text') node.textContent = value;
      else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
      else if (value === true) node.setAttribute(key, '');
      else if (value !== false && value != null) node.setAttribute(key, value);
    }
    for (const child of [].concat(children)) if (child) node.append(child);
    return node;
  }

  function setOrDelete(obj, key, value) {
    if (value === '' || value == null || Number.isNaN(value)) delete obj[key];
    else obj[key] = value;
  }

  function uniqueId(prefix, taken) {
    let n = 1;
    while (taken.includes(`${prefix}${n}`)) n++;
    return `${prefix}${n}`;
  }

  function slugify(text) {
    const slug = text.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    return slug ? (/^[a-z]/.test(slug) ? slug : `q-${slug}`).slice(0, 64) : '';
  }

  function refreshPreview() {
    $('#json-preview').textContent = JSON.stringify(doc, null, 2);
  }

  // Inputs bound to a key on an object. Number inputs store numbers.
  function textInput(obj, key, attrs = {}) {
    return el('input', {
      type: 'text', value: obj[key] ?? '', ...attrs,
      oninput: (e) => { setOrDelete(obj, key, e.target.value); refreshPreview(); },
    });
  }

  function numberInput(obj, key, attrs = {}) {
    return el('input', {
      type: 'number', value: obj[key] ?? '', ...attrs,
      oninput: (e) => {
        setOrDelete(obj, key, e.target.value === '' ? '' : Number(e.target.value));
        refreshPreview();
      },
    });
  }

  function checkbox(obj, key) {
    return el('input', {
      type: 'checkbox', checked: !!obj[key],
      onchange: (e) => { obj[key] = e.target.checked; refreshPreview(); },
    });
  }

  function field(label, input) {
    return el('label', {}, [label, ' ', input]);
  }

  function inlineField(label, input) {
    return el('label', { class: 'inline' }, [input, ' ', label]);
  }

  // ---- question editing --------------------------------------------------

  function newQuestion(type) {
    const question = {
      id: uniqueId('q', doc.questions.map((q) => q.id)),
      type,
      text: '',
      required: false,
    };
    applyTypeDefaults(question);
    return question;
  }

  function applyTypeDefaults(question) {
    const allowed = new Set([...COMMON_KEYS, ...TYPE_KEYS[question.type]]);
    for (const key of Object.keys(question)) if (!allowed.has(key)) delete question[key];

    if (question.type.endsWith('_choice') && !question.options) {
      question.options = [
        { value: 'option_1', label: 'Option 1' },
        { value: 'option_2', label: 'Option 2' },
      ];
    }
    if (question.type === 'scale') {
      if (!Number.isInteger(question.min)) question.min = 1;
      if (!Number.isInteger(question.max)) question.max = 5;
    }
  }

  function optionsEditor(question) {
    const list = el('div', { class: 'options' });
    question.options.forEach((option, i) => {
      list.append(el('div', { class: 'option-row' }, [
        textInput(option, 'label', { placeholder: 'Label', 'aria-label': 'Option label' }),
        textInput(option, 'value', { placeholder: 'value', 'aria-label': 'Option value', class: 'mono' }),
        el('button', {
          type: 'button', class: 'btn btn-small', text: 'Remove', disabled: question.options.length <= 2,
          onclick: () => { question.options.splice(i, 1); render(); },
        }),
      ]));
    });
    list.append(el('button', {
      type: 'button', class: 'btn btn-small', text: 'Add option',
      onclick: () => {
        const value = uniqueId('option_', question.options.map((o) => o.value));
        question.options.push({ value, label: `Option ${value.split('_')[1]}` });
        render();
      },
    }));
    return list;
  }

  function typeFields(question) {
    switch (question.type) {
      case 'text':
        return [
          inlineField('Multi-line answer', checkbox(question, 'multiline')),
          field('Max length', numberInput(question, 'maxLength', { min: 1 })),
        ];
      case 'number':
        return [
          el('div', { class: 'row' }, [
            field('Min', numberInput(question, 'min')),
            field('Max', numberInput(question, 'max')),
          ]),
          inlineField('Whole numbers only', checkbox(question, 'integer')),
        ];
      case 'single_choice':
        return [optionsEditor(question)];
      case 'multiple_choice':
        return [
          optionsEditor(question),
          el('div', { class: 'row' }, [
            field('Min selections', numberInput(question, 'minSelections', { min: 0 })),
            field('Max selections', numberInput(question, 'maxSelections', { min: 1 })),
          ]),
        ];
      case 'scale':
        return [
          el('div', { class: 'row' }, [
            field('From', numberInput(question, 'min', { step: 1 })),
            field('To', numberInput(question, 'max', { step: 1 })),
          ]),
          el('div', { class: 'row' }, [
            field('Low label', textInput(question, 'minLabel', { maxlength: 100 })),
            field('High label', textInput(question, 'maxLabel', { maxlength: 100 })),
          ]),
        ];
      default:
        return [];
    }
  }

  function move(index, delta) {
    const [question] = doc.questions.splice(index, 1);
    doc.questions.splice(index + delta, 0, question);
    render();
  }

  function questionCard(question, index) {
    const typeSelect = el('select', {
      'aria-label': 'Question type',
      onchange: (e) => { question.type = e.target.value; applyTypeDefaults(question); render(); },
    }, Object.entries(TYPES).map(([value, label]) =>
      el('option', { value, text: label, selected: value === question.type })));

    const last = doc.questions.length - 1;
    return el('div', { class: 'card question' }, [
      el('div', { class: 'question-head' }, [
        el('span', { class: 'number', text: `${index + 1}.` }),
        typeSelect,
        el('span', { class: 'spacer' }),
        el('button', { type: 'button', class: 'btn btn-small', text: '↑', title: 'Move up', disabled: index === 0, onclick: () => move(index, -1) }),
        el('button', { type: 'button', class: 'btn btn-small', text: '↓', title: 'Move down', disabled: index === last, onclick: () => move(index, 1) }),
        el('button', {
          type: 'button', class: 'btn btn-small btn-danger', text: 'Delete',
          onclick: () => { doc.questions.splice(index, 1); render(); },
        }),
      ]),
      field('Question', textInput(question, 'text', { maxlength: 1000, placeholder: 'What would you like to ask?' })),
      el('div', { class: 'row' }, [
        field('ID', textInput(question, 'id', { maxlength: 64, class: 'mono' })),
        inlineField('Required', checkbox(question, 'required')),
      ]),
      field('Help text', textInput(question, 'help', { maxlength: 2000 })),
      ...typeFields(question),
    ]);
  }

  // Full re-render: only called on structural changes so typing keeps focus.
  function render() {
    const container = $('#questions');
    container.replaceChildren(...doc.questions.map(questionCard));
    if (!doc.questions.length) {
      container.append(el('p', { class: 'empty', text: 'No questions yet. Pick a type below and add one.' }));
    }
    refreshPreview();
  }

  // ---- saving ------------------------------------------------------------

  function csrfToken() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
  }

  function showErrors(messages) {
    $('#errors').replaceChildren(...messages.map((m) => el('li', { text: m })));
  }

  function flattenErrors(body) {
    if (Array.isArray(body)) return body.map(String);
    if (body && typeof body === 'object') {
      return Object.entries(body).flatMap(([key, value]) =>
        key === 'data' ? flattenErrors(value) : flattenErrors(value).map((m) => `${key}: ${m}`));
    }
    return [String(body)];
  }

  function updateDownloadLink() {
    const link = $('#download');
    link.hidden = pk == null;
    if (pk != null) link.href = `${window.API_BASE}${pk}/export/`;
  }

  async function save() {
    const status = $('#status');
    status.textContent = 'Saving…';
    showErrors([]);
    const url = pk == null ? window.API_BASE : `${window.API_BASE}${pk}/`;
    try {
      const response = await fetch(url, {
        method: pk == null ? 'POST' : 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
        body: JSON.stringify({ data: doc }),
      });
      const body = await response.json();
      if (!response.ok) {
        status.textContent = 'Not saved.';
        showErrors(flattenErrors(body));
        return;
      }
      if (pk == null) {
        pk = body.id;
        history.replaceState(null, '', `/${pk}/edit/`);
      }
      updateDownloadLink();
      status.textContent = `Saved at ${new Date().toLocaleTimeString()}.`;
    } catch (err) {
      status.textContent = 'Not saved.';
      showErrors([`Network error: ${err.message}`]);
    }
  }

  // ---- wiring ------------------------------------------------------------

  const titleInput = $('#q-title');
  const idInput = $('#q-id');
  // Suggest an id from the title until the user edits the id themselves.
  let idTouched = !!doc.id;

  titleInput.value = doc.title;
  idInput.value = doc.id;
  $('#q-description').value = doc.description ?? '';

  titleInput.addEventListener('input', (e) => {
    doc.title = e.target.value;
    if (!idTouched) idInput.value = doc.id = slugify(doc.title);
    refreshPreview();
  });
  idInput.addEventListener('input', (e) => {
    idTouched = true;
    doc.id = e.target.value;
    refreshPreview();
  });
  $('#q-description').addEventListener('input', (e) => {
    setOrDelete(doc, 'description', e.target.value);
    refreshPreview();
  });

  $('#new-type').append(...Object.entries(TYPES).map(([value, label]) => el('option', { value, text: label })));
  $('#add-question').addEventListener('click', () => {
    doc.questions.push(newQuestion($('#new-type').value));
    render();
    const cards = document.querySelectorAll('.question');
    cards[cards.length - 1].querySelector('input').focus();
  });
  $('#save').addEventListener('click', save);

  updateDownloadLink();
  render();
})();
