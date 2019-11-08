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
    let trimmed = $.trim(str);
    return trimmed.replace(/[^a-z0-9-_]/gi, '-')
                   .replace(/-+/g, '-')
                   .replace(/^-|-$/g, '');
};

function groupByContainer() {
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
    let group = $('span.group-name').html();
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
    let rows = $('.repeat-row').not('.template');
    $.each(data, function(e, values) {
        let field = e.split('_set')[0];
        $.each(values, function(i, val) {
            let input = $(rows[i]).find($(':input[name="' + field + '"]'));
            input.val(val);
        });
    });
    //$('.repeat-container').css('opacity', 0).fadeTo('slow', 1);
}


function openSelector(group) {
    $('span.group-name').html(group);
    $('#group-select circle.full[group="'+group+'"]').addClass('selected').removeClass('full');
    $('#group-select circle').off();
    $('#group-select circle').on('click', function () {
        selectOne(this, group);
    });
}
function initShipmentWizard() {
    let row_selector = '.repeat-row';
    let rowcount_placeholder = '{rowcount}';

    function update_fields() {
        // Update and renumber field ids, reconstructing select2 elements as needed
        $(row_selector+':not(.template)').each(function(pos, row){

            $(row).find(".select-alt.select2-hidden-accessible").each(function (i, elem){
                if ($(this).data('select2')) {
                    $(this).select2('destroy');
                }
            });

            $(row).find('[id]').each(function(i, item){
                if (item.id.match(/--\d+$/)) {
                    $(item).attr('id', item.id.replace(/--\d+$/, '--'+pos));
                } else {
                    $(item).attr('id', item.id + '--' + pos);
                }
            });
            $(row).find('label[for]').each(function(i, item){
                if ($(item).attr('for').match(/--\d+$/)) {
                    $(item).attr('for', $(item).attr('for').replace(/--\d+$/, '--'+pos));
                } else {
                    $(item).attr('for', $(item).attr('for') + '--' + pos);
                }
            });
            $(row).find('a[href*="--"]').each(function(i, item){
                if ($(item).attr('href').match(/--\d+$/)) {
                    $(item).attr('href', $(item).attr('href').replace(/--\d+$/, '--'+pos));
                }
            });
            $(row).find(".select-alt:not(.select2-hidden-accessible)").select2({theme: 'bootstrap4'});
        });
    }
    $('.repeat').each(function() {
        // Destroy select2 widgets as they will be added later
        $(this).find(".select-alt.select2-hidden-accessible").each(function() {
            if ($(this).data('select2')) {
               $(this).select2('destroy');
            }
        });

        // Connect remove event handler globally for this repeat-group
        $(this).on('click', '.safe-remove', function (){
            let cur_row = $(this).closest('.repeat-row');
            $(this).hide();
            cur_row.find($('.remove')).show();
            setTimeout(function(){
                cur_row.find($('.safe-remove')).show();
                cur_row.find($('.remove')).hide();
            }, 3000);
        });

        // Initialize repeatable for repeat-group
        $(this).repeatable_fields({
            row_count_placeholder: rowcount_placeholder,
            row: row_selector,
            container: '.repeat-container',
            wrapper: '.repeat-wrapper',
            after_add: function(container, row) {
                let row_count = $(container).attr('data-rf-row-count');
			    row_count++;
                $('*', row).each(function() {
                    $.each(this.attributes, function() {
                        this.value = this.value.replace(rowcount_placeholder, row_count - 1);
                    });
                });

			    $(container).attr('data-rf-row-count', row_count);
                update_fields();

            },
            after_remove: function(container, row) {
                update_fields();
            }
        });
        $('.add').trigger('click');
        $('.repeat-wrapper').find('.repeat-container').on('sortupdate', function( event, ui ) {
            $.each($('input[name$="priority"]'), function(i, e) {
               $(e).val(i);
            });
        } );
    });
}
