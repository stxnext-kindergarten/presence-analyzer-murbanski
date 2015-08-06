(function($) {
    $(document).ready(function(){
        var loading = $('#loading');
        $.getJSON("/api/v1/users", function(result) {
            var dropdown = $("#user_id");
            $.each(result, function(item) {
                dropdown.append($("<option />").val(this.user_id+','+this.avatar).text(this.name));
            });
            dropdown.show();
            loading.hide();
        });
        $('#user_id').change(function(){
            var selected_user = $("#user_id").val().split(',')[0];
            if(selected_user) {
                var avatar = $("#user_id").val().split(',')[1];
                var avatar_div = $('#user_avatar');
                avatar_div.empty();
                avatar_div.append($("<img />").attr("src",avatar))
            }
        });
    });
})(jQuery);