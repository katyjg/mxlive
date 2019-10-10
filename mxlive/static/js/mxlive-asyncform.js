(function($){
    $.fn.shake = function(options) {
        let settings = $.extend({
            interval: 100,
            distance: 5,
            times: 4
        }, options );

        $(this).css('position','relative');

        for(let iter=0; iter<(settings.times+1); iter++){
            $(this).animate({ left:((0 === iter%2 ? settings.distance : settings.distance * -1)) }, settings.interval);
        }
        $(this).animate({ left: 0}, settings.interval, function(){});
    };
})(jQuery);


(function ( $ ) {
    $.fn.asyncForm = function (options) {
        let defaults = {
            url: $(this).data('form-action'),
            setup: function (body) {
                body.find('form').attr('action', "");
                body.find(".chosen").chosen({
                    placeholder_text_single: "Select an option",
                    search_contains: true,
                    allow_single_deselect: true,
                    disable_search_threshold: 8,
                });
                body.find(".chosen").trigger("chosen:updated");
                body.find("select[data-update-on]").each(function(){
                    let src = $('[name="'+ $(this).data('update-on')+'"]');
                    let dst = $(this);
                    let initial = dst.find('option:selected').val();
                    let url_template = dst.data('update-url');

                    src.change(function(){
                        if (src.val()) {
                            let url = url_template.replace(/\d+/, src.val());
                            $.ajax({
                                url: url,
                                dataType: 'json',
                                success: function (response) {
                                    let new_options = response;
                                    dst.empty();
                                    $.each(new_options, function(i, item) {
                                        dst.append($('<option>', {
                                                value : item[0],
                                                text: item[1],
                                            selected: (initial == item[0])
                                            })
                                        );
                                    });
                                    dst.trigger('chosen:updated');
                                }
                            });
                        }
                    });
                });
            },
            complete: function(data) {
                console.log(data);
                //window.location.reload()
            }
        };
        let settings = $.extend(defaults, options);
        let target = $(this);

        // load form and initialize it
        $.ajax({
            type: 'GET',
            url: settings.url,
            success: function(response) {
                target.html(response);
                settings.setup(target);
                target.find('.modal').modal({backdrop: 'static'});
                target.find('.modal').on('hidden.bs.modal', function(){
                    target.empty();  // remove contents after hiding
                });
            }
        });
        target.off("click", ":submit");
        target.on("click", ":submit", function(e){
            console.log(target.find('form'));
            e.preventDefault();
            e.stopPropagation();
            let button = $(this);
            button.html('<i class="ti ti-reload spin"></i>');

            target.find("form").ajaxSubmit({
                type: 'post',
                url: settings.url,
                data: {'submit': button.attr('value')},
			    beforeSend: function(xhr, settings){
                    xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
                },
                success: function(data, status, xhr) {
                    let dataType = xhr.getResponseHeader("content-type") || "";

                    // contains form
                    if (/html/.test(dataType)) {
                        let response = $(data);
                        let contents = target.find(".modal-content");
                        let new_contents = response.find('.modal-content');
                        if (contents.length && new_contents.length) {
                            contents.html(new_contents.html());
                            settings.setup(target);
                        } else {
                            target.html(data);
                            settings.setup(target);
                            target.find('.modal').modal({backdrop: 'static'});
                        }
                    } else if (/json/.test(dataType)) {
                        target.find('.modal').modal('hide').data('bs.modal', null);
                        settings.complete(data);
                    } else {
                        target.find('.modal').modal('hide').data('bs.modal', null);
                    }
                },
                error: function() {
                    button.shake();
                    button.html('<i class="ti ti-alert"></i>');
                }
            })
        });
    };

}(jQuery));