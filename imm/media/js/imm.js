function initBrowser(){
    // Add classes to identify browser types
    var detect = navigator.userAgent.toLowerCase();
    jQuery.each(['firefox', 'msie', 'webkit'], function(index, value){
        if(detect.indexOf(value) + 1){
            jQuery('body, html').addClass(value);
        }
    });
}

function initForms(){
    
    // Transform all multiple select fields
    jQuery('form.objform_raw select[multiple].field.select.large').each(function(index, el){
        var $src_sel = jQuery(el);
        //Add a label beneath the select before cloning the whole div
        $lbl = jQuery('<label/>', {
            'class': 'desc', 
            text: 'Selected ' + $src_sel.attr('name')
        });
        $src_sel.after($lbl);
        var $src_div = $src_sel.parent();
        var $dst_div = $src_div.clone();
        var $dst_sel = $dst_div.find('select[multiple]');
        $lbl.text('Available ' + $src_sel.attr('name'));
        $src_sel.attr({id: $src_sel.attr('id') + '_src', name: $src_sel.attr('name') + '_src'});
        $src_div.attr('class', 'leftSelect');
        $dst_div.attr('class', 'rightSelect');
        $src_div.after($dst_div);
        var $tool_div = jQuery('<div/>', {'class': 'selectTools'});
        var $add_link = jQuery('<img/>', {'class': 'selectAddTool link-row', src: '/img/small-add-icon.png'});
        var $del_link = jQuery('<img/>', {'class': 'selectDelTool link-row', src: '/img/small-remove-icon.png'});
        $tool_div.append($add_link);
        $tool_div.append('<br/>');
        $tool_div.append($del_link);
        $dst_div.before($tool_div);
        
        //Empty right select and transfer all selected items from left select
        $dst_sel.find('option').remove();
        $src_sel.find('option:selected').each(function(i, v){
                $dst_sel.append(v);
        }); 
               
        $add_link.bind('click', function(){
            $src_sel.find('option:selected').each(function(i, v){
                $dst_sel.append(v);
            });
        });
        $del_link.bind('click', function(){
            $dst_sel.find('option:selected').each(function(i, v){
                $src_sel.append(v);
            });
        });       
    });
    
    // Make sure all entries in right select are selected on submit
    jQuery('form.objform_raw').bind('submit', function(){
        jQuery('div.rightSelect option').attr('selected', 'selected');
    });
    
    //add focus handlers
    jQuery('form.objform_raw select.field, form.objform_raw input.field, form.objform_raw textarea.field').each(function(i, el){
        var $field = jQuery(el);
        $field.bind('focus', function(){$field.parent().parent().addClass('focused');});
        $field.bind('blur', function(){$field.parent().parent().removeClass('focused');});
        console.log($field);
    });
    
    // make sure we do not initialize a form twice
    jQuery('form.objform_raw').addClass('objform').removeClass('objform_raw');
    
    
}


