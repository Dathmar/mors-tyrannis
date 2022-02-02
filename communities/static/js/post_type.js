async function change_post_type() {
    let form_type = $('#id_post_type');
    let post_type = form_type.val();
    let form_container = $('#form-container');
    let url = '/c/change-form-type/' + post_type;
    await fetch(url).then(
        response => response.json()
    ).then(
        data => {
            form_container.html(data.form_html);
            if (post_type === 'image') {
                form_container.attr('enctype', "multipart/form-data")
            } else {
                form_container.removeAttr('enctype')
            }

            form_type = $('#id_post_type');
            form_type.val(post_type);
        }
    );

}