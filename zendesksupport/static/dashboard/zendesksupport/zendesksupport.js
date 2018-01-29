(function($) {
    $(document).ready(function() {
        $('.zendesk-avatar, .zendesk-profile-avatar').nameBadge({
            border: {
                color: '#ddd',
                width: 3
            },

            // an array of background colors.
            colors: ['#a3a948', '#edb92e', '#f85931', '#ce1836', '#009989'],

            // text color
            text: '#fff',
            
            // avatar size
            size: 40,

            // avatar margin
            margin: 5,

            // disable middle name 
            middlename: true,

            // force uppercase
            uppercase: false

        });
    });
})(jQuery);

