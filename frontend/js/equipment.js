/* ── TechLoan — Gestión de Equipos ───────────────────────────────────────── */

const API = 'http://localhost:8000';
let editingId = null;
let deletingId = null;

/* ── Utility ─────────────────────────────────────────────────────────────── */
const $ = id => document.getElementById(id);

function toast(msg, type = 'success') {
  const el = $('toast');
  el.textContent = msg;
  el.className = `toast toast-${type}`;
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.className = 'toast hidden'; }, 3500);
}

function statusBadge(status) {
  const cls = status === 'DISPONIBLE' ? 'badge-disponible' : 'badge-prestado';
  return `<span class="badge ${cls}">${status}</span>`;
}

/* ── Fetch helpers ───────────────────────────────────────────────────────── */
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

/* ── Load equipment list ─────────────────────────────────────────────────── */
async function loadEquipment() {
  try {
    const data = await apiFetch('/equipment/');
    renderTable(data);
  } catch (e) {
    renderTable([]);
    toast('No se pudo cargar la lista de equipos', 'error');
  }
}

function renderTable(list) {
  const tbody = $('eqBody');
  $('eqCount').textContent = `${list.length} equipo${list.length !== 1 ? 's' : ''}`;

  if (!list.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty-cell">No hay equipos registrados.</td></tr>';
    return;
  }

  tbody.innerHTML = list.map(eq => `
    <tr data-id="${eq.id}">
      <td><strong>${eq.code}</strong></td>
      <td>${eq.name}</td>
      <td>${eq.category}</td>
      <td>${statusBadge(eq.status)}</td>
      <td class="actions-cell">
        <button class="btn-icon btn-edit" onclick="startEdit(${eq.id})" title="Editar">✏️</button>
        <button class="btn-icon btn-del"  onclick="askDelete(${eq.id})" title="Eliminar">🗑️</button>
      </td>
    </tr>
  `).join('');
}

/* ── Form helpers ────────────────────────────────────────────────────────── */
function clearErrors() {
  ['errCode','errName','errCategory'].forEach(id => { $(id).textContent = ''; });
}

function validateForm() {
  clearErrors();
  let ok = true;
  if (!$('fCode').value.trim())     { $('errCode').textContent = 'El código es obligatorio.'; ok = false; }
  if (!$('fName').value.trim())     { $('errName').textContent = 'El nombre es obligatorio.'; ok = false; }
  if (!$('fCategory').value.trim()) { $('errCategory').textContent = 'La categoría es obligatoria.'; ok = false; }
  return ok;
}

function getFormData() {
  return {
    code:        $('fCode').value.trim(),
    name:        $('fName').value.trim(),
    category:    $('fCategory').value.trim(),
    description: $('fDesc').value.trim() || null,
    status:      $('fStatus').value,
  };
}

function resetForm() {
  $('equipmentForm').reset();
  $('equipmentId').value = '';
  editingId = null;
  $('formTitle').textContent = 'Registrar Equipo';
  $('submitBtn').textContent = 'Registrar';
  clearErrors();
}

/* ── Edit ─────────────────────────────────────────────────────────────────── */
async function startEdit(id) {
  try {
    const eq = await apiFetch(`/equipment/${id}`);
    editingId = id;
    $('equipmentId').value = id;
    $('fCode').value     = eq.code;
    $('fName').value     = eq.name;
    $('fCategory').value = eq.category;
    $('fDesc').value     = eq.description || '';
    $('fStatus').value   = eq.status;
    $('formTitle').textContent = 'Actualizar Equipo';
    $('submitBtn').textContent = 'Actualizar';
    clearErrors();
    $('fCode').focus();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } catch (e) {
    toast('No se pudo cargar el equipo', 'error');
  }
}

/* ── Delete ──────────────────────────────────────────────────────────────── */
function askDelete(id) {
  deletingId = id;
  $('overlay').classList.remove('hidden');
}

$('btnCancelDel').onclick = () => {
  $('overlay').classList.add('hidden');
  deletingId = null;
};

$('btnConfirmDel').onclick = async () => {
  $('overlay').classList.add('hidden');
  try {
    await apiFetch(`/equipment/${deletingId}`, { method: 'DELETE' });
    toast('Equipo eliminado correctamente');
    loadEquipment();
  } catch (e) {
    toast(e.message, 'error');
  }
  deletingId = null;
};

/* ── Form submit ─────────────────────────────────────────────────────────── */
$('equipmentForm').onsubmit = async e => {
  e.preventDefault();
  if (!validateForm()) return;

  const data = getFormData();
  const btn = $('submitBtn');
  btn.disabled = true;
  btn.textContent = editingId ? 'Actualizando…' : 'Registrando…';

  try {
    if (editingId) {
      await apiFetch(`/equipment/${editingId}`, { method: 'PUT', body: JSON.stringify(data) });
      toast('Equipo actualizado correctamente');
    } else {
      await apiFetch('/equipment/', { method: 'POST', body: JSON.stringify(data) });
      toast('Equipo registrado correctamente');
    }
    resetForm();
    loadEquipment();
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = editingId ? 'Actualizar' : 'Registrar';
  }
};

$('cancelBtn').onclick = resetForm;

/* ── Init ────────────────────────────────────────────────────────────────── */
loadEquipment();
