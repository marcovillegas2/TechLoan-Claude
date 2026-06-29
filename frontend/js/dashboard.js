/* ── TechLoan — Dashboard Administrativo ─────────────────────────────────── */

const API = 'http://localhost:8000';
const $ = id => document.getElementById(id);

/* ── Colors ──────────────────────────────────────────────────────────────── */
const COLORS = {
  navy:  '#1E3A8A',
  blue:  '#3B82F6',
  sky:   '#93C5FD',
  green: '#16A34A',
  amber: '#D97706',
  red:   '#DC2626',
  gray:  '#9CA3AF',
};

/* ── Fetch helper ────────────────────────────────────────────────────────── */
async function apiFetch(path) {
  const resp = await fetch(`${API}${path}`);
  if (!resp.ok) throw new Error(`Error ${resp.status} en ${path}`);
  return resp.json();
}

/* ── Render summary cards ────────────────────────────────────────────────── */
function renderSummary(data) {
  $('cTotal').textContent  = data.total_equipment  ?? 0;
  $('cAvail').textContent  = data.available_equipment ?? 0;
  $('cLoaned').textContent = data.loaned_equipment ?? 0;
  $('cOverdue').textContent= data.overdue_loans    ?? 0;
}

/* ── Donut chart (equipment) ─────────────────────────────────────────────── */
function drawDonut(canvasId, legendId, segments) {
  const canvas = $(canvasId);
  const ctx    = canvas.getContext('2d');
  const W = canvas.width;
  const H = canvas.height;
  const cx = W / 2, cy = H / 2;
  const R = Math.min(W, H) / 2 - 16;
  const r = R * 0.55;

  ctx.clearRect(0, 0, W, H);

  const total = segments.reduce((s, seg) => s + seg.value, 0);

  if (total === 0) {
    // Empty state
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.strokeStyle = '#E5E7EB';
    ctx.lineWidth = R - r;
    ctx.stroke();

    ctx.fillStyle = '#9CA3AF';
    ctx.font = 'bold 13px Segoe UI, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Sin datos', cx, cy);

    $(legendId).innerHTML = segments.map(seg => `
      <div class="legend-item">
        <span class="legend-dot" style="background:${seg.color}"></span>
        <span class="legend-label">${seg.label}</span>
        <span class="legend-val">0</span>
      </div>`).join('');
    return;
  }

  let angle = -Math.PI / 2;
  segments.forEach(seg => {
    if (!seg.value) return;
    const slice = (seg.value / total) * Math.PI * 2;

    // Arc (thick)
    ctx.beginPath();
    ctx.arc(cx, cy, R, angle, angle + slice);
    ctx.arc(cx, cy, r, angle + slice, angle, true);
    ctx.closePath();
    ctx.fillStyle = seg.color;
    ctx.fill();

    // Small gap
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, R + 1, angle, angle);
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();

    angle += slice;
  });

  // Center text
  ctx.fillStyle = '#1F2937';
  ctx.font = `bold 20px Segoe UI, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(total, cx, cy - 8);
  ctx.fillStyle = '#6B7280';
  ctx.font = `11px Segoe UI, sans-serif`;
  ctx.fillText('total', cx, cy + 10);

  // Legend
  $(legendId).innerHTML = segments.map(seg => `
    <div class="legend-item">
      <span class="legend-dot" style="background:${seg.color}"></span>
      <span class="legend-label">${seg.label}</span>
      <span class="legend-val">${seg.value}</span>
    </div>`).join('');
}

/* ── Bar chart (loans by status) ─────────────────────────────────────────── */
function drawBars(canvasId, legendId, bars) {
  const canvas = $(canvasId);
  const ctx    = canvas.getContext('2d');
  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const maxVal = Math.max(...bars.map(b => b.value), 1);
  const padL = 16, padR = 16, padT = 20, padB = 40;
  const chartW = W - padL - padR;
  const chartH = H - padT - padB;
  const barW   = Math.floor(chartW / bars.length) - 12;
  const gap    = (chartW - bars.length * barW) / (bars.length + 1);

  bars.forEach((bar, i) => {
    const x  = padL + gap + i * (barW + gap);
    const bh = bar.value > 0 ? Math.max((bar.value / maxVal) * chartH, 6) : 0;
    const y  = padT + chartH - bh;

    // Bar
    ctx.fillStyle = bar.color;
    ctx.beginPath();
    ctx.roundRect(x, y, barW, bh, [4, 4, 0, 0]);
    ctx.fill();

    // Value above bar
    if (bar.value > 0) {
      ctx.fillStyle = '#1F2937';
      ctx.font = 'bold 13px Segoe UI, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(bar.value, x + barW / 2, y - 3);
    }

    // Label below
    ctx.fillStyle = '#6B7280';
    ctx.font = '11px Segoe UI, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(bar.label, x + barW / 2, padT + chartH + 8);
  });

  // Baseline
  ctx.strokeStyle = '#E5E7EB';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padL, padT + chartH);
  ctx.lineTo(padL + chartW, padT + chartH);
  ctx.stroke();

  // Legend
  $(legendId).innerHTML = bars.map(bar => `
    <div class="legend-item">
      <span class="legend-dot" style="background:${bar.color}"></span>
      <span class="legend-label">${bar.label}</span>
      <span class="legend-val">${bar.value}</span>
    </div>`).join('');
}

/* ── Render charts ───────────────────────────────────────────────────────── */
function renderCharts(data) {
  const eq = data.equipment_by_status  || {};
  const ln = data.loans_by_status      || {};

  drawDonut('chartEquip', 'legendEquip', [
    { label: 'Disponibles', value: eq.DISPONIBLE || 0, color: COLORS.green },
    { label: 'Prestados',   value: eq.PRESTADO   || 0, color: COLORS.amber },
  ]);

  drawBars('chartLoans', 'legendLoans', [
    { label: 'Activos',   value: ln.ACTIVO   || 0, color: COLORS.blue  },
    { label: 'Devueltos', value: ln.DEVUELTO || 0, color: COLORS.green },
    { label: 'Vencidos',  value: ln.VENCIDO  || 0, color: COLORS.red   },
  ]);
}

/* ── Render overdue table ────────────────────────────────────────────────── */
function renderOverdueTable(users) {
  const tbody = $('overdueBody');
  $('overdueCount').textContent = users.length
    ? `${users.length} usuario${users.length !== 1 ? 's' : ''}`
    : '0 usuarios';

  if (!users.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-cell">No existen usuarios con devoluciones vencidas.</td></tr>';
    return;
  }

  tbody.innerHTML = users.map(u => {
    const [y, m, d] = u.due_date.split('-');
    const fmtDate   = `${d}/${m}/${y}`;
    return `
      <tr>
        <td><strong>${u.borrower_full_name}</strong></td>
        <td>${u.borrower_dni}</td>
        <td>${u.equipment_name}</td>
        <td>${fmtDate}</td>
        <td><span class="days-badge">${u.days_overdue} día${u.days_overdue !== 1 ? 's' : ''}</span></td>
        <td><span class="badge badge-vencido">VENCIDO</span></td>
      </tr>`;
  }).join('');
}

/* ── Load all ────────────────────────────────────────────────────────────── */
async function loadAll() {
  const btn = $('refreshBtn');
  btn.disabled = true;
  btn.textContent = '↻ Actualizando…';

  // Reset cards to loading state
  ['cTotal','cAvail','cLoaned','cOverdue'].forEach(id => { $(id).textContent = '—'; });

  try {
    const [summary, charts, overdue] = await Promise.all([
      apiFetch('/dashboard/summary'),
      apiFetch('/dashboard/charts'),
      apiFetch('/dashboard/overdue-users'),
    ]);
    renderSummary(summary);
    renderCharts(charts);
    renderOverdueTable(overdue);
  } catch (e) {
    // Graceful degradation: show zeros on error
    renderSummary({ total_equipment: 0, available_equipment: 0, loaned_equipment: 0, overdue_loans: 0 });
    renderCharts({ equipment_by_status: {}, loans_by_status: {} });
    renderOverdueTable([]);
    console.error('Dashboard error:', e);
  } finally {
    btn.disabled = false;
    btn.textContent = '↻ Actualizar';
  }
}

/* ── Init ────────────────────────────────────────────────────────────────── */
loadAll();
