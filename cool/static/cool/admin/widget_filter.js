
(function($) {
    'use strict';

    var submit = function(event, element) {
        $("#changelist-filter input, #changelist-filter select").attr("disabled", "disabled");
        var url;
        if (event.target.value) {
            url = element.dataset.queryString.replace(element.dataset.queryStringValue, event.target.value);
        } else {
            url = element.dataset.queryStringAll;
        }
        window.location = window.location.pathname + url;
    };
    $(function() {
        $.each($('input.admin-widget-filter, select.admin-widget-filter'), function(i, element) {
            $(element).on('change', function (event){
                submit(event, element);
            });
            $(element).on('keydown', function (event){
                if(event.keyCode === 13){
                    submit(event, element);
                }
            });
        });
    });
}(django.jQuery));
