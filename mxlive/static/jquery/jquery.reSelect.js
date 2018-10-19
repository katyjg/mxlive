/*!
 * jquery.reSelect() - v0.0.1
 * 2014-07-18
 *
 * Copyright 2014 Michel Fodje
 * @license http://www.opensource.org/licenses/mit-license.html MIT License
 * @license http://www.gnu.org/licenses/gpl.html GPL License 
 */
(function( $ ) {
    $.fn.reSelect = function() {
        this.filter( "select" ).each(function() {
            $(this).wrap("<div class='reselect'></div>");
        }); 
        return this;
    };
}( jQuery ));

