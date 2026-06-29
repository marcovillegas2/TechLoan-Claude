/* ── TechLoan — Gestión de Préstamos ─────────────────────────────────────── */

const API = 'http://localhost:8000';
let borrowersCache = [];
let foundBorrowerId = null;
let returningLoanId = null;

const $ = id => document.getElementById(id);

/* ── Toast ───────────────────────────────────────────────────────────────── */
function toast(msg, type = 'success') {
  const el = $('toast');
  el.textContent = msg;
  el.className = `toast toast-${type}`;
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.className = 'toast hidden'; }, 3800);
}

/* ── Fetch helper ────────────────────────────────────────────────────────── */
async function apiFetch(path, opts = {}) {
  const resp = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Error del servidor' }));
    throw new Error(err.detail || `Error ${resp.status}`);
  }
  if (resp.status === 204) return null;
  return resp.json();
}

/* ── Status helpers ──────────────────────────────────────────────────────── */
function loanBadge(status) {
  const cls = { ACTIVO: 'badge-activo', DEVUELTO: 'badge-devuelto', VENCIDO: 'badge-vencido' }[status] || 'badge-activo';
  return `<span class="badge ${cls}">${status}</span>`;
}

function isOverdue(loan) {
  if (loan.return_date) return false;
  return new Date(loan.due_date) < new Date();
}

function fmt(dateStr) {
  if (!dateStr) return '—';
  const [y, m, d] = dateStr.split('-');
  return `${d}/${m}/${y}`;
}

/* ── Load data ───────────────────────────────────────────────────────────── */
async function loadAll() {
  try {
    const [loans, avail, borrowers] = await Promise.all([
      apiFetch('/loans/'),
      apiFetch('/loans/available-equipment'),
      apiFetch('/borrowers/')
    ]);
    borrowersCache = borrowers;
    populateEquipmentSelect(avail);
    renderLoanTable(loans, borrowers);
  } catch (e) {
    toast('Error al cargar datos: ' + e.message, 'error');
    renderLoanTable([], []);
  }
}

function populateEquipmentSelect(available) {
  const sel = $('lEquip');
  sel.innerHTML = '<option value="">— Seleccionar equipo —</option>';
  if (!available.length) {
    sel.innerHTML += '<option disabled>No hay equipos disponibles</option>';
    return;
  }
  available.forEach(eq => {
    sel.innerHTML += `<option value="${eq.id}">${eq.code} — ${eq.name} (${eq.category})</option>`;
  });
}

function renderLoanTable(loans, borrowers) {
  const tbody = $('loanBody');
  $('loanCount').textContent = `${loans.length} préstamo${loans.length !== 1 ? 's' : ''}`;

  if (!loans.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-cell">No hay préstamos registrados.</td></tr>';
    return;
  }

  const bMap = {};
  borrowers.forEach(b => { bMap[b.id] = b; });

  tbody.innerHTML = loans.map(loan => {
    const b = bMap[loan.borrower_id] || {};
    const overdue = isOverdue(loan);
    const canReturn = loan.status === 'ACTIVO';
    const rowClass = overdue ? 'overdue-row' : '';
    return `
      <tr class="${rowClass}">
        <td>${loan.equipment_id}</td>
        <td>${b.full_name || '—'}</td>
        <td>${b.dni || '—'}</td>
        <td>${fmt(loan.loan_date)}</td>
        <td>${fmt(loan.due_date)}</td>
        <td>${loanBadge(overdue && canReturn ? 'VENCIDO' : loan.status)}</td>
        <td>
          <button class="btn-return" onclick="askReturn(${loan.id})" ${canReturn ? '' : 'disabled'}>
            ${canReturn ? 'Devolver' : 'Cerrado'}
          </button>
        </td>
      </tr>`;
  }).join('');
}

/* ── Borrower lookup ─────────────────────────────────────────────────────── */
$('btnLookup').onclick = () => {
  const dni = $('bDni').value.trim();
  if (!dni) { $('errDni').textContent = 'Ingrese un DNI para buscar.'; return; }
  $('errDni').textContent = '';
  const found = borrowersCache.find(b => b.dni === dni);
  const hint  = $('lookupHint');

  if (found) {
    foundBorrowerId = found.id;
    $('bFullName').value = found.full_name;
    $('bEmail').value    = found.email;
    $('bPhone').value    = found.phone;
    $('bDept').value     = found.department;
    hint.textContent = `✓ Solicitante encontrado — se usará el registro existente.`;
    hint.className   = 'lookup-hint hint-found';
    ['bFullName','bEmail','bPhone','bDept'].forEach(id => { $(id).readOnly = true; $(id).style.background = '#f8fafc'; });
  } else {
    foundBorrowerId = null;
    ['bFullName','bEmail','bPhone','bDept'].forEach(id => { $(id).readOnly = false; $(id).style.background = ''; $(id).value = ''; });
    hint.textContent = '⚠ DNI no encontrado — complete los datos para crear un nuevo solicitante.';
    hint.className   = 'lookup-hint hint-new';
  }
};

