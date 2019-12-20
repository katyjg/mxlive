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

var contentTemplate = _.template(
    '<div id="entry-<%= id %>" <% let style = entry.style || ""; %>' +
    '       class="section-entry <%= style %>">' +
    '       <%  if ((entry.title) &! (entry.kind))  {%>' +
    '       <h4><%= entry.title %></h4>' +
    '       <% } %>' +
    '       <%  if (entry.description)  {%>' +
    '       <%     let html = markdown.makeHTML(entry.description); %>' +
    '       <div class="description"><%= html %></div>' +
    '       <% } %>' +
    '       <%  if ((entry.kind === "table") && (entry.data))  {%>' +
    '       <% let html = buildTable(entry, id); %>' +
    '       <%= html %>' +
    '       <% } %>' +
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



function buildTable(entry, id) {
    let table = $('<table></table>');
    table.attr('id', 'table-'+id);
    table.addClass('table table-hover table-sm');
    if ((entry.kind === 'table') && (entry.data)) {
        console.log(entry);
        let thead = $('<thead></thead>');
        let tbody = $('<tbody></tbody>');

        $.each(entry.data, function (l, line) {
            if (line) {
                let tr = $('<tr></tr>');
                $.each(line, function(k, datum) {
                    let td =  '';
                    if ((k === 0 && entry.header.includes('column')) || (l === 0 && entry.header.includes('row'))) {
                        td = $('<th></th>').text(line[k]);
                    } else {
                        td = $('<td></td>').text(line[k]);
                    }
                    tr.append(td);
                });

                if (entry.header.includes('row') && l === 0) {
                    thead.append(tr);
                } else {
                    tbody.append(tr);
                }
            }
        });
        table.append(thead);
        table.append(tbody);
        if (entry.title) {
            table.append("<caption class='text-center'>Table " + ($('table').length + 1) + '. ' + entry['title'] + "</caption>");
        }

    }
    console.log(table[0]);
    return table[0].outerHTML;
}

var tableTemplate = _.template(
    '<table id="table-<%= id %>" class="table table-sm table-hover">' +
    '<thead></thead>' +
    '<tbody></tbody>' +
    '</table>'

);

(function ($) {
    $.fn.liveReport = function (options) {
        let target = $(this);
        let defaults = {
            data: {},
            scheme: d3.schemeSet2.concat(d3.schemeDark2)
        };
        let settings = $.extend(defaults, options);
        let markdown = new showdown.Converter();
        target.addClass('report-viewer');
        $.each(settings.data.details, function (i, section) {
            target.append(sectionTemplate({id: i, section: section}))
        });
    };
}(jQuery));