function join_attempt(community_slug) {
    var data = {
        'community_slug': community_slug,
    };
    $.ajax({
        type: 'POST',
        url: '/c/' + community_slug + '/verify-join/',
        headers: {"X-Requested-With": "XMLHttpRequest", "X-CSRFToken": getCookie("csrftoken")},
        data: data,
        success: function(data) {
            if (data.success) {
                let join_parent = $('#join');
                let c_slug = `'${community_slug}'`;
                join_parent.html('<button onclick="unjoin_attempt(' + c_slug + ')" id="unjoin_community_button" class="btn btn-primary rounded-3 mt-3" style="width: 11em;">Unfollow</button>');

            } else {
                console.log('failure');
            }
        }
    });
}

function unjoin_attempt(community_slug){
    var data = {
        'community_slug': community_slug,
    };
    $.ajax({
        type: 'POST',
        url: '/c/' + community_slug + '/verify-unjoin/',
        headers: {"X-Requested-With": "XMLHttpRequest", "X-CSRFToken": getCookie("csrftoken")},
        data: data,
        success: function(data) {
            if (data.success) {
                let join_parent = $('#join');
                let c_slug = `'${community_slug}'`;
                console.log(c_slug)
                join_parent.html('<button onclick="join_attempt(' + c_slug + ')" id="join_community_button" class="btn btn-primary rounded-3 mt-3" style="width: 11em;">Follow</button>');

            } else {
                console.log('failure');
            }
        }
    });
}