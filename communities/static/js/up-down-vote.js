
async function vote_post(url) {
    console.log(url);
    let promise = await fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest"
        }
    }).catch(error => console.log(error));
    console.log(promise);
    if (promise.status == 200) {
        console.log("Successfully voted");
    } else {
        console.log("Failed to vote");
    }
}