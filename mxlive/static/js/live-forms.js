function selectOne(e, group) {
    var locations = $('input[id$=sample_locations]');
    var data = $.parseJSON(locations.val());
    var assigned_group = $(e).attr('group');
    if (!assigned_group | group == assigned_group) {

        $(e).toggleClass('empty').toggleClass('selected');
        var port = $(e).attr('port');
        var container = slug($(e).closest('svg').attr('id'));
        if (!(group in data)) {
            data[group] = {};
        }
        if (assigned_group == group) {
            $(e).attr('group','');
            data[group][container] = $.grep(data[group][container], function (value) {
                return value != port;
            });
        } else {
            $(e).attr('group', group);
            if (!(container in data[group])) {
                data[group][container] = [];
            }
            if (port.indexOf(data[group][container]) <= 0) {
                data[group][container].push(port);
            }
        }
    }

    locations.val(JSON.stringify(data));
}

function selectAll(container) {
    var group = $('span.group-name').html();
    var containerid = slug(container);
    if($('#group-select #'+container+' circle.empty').length) {
        $.each( $('#group-select #'+container+' circle.empty'), function() {
            selectOne(this, group);
        });
    } else {
        $.each($('#group-select #' + container + ' circle.selected'), function () {
            selectOne(this, group);
        });
    }
};

var slug = function(str) {
    var $slug = '';
    var trimmed = $.trim(str);
    $slug = trimmed.replace(/[^a-z0-9-]/gi, '-').
    replace(/-+/g, '-').
    replace(/^-|-$/g, '');
    return $slug;
}

function fillContainers() {

    $.each($('.repeat-row[class!="template"]'), function() {
       if (!($(this).hasClass('template'))) {
           $(this).find('.remove').trigger('click');
       }
    });

    $.each( $('[id^="formlayout"] svg'), function() {
        $('.add').trigger('click');
        var container = $(this).attr('id');
        var row = $('.repeat-row[class!="template"]').last();
        row.find('input[name$="name"]').val(slug(container).toLowerCase()).trigger('focusin').trigger('change');
        $('span.group-name').html(slug(container).toLowerCase());
        selectAll(container);
        var num = $('[id^="formlayout"] circle[group="'+slug(container).toLowerCase()+'"]').length;
        row.find('input[name$="sample_count"]').val(num);
    });

    $('#group-select circle.selected').addClass('full').removeClass('selected');

}

$('text[port]').hover(function() {
    $.each($(this).parents('svg').find('circle[port*="'+$(this).attr('port')+'"]').not('.full'), function() {
       $(this).addClass('hover');
    });
}, function() {
    $.each($(this).parents('svg').find('circle[port*="'+$(this).attr('port')+'"]').not('.full'), function() {
       $(this).removeClass('hover');
    });
});
$('text[port]').on('click', function() {
    var group = $('span.group-name').html();
    $.each($(this).parents('svg').find('circle[port*="'+$(this).attr('port')+'"]').not('.full'), function() {
       selectOne(this, group);
    });
});

function setInitial(data) {
    $.each(data, function(e, values) {
        for (var i=0; i<=values.length; i++) {
            if (i > $('.repeat-row').not('.template').length) {
                $('.add').trigger('click');
            }
        }
    });
    var rows = $('.repeat-row').not('.template');
    $.each(data, function(e, values) {
        var field = e.split('_set')[0];
        $.each(values, function(i, val) {
            var input = $(rows[i]).find($('input[css-id="'+field.toString()+'"]'));
            var select = $(rows[i]).find($('select[css-id="'+field.toString()+'"]'));
            if (input.length) { input.attr('value', val); }
            if (select.length) {
                var option = select.find('option[value="'+val+'"]').attr('selected','true');
                $(rows[i]).find($('.tab-chosen')).trigger("chosen:updated");
            }
        });
    });
    $.each($('input[name$="name"]'), function() {
        if ($(this).attr('value')) {
            var row = $(this).closest('.repeat-row');
            $(this).attr('')
            $(row).find($('a.disabled')).removeClass('disabled').attr('group',$(this).attr('value'));
        }
    });
}

function hideModal(e) {
    e.closest($('.modal')).modal('hide');
    var group = $('span.group-name').html();
    $('#group-select circle.selected').addClass('full').removeClass('selected');
    $('#group-select circle').off();
}
function showModal(e) {
    $(e.attr('href')).modal('show');
    var group = $(e).attr('group');
    openSelector(group);
}

