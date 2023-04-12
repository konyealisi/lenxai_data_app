console.log("Script loaded");

$(document).ready(function () {
  const clientIDSelect = document.getElementById("clientIDSelect");
  const facilitySelect = document.getElementById("facilitySelect");
  const form = document.getElementById("validate-form");
  const recordDisplay = document.getElementById("record-display");

  function updateFormAction() {
    form.action = "/validate_client_record/" + clientIDSelect.value + "/" + facilitySelect.value;
  }

  clientIDSelect.addEventListener("change", updateFormAction);
  facilitySelect.addEventListener("change", updateFormAction);
  updateFormAction();

  function updateClientRecordDisplay(clientRecord) {
    if (clientRecord) {
      $("#dregimen_po").text(clientRecord.dregimen_po);
      $("#dregimen_pw").text(clientRecord.dregimen_pw);
      $("#laspud_po").text(clientRecord.laspud_po);
      $("#laspud_pw").text(clientRecord.laspud_pw);
      $("#quantityd_po").text(clientRecord.quantityd_po);
      $("#quantityd_pw").text(clientRecord.quantityd_pw);
      $("#record-display").show();
    } else {
      $("#record-display").hide();
    }
  }

  function fetchClientRecord() {
    if (clientIDSelect.value && facilitySelect.value) {
      $.ajax({
        url: "/fetch_client_record",
        data: {
          client_id: clientIDSelect.value,
          facility_name: facilitySelect.value,
        },
        dataType: "json",
        success: function (data) {
          updateClientRecordDisplay(data);
        },
        error: function () {
          updateClientRecordDisplay(null);
        },
      });
    } else {
      updateClientRecordDisplay(null);
    }
  }

  clientIDSelect.addEventListener("change", fetchClientRecord);
  facilitySelect.addEventListener("change", fetchClientRecord);
  fetchClientRecord();
});
