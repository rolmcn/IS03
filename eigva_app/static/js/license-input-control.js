function attachNumberControl(inputId, decBtnId, incBtnId) {
    const input = document.getElementById(inputId);
    const decBtn = document.getElementById(decBtnId);
    const incBtn = document.getElementById(incBtnId);

    if (!input || !decBtn || !incBtn) return;

    // 🔒 prevent double init
    if (input.dataset.numberControlInit === "1") return;
    input.dataset.numberControlInit = "1";

    const min = input.min !== "" ? parseInt(input.min) : -Infinity;
    const max = input.max !== "" ? parseInt(input.max) : Infinity;
    const step = input.step ? parseInt(input.step) : 1;

    function setValue(newValue) {
        let value = parseInt(newValue);

        if (isNaN(value)) value = 0;

        value = Math.min(Math.max(value, min), max);

        input.value = value;
        input.dispatchEvent(new Event("input", { bubbles: true }));

        updateButtons(value); // 🔥 ADD
    }

    function updateButtons(value) {
        decBtn.disabled = value <= min;
        incBtn.disabled = value >= max;
    }

    function change(delta) {
        const current = parseInt(input.value) || 0;
        setValue(current + delta);
    }

    // initial state
    setValue(input.value);

    decBtn.addEventListener("click", () => change(-step));
    incBtn.addEventListener("click", () => change(step));

    input.addEventListener("input", () => {
        setValue(input.value);
    });

    input.addEventListener("blur", () => {
        if (input.value === "") setValue(0);
    });
}

// === INIT ===
document.addEventListener("DOMContentLoaded", function () {

    attachNumberControl(
        "licenses-quantity",
        "decrease-licenses",
        "increase-licenses"
    );

    attachNumberControl(
        "licenses-duration",
        "decrease-months",
        "increase-months"
    );

});