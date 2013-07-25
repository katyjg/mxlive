function initBrowser(){
    // Add classes to identify browser types
    var detect = navigator.userAgent.toLowerCase();
    jQuery.each(['firefox', 'msie', 'webkit'], function(index, value){
        if(detect.indexOf(value) + 1){
            jQuery('body, html').addClass(value);
        }
    });
    
    // Enable nicer tooltips
    tooltips();
    
    // Make sure ajax POSTs are not rejected by django CSRF mechanism
    jQuery.ajaxSetup({ 
         beforeSend: function(xhr, settings) {
             function getCookie(name) {
                 var cookieValue = null;
                 if (document.cookie && document.cookie != '') {
                     var cookies = document.cookie.split(';');
                     for (var i = 0; i < cookies.length; i++) {
                         var cookie = jQuery.trim(cookies[i]);
                         // Does this cookie string begin with the name we want?
                     if (cookie.substring(0, name.length + 1) == (name + '=')) {
                         cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                         break;
                     }
                 }
             }
             return cookieValue;
             }
             if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                 // Only send the token to relative URLs i.e. locally.
                 xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
             }
         } 
    });
}

function initRedirects(){
    jQuery(".redirect").live("click", function() {    
        // any element with ".redirect" class will act as a link when clicked,
        // and go to the link specified in the href attribute
        if(jQuery(this).attr("href")) {
            // fetch the contents of the href
            var $row = jQuery(this);
            var contentURL = $row.attr("href");
            window.location.href = contentURL;
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
    });
        
    // make sure we do not initialize a form twice
    jQuery('form.objform_raw').addClass('objform').removeClass('objform_raw');

    // disable submit-on-enter for barcode fields
    $('input.barcode, input.matrixcode').live("keypress", function(e) {
        /* ENTER PRESSED*/
        if (e.keyCode == 13) {
            /* FOCUS ELEMENT */
            var inputs = $(this).parents("form").eq(0).find(":input");
            var idx = inputs.index(this);
            if (idx == inputs.length - 1) {
                inputs[0].select()
            } else {
                inputs[idx + 1].focus(); // handles submit buttons
            }
            return false;
        }
    });

}

function initModals(){
    // Prepare all modal popub including links for modal forms
	jQuery(".modal").fancybox({
		'titlePosition'		: 'inside',
		'transitionIn'		: 'none',
		'transitionOut'		: 'none',
		'scrolling'         : 'no',
		'titleShow'         : false
	});
	
	jQuery(".modal-ajax").fancybox({
		'titlePosition'		: 'inside',
		'transitionIn'		: 'none',
		'transitionOut'		: 'none',
		'scrolling'         : 'no',
		'titleShow'         : false,
		'type'              : 'ajax'
	});
	
	jQuery(".modal-inline").fancybox({
		'titlePosition'		: 'inside',
		'transitionIn'		: 'none',
		'transitionOut'		: 'none',
		'titleShow'         : false,
		'type'              : 'inline'
	});

	jQuery(".modal-iframe").fancybox({
		'width'				: '75%',
		'height'			: '75%',
		'autoScale'			: false,
		'transitionIn'		: 'none',
		'transitionOut'		: 'none',
		'titleShow'         : false,
		'type'				: 'iframe'
	});
	
	jQuery(".modal-image").fancybox({
		'transitionIn'	: 'elastic',
		'transitionOut'	: 'elastic',
		'type'          : 'image',
		'titlePosition'	: 'inside'
	});
	
	jQuery(".modal-flash").fancybox({
        'width'         : '100%',
        'height'        : '100%',
		'titleShow'     : false,
		'type'          : 'swf'
	});

    jQuery(".modal-form").fancybox({
	    'scrolling'         : 'no',		
	    'titleShow'         : false,
         onComplete:function (){
            //grab this function so that we can pass it back to
            //`onComplete` of the new fancybox we're going to create
            var func = arguments.callee;
            current_url = window.location.href;

            //bind the submit of our new form
            jQuery('#objform-container form').ajaxForm({
                beforeSubmit: function(){
                    jQuery.fancybox.showActivity();
                },
                success:  function(msg){
                    if (typeof(msg) == 'string') {
                        var form = msg.indexOf("form") > -1; // if another form is sent back, it should be displayed
                    } else {
                        var form = false;
                    }
                    if(form) {
                        jQuery.fancybox({content:msg,onComplete:func,scrolling:'no',titleShow:false});
                    } else {
                        // A json object with a url field will be returned in some cases. just redirect to it.
                        jQuery.fancybox.close();
                        if (typeof(msg) == 'object') {
                            window.location.href = msg.url;                        
                        } else {
                            if(jQuery("input.default").attr('value') == 'Delete') { 
                                if(current_url.search("cocktail") != -1 || current_url.search("crystalform") != -1) {
                                    window.location.reload(); 
                                } else { history.go(-1); }
                            } else { window.location.reload(); }
                        }
                    }
                    jQuery.fancybox.hideActivity();
                    return false;
                }
                
            });
        }
    });

    jQuery(".modal-upload-form").fancybox({
	    'scrolling'         : 'no',		
	    'titleShow'         : false,
	    'type'              : 'iframe',
	    'height'			: '65%'
    });
       
}
    
function remove_item(element) {
    jQuery.fancybox.showActivity();
	jQuery.ajax({
        type: "POST",
        url: element.rel,
        data: "",
        success: function() {
            window.location.reload();
        }
    });
}


var dataViewer = function(){

    var  loadingTimer, loadingFrame= 1;
    var  loading = jQuery('#data-image-loading');
    var  wavelength = 1.0;
    var  ref_resol = 2.0;
    var  theta_m = Math.asin(0.5*wavelength)/ref_resol;
    
	function  _animate_loading() {
	    if (!loading.is(':visible')){
		    clearInterval(loadingTimer);
		    return;
	    }
	    jQuery('div', loading).css('top', (loadingFrame * -40) + 'px');
        loadingFrame = (loadingFrame + 1) % 12;
    }
    
    return {
        setPars: function(w, r) {
            wavelength = w;
            ref_resol = r;
            theta_m = Math.asin(0.5*wavelength)/ref_resol;
        },
        calcRes: function(f) {
            return (0.5*wavelength)/Math.sin(f * theta_m)
        },
        showActivity: function() {
	        loading = jQuery('#data-image-loading');
            clearInterval(loadingTimer);
            loading.show();
            loadingTimer = setInterval(_animate_loading, 66);
	    },
	    hideActivity: function() {
	        loading.hide();
	    }
    }
}();

function tooltips() {    
    this.xOffset = -10; // x distance from mouse
    this.yOffset = 20; // y distance from mouse       
    
    $("[title]").unbind().hover(
        function(e) {
            this.t = this.title;
            this.title = ''; 
            this.top = (e.pageY + yOffset); this.left = (e.pageX + xOffset);
            
            $('body').append( '<p id="vtip"><img id="vtipArrow" />' + this.t + '</p>' );
                        
            $('p#vtip #vtipArrow').attr("src", '/img/vtip_arrow.png');
            $('p#vtip').css("top", this.top+"px").css("left", this.left+"px").css("max-width", '18em').fadeIn("slow");
            
        },
        function() {
            this.title = this.t;
            $("p#vtip").fadeOut("slow").remove();
        }
    ).mousemove(
        function(e) {
            this.top = (e.pageY + yOffset);
            this.left = (e.pageX + xOffset);
                         
            $("p#vtip").css("top", this.top+"px").css("left", this.left+"px");
        }
    );                
};

