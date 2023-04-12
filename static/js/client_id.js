function updateClientIdChoices() {
    if (facilitySelect.value) {
        $.ajax({
            url: "/get_client_ids",
            data: {
                facility_name: facilitySelect.options[facilitySelect.selectedIndex].text
            },
            dataType: 'json',
            success: function(data) {
                let options = '<option data-hidden="true">Select a client ID</option>';
                data.forEach(client => {
                    options += `<option value="${client.id}">${client.client_id}</option>`;
                });
                clientIDSelect.innerHTML = options;
            },
            error: function() {
                clientIDSelect.innerHTML = '<option data-hidden="true">Select a client ID</option>';
            }
        });
    } else {
        clientIDSelect.innerHTML = '<option data-hidden="true">Select a client ID</option>';
    }
}
