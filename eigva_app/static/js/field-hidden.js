document.addEventListener("DOMContentLoaded", function () {

    const buyerType = document.getElementById("buyer_type");
    const vatStatus = document.getElementById("vat_status");

    const companyCodeField = document.getElementById("identification_code").closest(".form-field");
    const vatCodeField = document.getElementById("vat_code").closest(".form-field");

    function toggleCompanyCode() {
        if (!buyerType) return;

        if (buyerType.value === "fizinis") {
            companyCodeField.style.display = "none";
        } else {
            companyCodeField.style.display = "";
        }
    }

    function toggleVatCode() {
        if (!vatStatus) return;

        if (vatStatus.value === "no") {
            vatCodeField.style.display = "none";
        } else {
            vatCodeField.style.display = "";
        }
    }

    // initial state (puslapio užkrovimas)
    toggleCompanyCode();
    toggleVatCode();

    // change events
    if (buyerType) {
        buyerType.addEventListener("change", toggleCompanyCode);
    }

    if (vatStatus) {
        vatStatus.addEventListener("change", toggleVatCode);
    }

});