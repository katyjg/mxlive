Event.observe(window, 'load', browserInit);

function load_page(containerid, url, pars){
    var myAjax = new Ajax.Updater(containerid, url, {method: 'get', parameters: pars});
};


function post_and_load(containerid, url, form){
    var myAjax = new Ajax.Updater(containerid, url, {method: 'post', parameters: $(form).serialize(true)});
};

function post_and_reload(containerid, url){
    var myAjax = new Ajax.Updater(containerid, url, {method: 'post'});
};


function refresh_window(){
    window.location.reload(true);
    
};

/*
function post_and_load(containerid,url, form){
    var myAjax = $(form).request({
        onComplete: function(response){
            $(containerid).update(response.responseText);
        }  
    });
}
*/

function linkto(theUrl){
  document.location.href = theUrl;
}

function browserInit(){
    var detect = navigator.userAgent.toLowerCase();
    
    ['safari', 'firefox'].each( tag_html )
    function tag_html( itm ){
        if(detect.indexOf(itm) + 1){
            $$('html')[0].addClassName(itm);
        }   
    }
}

function add_focus_handlers(el) {
    el.observe('focus', function() {el.parentNode.parentNode.addClassName('focused');} );
    el.observe('blur', function() {el.parentNode.parentNode.removeClassName('focused');} );
}


function transform_select(src_el) {
    src_el.className='field select large';
    var src_div = src_el.parentNode;
    var el_li = src_div.parentNode;
    var dest_div = new Element('div', {'class': 'rightSelect'});
    var tool_div = new Element('div', {'class': 'selectTools'});
    var dest_el = src_el.cloneNode(false);
    src_el.id += '_src';
    src_el.name += '_src';
   
    src_div.className = 'leftSelect';
    src_div.insert({'after': dest_div});
    src_div.insert({'after': tool_div});
    dest_div.appendChild(dest_el);
    var add_link = new Element('img', {'class':'selectAddTool link-row','src':'/img/add-icon.png','border':0});
    var del_link = new Element('img', {'class':'selectDelTool link-row','src':'/img/remove-icon.png','border':0});
    tool_div.insert(add_link);
    tool_div.insert(del_link);
    add_link.insert({'after': '<br/>'} );

    add_link.observe('click', add_items);
    del_link.observe('click', remove_items);
    
    src_el.insert({'after': new Element('label', {'for':src_el.id, 'class':'desc'}).update("Available #{nm}".interpolate({'nm': dest_el.name}))});
    dest_el.insert({'after': new Element('label', {'for':dest_el.id, 'class':'desc'}).update("Selected #{nm}".interpolate({'nm': dest_el.name}))});
    
    function transfer(src, dest){
        while (src.selectedIndex != -1){
            dest.appendChild(src.options.item(src.selectedIndex)) 
        }
    }

    function add_items(event) {
        transfer(src_el, dest_el)
    }

    function remove_items(event) {
        transfer(dest_el, src_el)
    }
    transfer(src_el, dest_el);
}

function transform_choicebox(el) {
    el.next('label').addClassName('choice');
}

function init_form(frm) {
    var field_str = "##{form}.objform .field".interpolate({'form': frm});
    var sel_str =   "##{form}.objform select[multiple]".interpolate({'form': frm});
    var choice_str = "##{form}.objform input.checkbox".interpolate({'form': frm});
    $$(sel_str).each(transform_select);
    $$(field_str).each( add_focus_handlers );
    $(frm).focusFirstElement();
    
    //$$(choice_str).each( transform_choicebox )
    $(frm).style.display = 'block';
    
    // Select all options before submitting 
    $(frm).observe('submit', function(){ 
        $$(sel_str).each( select_all);
    });
    
    function select_all(sel){
        sel.childElements().each( function(opt){
        opt.selected=true
    });
    }
        
}