/* ── Form validation ─────────────────────────────────────────────────────── */
function clearErrors() {
  ['errDni','errFullName','errEmail','errPhone','errDept','errEquip','errLoanDate','errDueDate']
    .forEach(id => { $(id).textContent = ''; });
}

function validateLoanForm() {
  clearErrors();
  let ok = true;
  if (!$('bDni').value.trim())      { $('errDni').textContent = 'DNI obligatorio.'; ok = false; }
  if (!foundBorrowerId) {
    if (!$('bFullName').value.trim()){ $('errFullName').textContent = 'Nombre obligatorio.'; ok = false; }
    if (!$('bEmail').value.trim())   { $('errEmail').textContent = 'Correo obligatorio.'; ok = false; }
    if (!$('bPhone').value.trim())   { $('errPhone').textContent = 'Teléfono obligatorio.'; ok = false; }
    if (!$('bDept').value.trim())    { $('errDept').textContent = 'Área obligatoria.'; ok = false; }
  }
  if (!$('lEquip').value)           { $('errEquip').textContent = 'Seleccione un equipo.'; ok = false; }
  if (!$('lLoanDate').value)        { $('errLoanDate').textContent = 'Fecha obligatoria.'; ok = false; }
  if (!$('lDueDate').value)         { $('errDueDate').textContent = 'Fecha obligatoria.'; ok = false; }
  if ($('lLoanDate').value && $('lDueDate').value) {
    if ($('lDueDate').value <= $('lLoanDate').value) {
      $('errDueDate').textContent = 'La fecha límite debe ser posterior a la fecha de préstamo.';
      ok = false;
    }
  }
  return ok;
}

/* ── Form submit ─────────────────────────────────────────────────────────── */
$('loanForm').onsubmit = async e => {
  e.preventDefault();
  if (!validateLoanForm()) return;

  const btn = $('submitLoan');
  btn.disabled = true;
  btn.textContent = 'Procesando…';

  try {
    let borrowerId = foundBorrowerId;

    if (!borrowerId) {
      const newBorrower = await apiFetch('/borrowers/', {
        method: 'POST',
        body: JSON.stringify({
          dni:        $('bDni').value.trim(),
          full_name:  $('bFullName').value.trim(),
          email:      $('bEmail').value.trim(),
          phone:      $('bPhone').value.trim(),
          department: $('bDept').value.trim(),
        })
      });
      borrowerId = newBorrower.id;
    }

    await apiFetch('/loans/', {
      method: 'POST',
      body: JSON.stringify({
        equipment_id: parseInt($('lEquip').value),
        borrower_id:  borrowerId,
        loan_date:    $('lLoanDate').value,
        due_date:     $('lDueDate').value,
        status:       'ACTIVO',
      })
    });

    toast('Préstamo registrado correctamente');
    resetForm();
    loadAll();
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Registrar préstamo';
  }
};

function resetForm() {
  $('loanForm').reset();
  foundBorrowerId = null;
  $('lookupHint').textContent = '';
  $('lookupHint').className = 'lookup-hint';
  ['bFullName','bEmail','bPhone','bDept'].forEach(id => {
    $(id).readOnly = false; $(id).style.background = '';
  });
  clearErrors();
}

$('btnClearLoan').onclick = resetForm;

/* ── Return ──────────────────────────────────────────────────────────────── */
function askReturn(loanId) {
  returningLoanId = loanId;
  $('returnOverlay').classList.remove('hidden');
}

$('btnCancelReturn').onclick = () => {
  $('returnOverlay').classList.add('hidden');
  returningLoanId = null;
};

$('btnConfirmReturn').onclick = async () => {
  $('returnOverlay').classList.add('hidden');
  try {
    await apiFetch(`/loans/${returningLoanId}/return`, { method: 'POST' });
    toast('Devolución registrada correctamente');
    loadAll();
  } catch (e) {
    toast(e.message, 'error');
  }
  returningLoanId = null;
};

/* ── Set default dates ───────────────────────────────────────────────────── */
function setDefaultDates() {
  const today = new Date().toISOString().split('T')[0];
  const nextWeek = new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0];
  $('lLoanDate').value = today;
  $('lDueDate').value  = nextWeek;
}

/* ── Init ────────────────────────────────────────────────────────────────── */
setDefaultDates();
loadAll();
