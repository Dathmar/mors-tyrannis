
async function vote_post(url, id) {
    let promise = await fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest"
        }
    }).then(response => response.json()).then(data => {
        let rep_change = data.rep_change;
        let vote_type = data.vote_type;

        let up_arrow_elem;
        let down_arrow_elem;
        let vote_elem;

        if (data.object_type === 'post') {
            vote_elem = $('#post-rep-' + id);
            up_arrow_elem = $('#post-up-arrow-' + id);
            down_arrow_elem = $('#post-down-arrow-' + id);
        } else {
            vote_elem = $('#comment-rep-' + id);
            up_arrow_elem = $('#comment-up-arrow-' + id);
            down_arrow_elem = $('#comment-down-arrow-' + id);
        }


        if (vote_type == 'up') {
            if (up_arrow_elem.hasClass('up-arrow-active')) {
                up_arrow_elem.removeClass('up-arrow-active');
                up_arrow_elem.addClass('up-arrow');
            } else {
                up_arrow_elem.addClass('up-arrow-active');
                up_arrow_elem.removeClass('up-arrow');
            }

            down_arrow_elem.removeClass('down-arrow-active');
            down_arrow_elem.addClass('down-arrow');
        } else if (vote_type == 'down') {
            if (down_arrow_elem.hasClass('down-arrow-active')) {
                down_arrow_elem.removeClass('down-arrow-active');
                down_arrow_elem.addClass('down-arrow');
            } else {
                down_arrow_elem.addClass('down-arrow-active');
                down_arrow_elem.removeClass('down-arrow');
            }

            up_arrow_elem.removeClass('up-arrow-active');
            up_arrow_elem.addClass('up-arrow');
        }

        vote_elem.text(parseInt(vote_elem.text()) + rep_change);

    }).catch(error => console.log(error));
}