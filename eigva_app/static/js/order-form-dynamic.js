document.addEventListener("DOMContentLoaded", () => {

  // ---------------- ELEMENTAI ----------------

  const form = document.querySelector("#order-form");
  const submitBtn = document.querySelector("#order-submit-button");

  const msgEl = document.querySelector("#order-message");
  const summaryEl = document.querySelector("#order-summary");
  const amountErrorEl = document.querySelector("#financial-amount-error");

  const qtyEl = document.querySelector("#licenses-quantity");
  const durEl = document.querySelector("#licenses-duration");
  const opEl = document.querySelector("#financial_operation_type");
  const amountEl = document.querySelector("#financial_amount");
  const accEl = document.querySelector("#refund_bank_account");
  const termsEl = document.querySelector("#terms-agree");

  const accWrapper = document
    .querySelector("label[for='refund_bank_account']")
    ?.closest(".form-field");

  const qtyGroup = qtyEl.closest(".control-group");
  const durGroup = durEl.closest(".control-group");

  const labels = {
    qty: document.querySelector('label[for="licenses-quantity"]'),
    dur: document.querySelector('label[for="licenses-duration"]'),
    op: document.querySelector('label[for="financial_operation_type"]'),
    amount: document.querySelector('label[for="financial_amount"]'),
    acc: document.querySelector('label[for="refund_bank_account"]'),
    terms: termsEl.closest("label")
  };

  // ---------------- GLOBAL ----------------

  const LICENSE_PRICING = window.LICENSE_PRICING || {
    base_price: 20,
    min_price: 10,
    step: 1
  };

  const sms_balance_eur = window.sms_balance_eur ?? 0;
  const vat_rate = (window.vat_rate_pct ?? 21) / 100 + 1;

  const state = {
    mode: "editing",
    scenario: "empty",
    hasErrors: false,
    hasEmptyRequired: true,
    isValid: false
  };

  let lastOpValue = opEl.value;

  // ---------------- HELPERS ----------------

  const n = v => parseFloat((v || "").toString().replace(",", ".")) || 0;
  const f = v => Number(v || 0).toFixed(2);

  function showMessage(text) {
    msgEl.textContent = text || "";
  }

  function disableSubmit() { submitBtn.disabled = true; }
  function enableSubmit() { submitBtn.disabled = false; }

  function setRequired(label, isRequired) {
    if (!label) return;
    label.classList.toggle("required-field", isRequired);
  }

  function setFieldLocked(el, locked) {
    if (!el) return;

    el.disabled = locked;
    if (locked) el.value = 0;

    const group = el.closest(".control-group");
    if (!group) return;

    group.querySelectorAll("button").forEach(btn => {
      btn.disabled = locked;
      btn.style.pointerEvents = locked ? "none" : "";
      btn.style.opacity = locked ? "0.4" : "";
    });

    const icon = group.querySelector(".update-disabled-symbol");
    if (icon) icon.classList.toggle("is-hidden", !locked);
  }

  // ---------------- STEPPERS FIX ----------------

  function updateSteppers() {
    const qty = qtyEl.valueAsNumber ?? 0;
    const dur = durEl.valueAsNumber ?? 0;

    const qtyMin = Number(qtyEl.min ?? 0);
    const qtyMax = Number(qtyEl.max ?? 100);

    const durMin = Number(durEl.min ?? 0);
    const durMax = Number(durEl.max ?? 12);

    const qtyMinus = document.querySelector("#decrease-licenses");
    const qtyPlus = document.querySelector("#increase-licenses");

    const durMinus = document.querySelector("#decrease-months");
    const durPlus = document.querySelector("#increase-months");

    // qty 0–100
    if (qtyMinus) qtyMinus.disabled = qty <= qtyMin;
    if (qtyPlus) qtyPlus.disabled = qty >= qtyMax;

    // dur 0–12
    if (durMinus) durMinus.disabled = dur <= durMin;
    if (durPlus) durPlus.disabled = dur >= durMax;
  }

  // ---------------- SKAIČIAVIMAI ----------------

  function license_price(nVal) {
    return Math.max(
      (LICENSE_PRICING.base_price + 1) - nVal,
      LICENSE_PRICING.min_price
    );
  }

  function calcA(qty, dur) {
    if (qty <= 0 || dur <= 0) return 0;
    return license_price(qty) * qty * dur * vat_rate;
  }

  function calcB(A, qty, dur) {
    if (!qty || !dur) return 0;
    return (A / qty) / dur;
  }

  // ---------------- SCENARIJUS ----------------

  function detectScenario() {
    const qty = n(qtyEl.value);
    const dur = n(durEl.value);
    const op = opEl.value;
    const amount = n(amountEl.value);

    if (!qty && !dur && !op && !amount) return "empty";
    if (op === "credit") return "credit";
    if (op === "return") return "return";
    if ((op === "add" || amount > 0) && !qty && !dur) return "sms_add";
    if ((qty > 0 || dur > 0) && !op && !amount) return "licenses_only";
    if ((qty > 0 || dur > 0) && op === "add") return "licenses_plus_sms";

    return "mixed";
  }

  // ---------------- VALIDATION ----------------

  function validate() {
    const s = state.scenario;
    const qty = n(qtyEl.value);
    const dur = n(durEl.value);
    const amount = n(amountEl.value);
    const A = calcA(qty, dur);

    amountErrorEl.textContent = "";

    if (s === "credit") {
      if (amount > A) {
        amountErrorEl.textContent =
          "Užskaitos suma negali būti didesnė už perkamų licencijų sumą";
        return false;
      }
      if (amount > sms_balance_eur) {
        amountErrorEl.textContent =
          "Užskaitos suma negali būti didesnė už įskaitytą SMS lėšų sumą";
        return false;
      }
    }

    if (s === "return") {
      if (amount > sms_balance_eur) {
        amountErrorEl.textContent =
          "Grąžinama suma negali būti didesnė už įskaitytą SMS lėšų sumą";
        return false;
      }
    }

    return true;
  }

  function requiredFilled() {
    const s = state.scenario;
    const qty = n(qtyEl.value);
    const dur = n(durEl.value);
    const amount = n(amountEl.value);
    const op = opEl.value;

    if (s === "empty") return false;

    if (s === "licenses_only")
      return qty > 0 && dur > 0 && termsEl.checked;

    if (s === "sms_add")
      return op === "add" && amount > 0 && termsEl.checked;

    if (s === "credit")
      return qty > 0 && dur > 0 && op === "credit" && amount > 0 && termsEl.checked;

    if (s === "return")
      return op === "return" && amount > 0 && termsEl.checked;

    if (s === "licenses_plus_sms")
      return qty > 0 && dur > 0 && op === "add" && amount > 0 && termsEl.checked;

    return false;
  }

  // ---------------- REQUIRED MARKS ----------------

  function applyRequiredMarks() {
    Object.values(labels).forEach(l => l?.classList.remove("required-field"));

    const s = state.scenario;

    if (["licenses_only", "licenses_plus_sms", "credit"].includes(s)) {
      setRequired(labels.qty, true);
      setRequired(labels.dur, true);
    }

    if (["sms_add", "licenses_plus_sms", "credit", "return"].includes(s)) {
      setRequired(labels.op, true);
      setRequired(labels.amount, true);
    }

    if (s !== "empty") {
      setRequired(labels.terms, true);
    }
  }

  // ---------------- SUMMARY ----------------

  function updateSummary() {
    const s = state.scenario;

    const qty = n(qtyEl.value);
    const dur = n(durEl.value);
    const amount = n(amountEl.value);

    const A = calcA(qty, dur);
    const B = calcB(A, qty, dur);

    let C = "", D = "", E = "", F = "", G = 0;

    if (s === "licenses_only") {
      E = "Mokėjimas per elektroninę bankininkystę";
      F = "Mokama suma:";
      G = A;
    }

    if (s === "sms_add") {
      C = f(amount);
      D = "Papildymas";
      E = "Mokėjimas per elektroninę bankininkystę";
      F = "Mokama suma:";
      G = amount;
    }

    if (s === "credit") {
      C = f(-amount);
      D = "Užskaita";
      G = A - amount;
      F = "Mokama suma:";
      if (G > 0) E = "Mokėjimas per elektroninę bankininkystę";
    }

    if (s === "return") {
      C = f(-amount);
      D = "Grąžinimas";
      F = "Grąžinama suma:";
      G = amount;
    }

    if (s === "licenses_plus_sms") {
      C = f(amount);
      D = "Papildymas";
      E = "Mokėjimas per elektroninę bankininkystę";
      F = "Mokama suma:";
      G = A + amount;
    }

    summaryEl.hidden = (s === "empty");

    summaryEl.innerHTML =
      (
        (s === "licenses_only" || s === "credit")
          ? `Licencijos: ${f(A)} EUR su PVM (${f(B)} EUR su PVM/vnt. per mėn.)<br>`
          : (A ? `Licencijos: ${f(A)} EUR su PVM (${f(B)} EUR su PVM/vnt. per mėn.)<br>` : "")
      ) +
      (C !== "" ? `SMS lėšos: ${C} EUR (${D})<br>` : "") +
      (E ? `${E}<br>` : "") +
      `<strong>${F} ${f(G)} EUR</strong>`;
  }

  // ---------------- STATE ----------------

  function syncState() {
    state.scenario = detectScenario();
    state.isValid = validate();
    state.hasEmptyRequired = !requiredFilled();
  }

  // ---------------- SCENARIOS ----------------

  const scenarios = {
    editing() {
      applyRequiredMarks();

      if (state.scenario === "return") {
        setFieldLocked(qtyEl, true);
        setFieldLocked(durEl, true);
      } else {
        setFieldLocked(qtyEl, false);
        setFieldLocked(durEl, false);
      }

      if (state.scenario === "empty") {
        summaryEl.hidden = true;
        showMessage("");
        disableSubmit();
        return;
      }

      updateSummary();
      updateSteppers();

      if (state.hasEmptyRequired) {
        showMessage("Uzpildykite privalomus formos laukus");
        disableSubmit();
        return;
      }

      if (!state.isValid) {
        showMessage("");
        disableSubmit();
        return;
      }

      showMessage("");
      enableSubmit();
    }
  };

  // ---------------- RENDER ----------------

  function render() {
    scenarios[state.mode]?.();
  }

  // ---------------- EVENTS ----------------

  form.addEventListener("input", () => {
    syncState();
    render();
  });

  form.addEventListener("change", () => {
    syncState();
    render();
  });

  opEl.addEventListener("focus", () => {
    lastOpValue = opEl.value;
  });

  opEl.addEventListener("change", () => {
    if (lastOpValue && !opEl.value) {
      form.reset();
      amountErrorEl.textContent = "";
      summaryEl.hidden = true;
      updateSteppers();
    }
    lastOpValue = opEl.value;
  });

  // ---------------- INIT ----------------

  function init() {
    summaryEl.hidden = true;
    disableSubmit();
    syncState();
    render();
    updateSteppers();
  }

  init();

});