function join_attempt(community_slug) {
    console.log("join_attempt");
    var data = {
        'community_slug': community_slug,
    };
    $.ajax({
        type: 'POST',
        url: '/c/'+community_slug+'/verify-join/',
        headers: {"X-Requested-With": "XMLHttpRequest", "X-CSRFToken": getCookie("csrftoken")},
        data: data,
        success: function(data) {
            if (data.success) {
                let join_button = $('#join_community_button');
                join_button.val('Joined!');
                join_button.attr('disabled', true);
                let join_parent = join_button.parent();
                join_parent.append('<a href="/c" + community_slug + "/new-post/" class="btn btn-primary rounded-3 mt-3" style="width: 11em;">Create Post</a>');

            } else {
                console.log()
            }
        }
    });
}