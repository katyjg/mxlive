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
        let target = $(this);
        let defaults = {
            url: $(this).data('form-action'),
            setup: function (body) {
                body.find(".select").select2({theme: 'bootstrap4'});
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
                                                selected: (initial === item[0])
                                            })
                                        );
                                    });
                                    dst.trigger('change.select2');
                                }
                            });
                        }
                    });
                });
            },
            complete: function(data) {
                if (data.url) {
                    if (data.modal) {
                        target.load(data.url);
                    } else {
                        window.location.replace(data.url);
                    }
                } else {
                    window.location.reload();
                }
            }
        };
        let settings = $.extend(defaults, options);


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
            let form = target.find('form');
            e.preventDefault();
            e.stopPropagation();

            if (!form[0].checkValidity()) {
                form[0].reportValidity();
                return
            }

            let button = $(this);
            button.html('<i class="ti ti-reload spin"></i>');

            form.ajaxSubmit({
                type: 'post',
                url: form.attr('action'),
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

(function ( $ ) {
    $.fn.loadModal = function (url) {
        let target = $(this);

        // load form and initialize it
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                target.html(response);
                target.find('.modal').modal({backdrop: 'static'});
                target.find('.modal').on('hidden.bs.modal', function(){
                    target.empty();  // remove contents after hiding
                });
            }
        });
    };
}(jQuery));


function slugify(str) {
    let slug = '';
    var trimmed = $.trim(str);
    slug = trimmed.replace(/[^a-z0-9-_]/gi, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
    return slug;
}

function strip(s) {
    return s.replace(/^\s*|\s*$/g, '');
}