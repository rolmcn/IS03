document.addEventListener("DOMContentLoaded", () => {

  // ---------------- ELEMENTAI ----------------

  const form = document.querySelector("#payer-form");
  const submitBtn = document.querySelector("#submit-button");
  const msgEl = document.querySelector("#status-message-text");

  const payerType = document.querySelector("#payer_type");
  const vatStatus = document.querySelector("#vat_status");

  const fullNameInput = document.querySelector("#full_name");
  const fullNameSymbol = fullNameInput.parentElement.querySelector(".update-disabled-symbol");

  const identificationInput = document.querySelector("#identification_code");
  const vatCodeInput = document.querySelector("#vat_code");

  const mobileInput = document.querySelector("#mobile_phone");
  const emailInput = document.querySelector("#email");

  const countryInput = document.querySelector("#country");

  // ---------------- GLOBAL ----------------

  const state = {
    mode: null, // pending | editing | success
    hasErrors: false,
    hasEmptyRequired: true,
    hasChanges: false
  };

  let currentUser = window.currentUser || {};
  let backendFieldErrors = window.fieldErrors || {};
  let scenario = window.scenario;

  let initialSnapshot = {};

  // 🔥 NEW: auto-fill flag
  let autoFilled = false;

  // 🔥 NEW: success timeout
  let successTimeout = null;

  // ---------------- HELPERS ----------------

  function showMessage(text, type) {
    msgEl.textContent = text || "";
    msgEl.className = type || "";

    // clear previous timeout
    if (successTimeout) {
      clearTimeout(successTimeout);
      successTimeout = null;
    }

    // auto hide success
    if (type === "status-success") {
      successTimeout = setTimeout(() => {
        msgEl.textContent = "";
        msgEl.className = "";
      }, 5000);
    }
  }

  function disableSubmit() { submitBtn.disabled = true; }
  function enableSubmit() { submitBtn.disabled = false; }

  function isHidden(el) {
    return el.offsetParent === null;
  }

  function normalizeValue(val) {
    return (val ?? "")
      .toString()
      .trim()
      .replace(/\s+/g, " ");
  }

  function getRequiredInputs() {
    return [...form.querySelectorAll(".required-field")]
      .map(label => document.getElementById(label.getAttribute("for")))
      .filter(el => el && !isHidden(el));
  }

  function hasEmptyRequired() {
    return getRequiredInputs().some(input => !normalizeValue(input.value));
  }

  function buildSnapshot() {
    const snap = {};
    [...form.elements].forEach(el => {
      if (el.name) {
        snap[el.name] = normalizeValue(el.value);
      }
    });
    return snap;
  }

  function hasFormChanged() {
    return [...form.elements].some(el => {
      if (!el.name) return false;

      const current = normalizeValue(el.value);
      const initial = normalizeValue(initialSnapshot[el.name]);

      return current !== initial;
    });
  }

  // ---------------- FIELD ERRORS ----------------

  function clearFieldErrorsUI() {
    document.querySelectorAll(".field-error").forEach(el => el.remove());
  }

  function renderFieldErrors() {
    clearFieldErrorsUI();

    Object.keys(backendFieldErrors).forEach(field => {
      const wrapper = document.querySelector(`#${field}`)?.closest(".form-field");
      if (!wrapper) return;

      const err = document.createElement("span");
      err.className = "field-error";
      err.textContent = backendFieldErrors[field];
      wrapper.appendChild(err);
    });
  }

  // ---------------- UI LOGIKA ----------------

  function applyVisibility() {
    if (payerType.value === "legal") {
      identificationInput.closest(".form-field").style.display = "";
    } else {
      identificationInput.closest(".form-field").style.display = "none";
      identificationInput.value = "";
    }

    if (vatStatus.value === "yes") {
      vatCodeInput.closest(".form-field").style.display = "";
    } else {
      vatCodeInput.closest(".form-field").style.display = "none";
      vatCodeInput.value = "";
    }
  }

  function applyFullNameLogic() {
    if (payerType.value === "physical") {

      // 🔥 auto-fill tik vieną kartą
      if (!autoFilled) {

        if (!fullNameInput.value) {
          fullNameInput.value =
            `${currentUser.first_name || ""} ${currentUser.last_name || ""}`.trim();
        }

        if (!mobileInput.value && currentUser.mobile_phone) {
          mobileInput.value = currentUser.mobile_phone;
        }

        if (!emailInput.value && currentUser.email) {
          emailInput.value = currentUser.email;
        }

        autoFilled = true;
      }

      fullNameInput.readOnly = true;
      fullNameSymbol.style.display = "";

    } else {
      fullNameInput.readOnly = false;
      fullNameSymbol.style.display = "none";

      autoFilled = false; // reset
    }
  }

  // ---------------- STATE ----------------

  function syncState() {
    state.hasEmptyRequired = hasEmptyRequired();
    state.hasChanges = hasFormChanged();
    state.hasErrors = Object.keys(backendFieldErrors).length > 0;
  }

  // ---------------- SCENARIJAI ----------------

  const scenarios = {

    pending() {
      showMessage("Užpildykite privalomus formos laukus", "status-attention");
      disableSubmit();

      fullNameInput.readOnly = false;
      fullNameSymbol.style.display = "none";
    },

    editing() {

      if (state.hasErrors) {
        showMessage("Ištaisykite formos pildymo klaidas", "status-error");
        disableSubmit();
        return;
      }

      if (state.hasEmptyRequired) {
        showMessage("Užpildykite privalomus formos laukus", "status-attention");
        disableSubmit();
        return;
      }

      if (state.hasChanges) {
        showMessage("Išsaugokite pakeitimus", "status-attention");
        enableSubmit();
        return;
      }

      showMessage("", "");
      disableSubmit();
    },

    success() {
      showMessage("Sėkmingai išsaugota", "status-success");
      disableSubmit();
    }
  };

  // ---------------- RENDER ----------------

  function render() {
    applyVisibility();
    applyFullNameLogic();
    renderFieldErrors();

    scenarios[state.mode]?.();
  }

  // ---------------- RESET ----------------

  function resetForm(newType) {
    const countryVal = countryInput.value;

    form.querySelectorAll("input, select").forEach(el => {
      if (el.id !== "payer_type" && el.id !== "country") {
        el.value = "";
      }
    });

    payerType.value = newType;
    countryInput.value = countryVal;

    backendFieldErrors = {};
    initialSnapshot = buildSnapshot();
    autoFilled = false; // 🔥 svarbu reset

    syncState();
    render();
  }

  // ---------------- EVENTS ----------------

  payerType.addEventListener("change", e => {
    resetForm(e.target.value);
  });

  vatStatus.addEventListener("change", () => {
    syncState();
    render();
  });

  form.addEventListener("input", (e) => {
    const field = e.target.name;

    if (backendFieldErrors[field]) {
      delete backendFieldErrors[field];
    }

    syncState();
    state.mode = "editing";
    render();
  });

  form.addEventListener("submit", async e => {
    e.preventDefault();

    const formData = new FormData(form);
    const res = await fetch(form.action, { method: "POST", body: formData });
    const data = await res.json();

    backendFieldErrors = data.field_errors || {};

    if (data.form_data) {
      Object.keys(data.form_data).forEach(key => {
        const el = document.querySelector(`[name="${key}"]`);
        if (el) el.value = data.form_data[key];
      });

      initialSnapshot = buildSnapshot();
    }

    syncState();

    if (Object.keys(backendFieldErrors).length > 0) {
      state.mode = "editing";
    } else if (data.scenario === "success") {
      state.mode = "success";
      initialSnapshot = buildSnapshot();
    }

    render();
  });

  // ---------------- INIT ----------------

  function init() {
    if (scenario === "pending") {
      state.mode = "pending";
    } else {
      state.mode = "editing";
    }

    initialSnapshot = buildSnapshot();

    syncState();
    render();
  }

  init();
});