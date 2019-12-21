function rounded(v) {
    let exp = Math.pow(10, -Math.ceil(Math.log(Math.abs(v), 10)));
    return Math.round(v * exp) / exp;
}

function choose(choices) {
    let index = Math.floor(Math.random() * choices.length);
    return choices[index];
}

Array.cleanspace = function (a, b, steps) {
    let A = [];
    let min = rounded((b - a) / 8);

    steps = steps || 7;
    a = Math.ceil(a / min) * min;
    b = Math.floor(b / min) * min;
    let step = Math.ceil(((b - a) / steps) / min) * min;

    A[0] = a;
    while (a + step <= b) {
        A[A.length] = a += step;
    }
    return A;
};

function inv_sqrt(a) {
    let A = [];
    $.each(a, function (i, value) {
        A[i] = Math.pow(value, -0.5);
    });
    return A;
}

function renderMarkdown(text) {
    let markdown = new showdown.Converter();
    return markdown.makeHtml(text);
}

var figureTypes = ["histogram", "lineplot", "barchart", "pie", "gauge"];

var contentTemplate = _.template(
    '<div id="entry-<%= id %>" <% let style = entry.style || ""; %> class="section-entry <%= style %>" >' +
    '   <% if ((entry.title) &! (entry.kind))  { %>' +
    '       <h4><%= entry.title %></h4>' +
    '   <% } %>' +
    '   <% if (entry.description) { %>' +
    '       <div class="description"><%= renderMarkdown(entry.description) %></div>' +
    '   <% } %>' +
    '   <% if ((entry.kind === "table") && (entry.data)) { %>' +
    '       <%= tableTemplate({id: id, entry: entry}) %>' +
    '   <% } else if (figureTypes.includes(entry.kind)) { %>' +
    '       <figure id="figure-<%= id %>" data-chart=\'<%= JSON.stringify(entry) %>\' >' +
    '       <% if (entry.title) { %>' +
    '           <figcaption class="text-center"><%= entry.title %></figcaption>' +
    '       <% } %>' +
    '       </figure>' +
    '   <% }%>' +
    '</div>'
);

var sectionTemplate = _.template(
    '<section id="section-<%= id %>" <% let style = section.style || "col-12"; %>' +
    '       class="<%= style %>">' +
    '       <%  if (section.title)  {%>' +
    '       <h3 class="section-title col-12"><%= section.title %></h3>' +
    '       <% } %>' +
    '       <%  if (section.description)  {%>' +
    '       <%     let html = markdown.makeHTML(section.description); %>' +
    '       <div class="description"><%= html %></div>' +
    '       <% } %>' +
    '     <% _.each(section.content, function(entry, j){ %><%= contentTemplate({id: id+"-"+j, entry: entry}) %><% }); %>' +
    '</section>'
);

var tableTemplate = _.template(
    '<table id="table-<%= id %>" class="table table-sm table-hover">' +
    '<%   if (entry.header.includes("row")) { %>' +
    '   <thead><tr>' +
    '       <% _.each(entry.data[0], function(cell, i){ %>' +
    '       <th><%= cell %></th>' +
    '       <% }); %>' +
    '   </tr></thead>' +
    '<% } %>' +
    '<tbody>' +
    '<% _.each(entry.data, function(row, j){ %>' +
    '   <% if ((!entry.header.includes("row")) || (j>0)) { %>' +
    '       <tr>' +
    '       <% _.each(row, function(cell, i){ %>' +
    '           <% if (entry.header.includes("column") && (i==0)) { %>' +
    '               <th><%= cell %></th>' +
    '           <% } else { %>' +
    '               <td><%= cell %></td>' +
    '           <% } %>' +
    '       <% }); %>' +
    '       </tr>' +
    '   <% } %>' +
    '<% }); %>' +
    '</tbody>' +
    '</table>'
);

(function ($) {
    $.fn.liveReport = function (options) {
        let target = $(this);
        let defaults = {
            data: {},
            scheme: d3.schemeSet2
        };
        let settings = $.extend(defaults, options);

        target.addClass('report-viewer');
        $.each(settings.data.details, function (i, section) {
            target.append(sectionTemplate({id: i, section: section}))
        });

        target.find('figure').each(function(){
            let chart = $(this).data('chart');
            if (chart.kind === 'histogram') {
                let data = [];
                let xkey = chart.data['x-label'];
                
                $.each(chart['data'].data, function(i, item){
                    let xvalue = item[xkey];
                    $.each(item, function(key, yvalue){
                        let point = {};
                        point['name'] = key;
                        point['value'] = yvalue;
                        point[xkey] = xvalue;
                        data.push(point);
                    });
                });
                $(this).height($(this).width()*9/16);
                var visualization = d3plus.viz()
                    .container("#"+$(this).attr('id'))
                    .data(data)
                    .type("bar")
                    .id("name")
                    .x(xkey)
                    .y("value")
                    .draw();
            }
        });
        
    };
}(jQuery));