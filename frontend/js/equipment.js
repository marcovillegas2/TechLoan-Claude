const API_URL = "/api/v1/equipment/";

const form       = document.getElementById("equipment-form");
const feedback   = document.getElementById("form-feedback");
const submitBtn  = document.getElementById("submit-btn");

// ── Client-side validation ─────────────────────────────────────────────────

const RULES = {
  name:          { required: true, min: 2, label: "Nombre" },
  brand:         { required: true, min: 2, label: "Marca" },
  model:         { required: true, min: 1, label: "Modelo" },
  serial_number: { required: true, min: 3, noSpaces: true, label: "Número de serie" },
  category:      { required: true, label: "Categoría" },
};

function validateField(name, value) {
  const rule = RULES[name];
  if (!rule) return null;
  if (rule.required && !value.trim()) return `${rule.label} es obligatorio.`;
  if (rule.min && value.trim().length < rule.min)
    return `${rule.label} debe tener al menos ${rule.min} caracteres.`;
  if (rule.noSpaces && value.includes(" "))
    return `${rule.label} no puede contener espacios.`;
  return null;
}

function showFieldError(name, message) {
  const input = form.elements[name];
  const error = document.getElementById(`${name.replace("_number", "")}-error`) ||
                document.getElementById(`${name}-error`);
  if (!input || !error) return;
  if (message) {
    input.classList.add("is-invalid");
    error.textContent = message;
  } else {
    input.classList.remove("is-invalid");
    error.textContent = "";
  }
}

function validateAll() {
  let valid = true;
  for (const [name, rule] of Object.entries(RULES)) {
    const el = form.elements[name];
    if (!el) continue;
    const msg = validateField(name, el.value);
    const errorId = name === "serial_number" ? "serial-error" : `${name}-error`;
    const errorEl = document.getElementById(errorId);
    if (errorEl) errorEl.textContent = msg || "";
    if (msg) { el.classList.add("is-invalid"); valid = false; }
    else el.classList.remove("is-invalid");
  }
  return valid;
}

// Inline feedback as user types
Object.keys(RULES).forEach(name => {
  const el = form.elements[name];
  if (!el) return;
  el.addEventListener("input", () => {
    const msg = validateField(name, el.value);
    showFieldError(name, msg);
  });
});

// ── Form submit ────────────────────────────────────────────────────────────

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideFeedback();
  if (!validateAll()) return;

  setLoading(true);

  const body = {
    name:          form.elements["name"].value.trim(),
    brand:         form.elements["brand"].value.trim(),
    model:         form.elements["model"].value.trim(),
    serial_number: form.elements["serial_number"].value.trim(),
    category:      form.elements["category"].value,
    description:   form.elements["description"].value.trim() || null,
  };

  try {
    const res  = await fetch(API_URL, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(body),
    });
    const data = await res.json();

    if (res.status === 201) {
      showFeedback("success",
        `Equipo <strong>${data.name}</strong> registrado exitosamente (ID: ${data.id}).`);
      form.reset();
      form.querySelectorAll(".is-invalid").forEach(el => el.classList.remove("is-invalid"));
    } else {
      const msg = data.detail || "Error al registrar el equipo.";
      showFeedback("error", msg);
    }
  } catch {
    showFeedback("error", "No se pudo conectar con el servidor. Intente nuevamente.");
  } finally {
    setLoading(false);
  }
});

// ── Helpers ────────────────────────────────────────────────────────────────

function setLoading(on) {
  submitBtn.disabled = on;
  submitBtn.classList.toggle("is-loading", on);
}

function showFeedback(type, html) {
  feedback.className = `feedback is-${type}`;
  feedback.innerHTML = html;
  feedback.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function hideFeedback() {
  feedback.className = "feedback";
  feedback.innerHTML = "";
}