function openSelector(group) {
    $('span.group-name').html(group);
    $('#group-select circle.full[group="'+group+'"]').addClass('selected').removeClass('full');
    $('#group-select circle').off();
    $('#group-select circle').on('click', function () {
        selectOne(this, group);
    });
}

jQuery(function() {
	$('#modalForm').find("[title]:not([data-toggle='popover'])").tooltip({
    		container: '#modal-form',
    		viewport: {selector: '#modal-form', padding: 5}
    });
	jQuery('.repeat').each(function() {
		jQuery(this).repeatable_fields({
            row_count_placeholder: '{rowcount}',
            row: '.repeat-row',
            container: '.repeat-container',
            wrapper: '.repeat-wrapper',
            after_add: function(container, new_row) {
                $('.flip-container').height($('.front').height());
                var rows = $(container).children('.repeat-row').filter(function() {
                    return !jQuery(this).hasClass('template');
                });
                var row_count = rows.length;
                $('*', new_row).each(function() {
                    $.each(this.attributes, function(index, element) {
                        this.value = this.value.replace('{rowcount}', row_count - 1);
                    });
                });
                rows.find('[data-toggle="tab"]').not('.repeated').each(function() {
                    var old_id = $(this).attr('href');
                    var num = row_count - 1;
                    $(this).attr('href', old_id + '-' + num ).addClass('repeated');
                    rows.find(old_id).attr("id", old_id.replace('#','') + '-' + num);
                });

                new_row.find(".tab-chosen").chosen({
                    placeholder_text_single: "Select an option",
                    search_contains: true,
                    allow_single_deselect: true,
                    disable_search_threshold: 8,
                });
                new_row.find(".chosen-select").trigger("change");
                new_row.find('[data-toggle="collapse"]').click(function(e){
                    e.preventDefault();
                    e.stopPropagation();
                    var dropdown = $($(this).attr('href'));
                    dropdown.slideToggle().toggleClass('in');
                });
                new_row.find("input[name$='name']").focus();

                if ($('input[id$=sample_locations]').length) {
                    $('input[name$="name"]').on('focusin', function (e) {
                        $(this).data('val', $(this).val());
                    });
                    $('input[name$="name"]').on('input paste change', function(f) {
                        var row = f.target.closest('.repeat-row');
                        $(row).find($('a[href="#group-select"]')).removeClass('disabled').attr('group', $(this).val());
                    });
                    $('input[name$="name"]').on('change', function (f) {
                        f.stopImmediatePropagation();
                        $(this).val(slug($(this).val()));
                        $('circle[group='+$(this).data('val')+']').attr("group", $(this).val());

                        var locations = $('input[id$=sample_locations]');
                        var data = $.parseJSON(locations.val());
                        data[$(this).val()] = data[$(this).data('val')];
                        if ($(this).data('val') in data) {
                            delete data[$(this).data('val')];
                        }
                        locations.val(JSON.stringify(data));
                    });
                }
                $('.safe-remove').on('click', function(e) {
                    var row = e.target.closest('.repeat-row');
                    $(this).hide();
                    $(row).find($('.remove')).show();
                    function protect(){
                      $(row).find($('.safe-remove')).show();
                      $(row).find($('.remove')).hide();
                    }
                    setTimeout(protect, 3000);
                });
            },
            before_remove: function(container, row) {
                if ($('input[id$=sample_locations]').length) {
                    var group = $(row).find($('input[name$="name"]')).val();

                    if (group) {
                        $.each($('#group-select circle[group='+group+']'), function () {
                            $(this).removeClass('full').addClass('selected');
                            selectOne(this, group);
                        });
                        var locations = $('input[id$=sample_locations]');;
                        var data = $.parseJSON(locations.val());
                        if (group in data) {
                            delete data[group];
                        }
                        locations.val(JSON.stringify(data));
                    }
                }
            }
        });
		$('.add').trigger('click');
		$('.repeat-wrapper').find('.repeat-container').on('sortupdate', function( event, ui ) {
		    $.each($('input[name$="priority"]'), function(i, e) {
		       $(e).val(i);
            });
        } );
	});
});