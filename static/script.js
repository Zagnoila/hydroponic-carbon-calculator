/* The browser collects inputs and displays Python results. No emissions math here. */
const form = document.querySelector('#farm-form');
const calculateButton = document.querySelector('#calculate');
const summary = document.querySelector('#error-summary');
const resultContent = document.querySelector('#result-content');
const resultSection = document.querySelector('#results');
const example = JSON.parse(document.querySelector('#example-data').textContent);
const number = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });
const precise = new Intl.NumberFormat('en-US', { maximumFractionDigits: 4 });
const percent = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });
let chart = null;
let requestController = null;
let requestVersion = 0;
let editVersion = 0;
const format = value => value > 0 && value < 0.0001 ? '<0.0001' : value > 0 && value < 0.01 ? precise.format(value) : number.format(value);
const share = value => value > 0 && value < 0.01 ? '<0.01%' : `${percent.format(value)}%`;
const text = (id, value) => { document.getElementById(id).textContent = value; };

function clearErrors() {
  summary.hidden = true;
  summary.replaceChildren();
  form.querySelectorAll('[aria-invalid]').forEach(input => input.removeAttribute('aria-invalid'));
  form.querySelectorAll('.field-error').forEach(el => { el.textContent = ''; });
}

function displayErrors(message, errors = {}) {
  summary.textContent = message;
  const list = document.createElement('ul');
  Object.entries(errors).forEach(([key, problem]) => {
    const input = form.elements.namedItem(key);
    const fieldError = document.getElementById(`error-${key}`);
    if (input) input.setAttribute('aria-invalid', 'true');
    if (fieldError) fieldError.textContent = problem;
    if (key.startsWith('factor_')) document.querySelector('#factor-panel').open = true;
    const item = document.createElement('li');
    item.textContent = problem;
    list.append(item);
  });
  if (list.childElementCount) summary.append(list);
  summary.hidden = false;
  summary.focus({ preventScroll: true });
  summary.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function markChanged() {
  editVersion += 1;
  if (!resultContent.hidden) {
    document.querySelector('#stale-notice').hidden = false;
    text('result-badge', 'Recalculate to update');
  }
}

form.addEventListener('input', markChanged);
document.querySelector('#load-example').addEventListener('click', () => {
  Object.entries(example).forEach(([key, value]) => {
    const field = form.elements.namedItem(key);
    if (field) field.value = value;
  });
  clearErrors();
  markChanged();
  text('form-status', 'Spreadsheet example loaded. These are demonstration values, not measured farm data.');
  document.querySelector('#farm').scrollIntoView({ behavior: 'smooth', block: 'start' });
});

function focusCategory(index, categories) {
  document.querySelectorAll('.legend-button').forEach((button, i) => {
    button.classList.toggle('active', i === index);
    button.setAttribute('aria-pressed', String(i === index));
  });
  const row = categories[index];
  text('chart-insight', `${row.label}: ${format(row.emissions)} kg CO₂e per year · ${share(row.percentage)} of your total.`);
  if (chart) {
    chart.setActiveElements([{ datasetIndex: 0, index }]);
    chart.update('none');
  }
}

function renderChart(data) {
  const categories = data.categories;
  const canvas = document.querySelector('#emissions-chart');
  const zeroState = document.querySelector('#zero-chart');
  if (chart) { chart.destroy(); chart = null; }
  canvas.hidden = data.metrics.total_annual === 0;
  zeroState.hidden = data.metrics.total_annual !== 0;
  if (!canvas.hidden && typeof Chart !== 'undefined') {
    chart = new Chart(canvas, {
      type: 'pie',
      data: {
        labels: categories.map(row => row.label),
        datasets: [{ data: categories.map(row => row.emissions), backgroundColor: categories.map(row => row.color), borderColor: '#fffefa', borderWidth: 2, hoverOffset: 10 }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        animation: matchMedia('(prefers-reduced-motion: reduce)').matches ? false : { duration: 450 },
        layout: { padding: 12 },
        plugins: {
          legend: { display: false },
          tooltip: { padding: 12, backgroundColor: '#203b31', titleFont: { family: 'DM Sans' }, bodyFont: { family: 'DM Sans' }, callbacks: {
            label: context => {
              const row = categories[context.dataIndex];
              return `${format(row.emissions)} kg CO₂e/year (${share(row.percentage)})`;
            }
          } }
        },
        onClick: (_event, elements) => { if (elements.length) focusCategory(elements[0].index, categories); }
      }
    });
  } else if (typeof Chart === 'undefined' && data.metrics.total_annual > 0) {
    canvas.hidden = true;
    zeroState.hidden = false;
    zeroState.textContent = 'The chart could not load. All results are available in the breakdown below.';
  }
  const legend = document.querySelector('#chart-legend');
  legend.replaceChildren();
  categories.forEach((row, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'legend-button';
    button.setAttribute('aria-pressed', 'false');
    const dot = document.createElement('span');
    dot.className = 'color-dot';
    dot.style.backgroundColor = row.color;
    dot.setAttribute('aria-hidden', 'true');
    const label = document.createElement('span');
    label.textContent = row.label;
    const value = document.createElement('strong');
    value.textContent = share(row.percentage);
    button.append(dot, label, value);
    button.addEventListener('click', () => focusCategory(index, categories));
    legend.append(button);
  });
  const largest = data.largest_source;
  text('chart-insight', largest ? `${largest.label} is your largest source at ${share(largest.percentage)} of annual emissions. Try adjusting that input to compare a new scenario.` : 'All seven categories are zero. There is no emissions share to compare yet.');
}

function renderResults(data) {
  document.querySelector('#empty-results').hidden = true;
  resultContent.hidden = false;
  document.querySelector('#stale-notice').hidden = true;
  text('result-badge', 'Annual estimate');
  text('result-description', `${data.farm_name}${data.crop ? ` · ${data.crop}` : ''} · Based on the values you just entered.`);
  text('metric-total', format(data.metrics.total_annual));
  text('metric-production', format(data.metrics.annual_production));
  text('metric-pound', data.defined.per_pound ? format(data.metrics.per_pound) : 'N/A');
  text('metric-area', data.defined.per_sqft ? format(data.metrics.per_sqft) : 'N/A');
  text('metric-cycle', data.defined.per_cycle ? format(data.metrics.per_cycle) : 'N/A');
  text('metric-electricity', format(data.metrics.electricity_kwh));
  const body = document.querySelector('#breakdown-body');
  body.replaceChildren();
  data.categories.forEach(category => {
    const row = document.createElement('tr');
    const name = document.createElement('th');
    name.scope = 'row';
    const dot = document.createElement('span');
    dot.className = 'color-dot';
    dot.style.backgroundColor = category.color;
    dot.setAttribute('aria-hidden', 'true');
    name.append(dot, document.createTextNode(category.label));
    const amount = document.createElement('td');
    amount.textContent = format(category.emissions);
    const percentage = document.createElement('td');
    percentage.textContent = share(category.percentage);
    row.append(name, amount, percentage);
    body.append(row);
  });
  text('breakdown-total', format(data.metrics.total_annual));
  text('breakdown-share', data.metrics.total_annual > 0 ? '100%' : '0%');
  const warnings = document.querySelector('#result-warnings');
  warnings.replaceChildren();
  warnings.hidden = data.warnings.length === 0;
  data.warnings.forEach(warning => { const p = document.createElement('p'); p.textContent = warning; warnings.append(p); });
  renderChart(data);
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  clearErrors();
  if (requestController) requestController.abort();
  requestController = new AbortController();
  const version = ++requestVersion;
  const submittedEditVersion = editVersion;
  const payload = Object.fromEntries(new FormData(form));
  // Browsers expose malformed number input as empty; do not silently treat it as zero.
  const browserErrors = {};
  form.querySelectorAll('input[type="number"]').forEach(input => {
    if (input.validity.badInput) browserErrors[input.name] = 'Enter a valid number.';
  });
  if (Object.keys(browserErrors).length) { displayErrors('Please check the highlighted fields.', browserErrors); return; }
  calculateButton.disabled = true;
  calculateButton.textContent = 'Calculating…';
  form.setAttribute('aria-busy', 'true');
  const timer = setTimeout(() => requestController?.abort(), 30000);
  try {
    const response = await fetch('/api/calculate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal: requestController.signal });
    const data = await response.json();
    if (version !== requestVersion) return;
    if (!response.ok) { displayErrors(data.error || 'Please check your inputs.', data.errors || {}); return; }
    renderResults(data);
    if (submittedEditVersion !== editVersion) markChanged();
    resultSection.focus({ preventScroll: true });
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    text('form-status', 'Calculation complete. Your inputs are still here if you want to compare another scenario.');
  } catch (error) {
    if (version === requestVersion) displayErrors(error.name === 'AbortError' ? 'The calculation took too long. Please try again.' : 'The calculator could not connect. Your inputs are still here—please try again.');
  } finally {
    clearTimeout(timer);
    if (version === requestVersion) {
      calculateButton.disabled = false;
      calculateButton.innerHTML = 'Calculate My Footprint <span aria-hidden="true">↗</span>';
      form.removeAttribute('aria-busy');
    }
  }
});

form.addEventListener('reset', () => {
  requestVersion += 1;
  editVersion += 1;
  requestController?.abort();
  if (chart) { chart.destroy(); chart = null; }
  clearErrors();
  resultContent.hidden = true;
  document.querySelector('#empty-results').hidden = false;
  document.querySelector('#stale-notice').hidden = true;
  document.querySelector('#factor-panel').open = false;
  text('result-badge', 'Ready when you are');
  text('form-status', 'Form and results cleared. Blank emission factors use the spreadsheet defaults.');
  calculateButton.disabled = false;
  calculateButton.innerHTML = 'Calculate My Footprint <span aria-hidden="true">↗</span>';
  form.removeAttribute('aria-busy');
  // Reset event happens before the browser clears the controls.
  requestAnimationFrame(() => { document.querySelector('#farm_name').focus({ preventScroll: true }); document.querySelector('#farm').scrollIntoView({ behavior: 'smooth' }); });
});
