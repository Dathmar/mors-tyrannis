function accept_request(url, elem) {
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    }).then(response => {
        if (response.status == 200) {
            let button_area = $(elem).closest('td');
            button_area.html('Accepted');
        } else {
            alert('Error accepting request');
        }
    });
}

function reject_request(url, elem) {
    let reject_id = elem.value;
    let reject_message = $(`#reject-message-${reject_id}`).val();
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            'reject_message': reject_message
        })

    }).then(response => {
        if (response.status == 200) {
            let button_area = $(elem).closest('td');
            button_area.html('Rejected');
        } else {
            alert('Error rejecting request');
        }
    });

}

function blah(){

}