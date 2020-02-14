(function ($) {
    $.fn.displayModes = function (options) {
        let parent = $(this);
        let settings = $.extend({
            detailed: parent.data('detailed'),
            prefix: parent.data('prefix') || 'bt',
            root_id: parent.data('pk'),
            on_complete: function() {
            },
        }, options);

        let url = parent.data('modes-url');
        // fetch data and render
        $.ajax({
            dataType: "json",
            url: url,
            success: function (data, status, xhr) {
                let width = parent.width();
                let height = width * (data.height || 1);
                let svg_id = settings.prefix + '-' + data.id;
                console.log(data);


                // run complete function
                settings.on_complete();
            }
        });
    }
}(jQuery));

(function ($) {
    $.fn.displayBeamtime = function (options) {
        let parent = $(this);
        let settings = $.extend({
            detailed: parent.data('detailed'),
            prefix: parent.data('prefix') || 'bt',
            root_id: parent.data('pk'),
            on_complete: function() {
            },
        }, options);

        let url = parent.data('beamtime-url');
        // fetch data and render
        $.ajax({
            dataType: "json",
            url: url,
            success: function (data, status, xhr) {
                $.each(data, function(i, bt) {
                    $.each(bt.starts, function(j, st) {
                        parent.find("[data-shift-id='" + st + "']").find("[data-beamline='" + bt.beamline + "']")
                            .html("<a href='#' data-form-link='/calendar/beamtime/" + bt.id + "/edit/'>" + bt.title + "</a>")
                            .attr('title', bt.comments)
                            .addClass('full');
                    });
                });

                // run complete function
                settings.on_complete();
            }
        });
    }
}(jQuery));

function setupEditor(sel) {
    let beamtime_url = $(sel).data('beamtime-url');
    $(sel + ' [data-beamline]')
        .mouseover(function (event) {
            if(!$('.hold').length && !$(this).hasClass("full")) {
                $(this).addClass('starting');
            }
        })
        .mouseout(function (event) {
            if(!$(this).hasClass('hold')) {
                $(this).removeClass('starting');
            }
        })
        .click(function (event) {
            let row = $(this).closest('tr');
            if(!$(this).hasClass('block') && !row.hasClass('block') && !$(this).hasClass("full")) {
                if ($('.hold').length) {
                    let bl = $('.hold').data('beamline');
                    let start = $('.hold').closest('tr').data('shift-id');
                    let end = row.data('shift-id');
                    $('#modal-target').asyncForm({
                        url: beamtime_url + "?start=" + start + "&end=" + end + "&beamline=" + bl,
                        complete: function (data) {
                            $.ajax({
                                url: $(sel).data('week-url'),
                                context: document.body,
                                success: function(d) {
                                    $(sel).html(d);
                                    $(document).on('click', '[data-form-link]', function () {
                                        $('#modal-target').asyncForm({url: $(this).data('form-link')});
                                    });
                                }
                            });
                        }
                    });
                } else {
                    let bl = $(this).data('beamline');
                    $(this).toggleClass('hold');
                    $(this).addClass('starting');
                    row.prevAll().addClass("block");
                    $('[data-beamline]').not('[data-beamline="' + bl + '"]').addClass("block");
                }
            }
        });
}
