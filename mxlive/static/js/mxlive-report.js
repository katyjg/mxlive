function rounded(v) {
    return v.toPrecision(1);
}

function choose(choices) {
    let index = Math.floor(Math.random() * choices.length);
    return choices[index];
}



function getPrecision(row, steps) {
    steps = steps || 8;
    let a = row[0];
    let b = row[row.length-1];
    let min = ((b - a) / steps).toPrecision(1);
    return Math.max(0, Math.ceil(Math.log10(1/min)) || 2)
}

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

const figureTypes = [
    "histogram", "lineplot", "barchart", "scatterplot", "pie", "gauge", "timeline"
];


const scheme4 = ["#a0b552", "#c56052", "#9f6dbf", "#8f9f9a"];
const scheme8 = [
    "#afc441", "#cc5c3e", "#64c192", "#9aa156", "#829aba", "#9565c9", "#c7588a", "#a39384"
];
const scheme14 = [
    "#cdc339", "#67aec1", "#c45a81", "#6dc758", "#a084b6", "#667ccd", "#c255b6", "#6db586", "#cd4f55", "#805cd6",
    "#cf622d", "#a69e4c", "#ae8e6b", "#9b9795"
];

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
    '       <figure id="figure-<%= id %>" data-type="<%= entry.kind %>" data-chart=\'<%= JSON.stringify(entry) %>\' >' +
    '       </figure>' +
    '   <% }%>' +
    '   <% if (entry.notes) { %>' +
    '       <div class="notes"><%= renderMarkdown(entry.notes) %></div>' +
    '   <% } %>' +
    '</div>'
);

var sectionTemplate = _.template(
    '<section id="section-<%= id %>" <% let style = section.style || "col-12"; %>' +
    '       class="<%= style %>">' +
    '       <%  if (section.title)  {%>' +
    '       <h3 class="section-title col-12"><%= section.title %></h3>' +
    '       <% } %>' +
    '       <%  if (section.description)  {%>' +
    '       <div class="description"><%= renderMarkdown(section.description) %></div>' +
    '       <% } %>' +
    '     <% _.each(section.content, function(entry, j){ %><%= contentTemplate({id: id+"-"+j, entry: entry}) %><% }); %>' +
    '</section>'
);

var tableTemplate = _.template(
    '<table id="table-<%= id %>" class="table table-sm table-hover">' +
    '<% if (entry.title) { %>' +
    '   <caption class="text-center"><%= entry.title %></caption>' +
    '<% } %>' +
    '<% if (entry.header.includes("row")) { %>' +
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


function drawXYChart(figure, chart, options, type='spline') {
    let colors = {};
    let columns = [];
    let axes = {};
    let data_type = type;
    let spline_opts = {interpolation: {}};
    let axis_opts = {x: {}, y: {}, y2: {}};
    let xdata = [];

    // Axis limits
    if (chart.data['x-limits']) {
        axis_opts.x.min = chart.data['x-limits'][0] || null;
        axis_opts.x.max = chart.data['x-limits'][0] || null;
    }
    if (chart.data['y1-limits']) {
        axis_opts.y.min = chart.data['y1-limits'][0] || null;
        axis_opts.y.max = chart.data['y1-limits'][0] || null;
    }
    if (chart.data['y2-limits']) {
        axis_opts.y2.min = chart.data['y2-limits'][0] || null;
        axis_opts.y2.max = chart.data['y2-limits'][0] || null;
    }

    // Spline Plo type
    if (["cardinal", "basis", "step", "step-before", "step-after"].includes(chart.data['interpolation'])) {
        data_type = 'spline';
        spline_opts.interpolation.type = chart.data['interpolation'];
    }

    // configure x-axis interpolation
    if (chart.data['x-scale'] === 'time') {
        axis_opts.x = {
            type: 'timeseries',
            tick: {format: chart.data['time-format']}
        };

        // convert x values to time series
        $.each(chart.data.x, function (i, value) {
            if (i === 0) {
                xdata.push(value)  // series label
            } else {
                xdata.push(Date.parse(value))
            }
        });
    } else {
        xdata = chart.data.x;
        let xvalues = xdata.slice(1, xdata.length);
        let prec = getPrecision(xvalues);
        let xconv = d3.interpolateDiscrete(xvalues);
        axis_opts.x = {
            type: 'category',
            tick: {
                centered: true,
                fit: false,
                multiline: false,
                culling: {max: 8},
                format: function (x) {
                    let val = x / (xvalues.length);
                    return xconv(val).toFixed(prec);
                }
            }
        };
    }

    // remove raw data from dom, not needed anymore
    figure.removeData('chart').removeAttr('data-chart');

    // gather columns data and configure labels and color
    columns.push(xdata);  // add x-axis
    let index = 0;
    $.each(chart.data.y1, function(i, line){  // y1
        columns.push(line);
        axes[line[0]] = 'y';
        colors[line[0]] = options.scheme[index++];
        axis_opts.y.label = line[0];
    });

    // gather y axes data
    $.each(chart.data.y2, function(i, line){  // y2
        columns.push(line);
        axes[line[0]] = 'y2';
        colors[line[0]] = options.scheme[index++];
        axis_opts['y2'] = {show: true, label: line[0]};
    });

    c3.generate({
        bindto: `#${figure.attr('id')}`,
        size: {width: options.width, height: options.height},
        data: {
            type: data_type,
            columns: columns,
            colors: colors,
            axes: axes,
            x: chart.data.x[0],
        },
        spline: spline_opts,
        point: {show: (chart.data.x.length < 15)},
        axis: axis_opts,
        grid: {y: {show: true}},
        zoom: {  enabled: true,   type: 'drag'},
        onresize: function () {
            this.api.resize({
                width: figure.width(),
                height: figure.width()*options.height/options.width
            });
        }
    });
}


function drawBarChart(figure, chart, options) {
    let series = [];
    let colors = {};

    // remove raw data from dom
    figure.removeData('chart');
    figure.removeAttr('data-chart');

    // series names
    let index = 0;
    $.each(chart.data["data"][0], function (key, value) {
        if (key !== chart.data["x-label"]) {
            series.push(key);
            colors[key] = options.scheme[index++];
        }
    });
    c3.generate({
        bindto: `#${figure.attr('id')}`,
        size: {width: options.width, height: options.height},
        data: {
            type: 'bar',
            json: chart.data["data"],
            colors: colors,
            keys: {
                x: chart.data["x-label"],
                value: series
            },
            groups: chart.data.stack || [],
        },
        grid: {y: {show: true}},
        axis: {x: {type: 'category', label: chart.data['x-label']}},
        legend: {hide: (series.length === 1)},
        bar: {width: {ratio: 0.85}},
        onresize: function () {
            this.api.resize({
                width: figure.width(),
                height: figure.width()*options.height/options.width
            });
        }
    });
}


function drawHistogram(figure, chart, options) {
    let yscale = chart['y-scale'];

    // remove raw data from dom
    figure.removeData('chart');
    figure.removeAttr('data-chart');


    c3.generate({
        bindto: `#${figure.attr('id')}`,
        size: {width: options.width, height: options.height},
        data: {
            type: 'bar',
            json: chart.data,
            colors: {
                y: options.scheme[figure.parent().index()]
            },
            keys: {
                x: 'x', value: ['y']
            },
        },
        axis: {
            x: {
                tick: {
                    fit: false,
                    count: 10,
                    format: v => v.toFixed(1)
                }
            },
            y : {
                type: yscale
            }
        },
        legend: {hide: true},
        grid: {y: {show: true}},
        bar: {width: {ratio: 0.5}},
        onresize: function () {
            this.api.resize({
                width: figure.width(),
                height: figure.width()*options.height/options.width
            });
        }
    });
}

function drawPieChart(figure, chart, options) {
    let data = {};
    let series = [];
    let colors = {};

    // remove raw data from dom
    figure.removeData('chart');
    figure.removeAttr('data-chart');

    $.each(chart.data, function(i, item){
        data[item.label] = item.value;
        series.push(item.label);
        colors[item.label] = options.scheme[i];
    });

    c3.generate({
        bindto: `#${figure.attr('id')}`,
        size: {width: options.width, height: options.height},
        data: {
            type: 'pie',
            json: [data],
            colors: colors,
            keys: {
                value: series
            },
        },
        onresiz1e: function () {
            this.api.resize({
                width: figure.width(),
                height: figure.width()*options.height/options.width
            });
        }
    });
}


function drawScatterChart(figure, chart, options) {
    drawXYChart(figure, chart, options, 'scatter');
}

function drawTimeline(figure, chart, options) {
    let colors = d3.scaleOrdinal(d3.schemeDark2);


    // remove raw data from dom
    figure.removeData('chart').removeAttr('data-chart');


    const myChart = TimelinesChart()(document.getElementById(`${figure.attr('id')}`));
    myChart.data(chart.data)
        .zColorScale(colors)
        .width(figure.width());
}


(function ($) {
    $.fn.liveReport = function (options) {
        let target = $(this);
        let defaults = {
            data: {},
        };
        let settings = $.extend(defaults, options);

        target.addClass('report-viewer');
        $.each(settings.data.details, function (i, section) {
            target.append(sectionTemplate({id: i, section: section}))
        });

        target.find('figure').each(function () {
            let figure = $(this);
            let chart = figure.data('chart');
            let options = {
                width: figure.width(),
                height: figure.width() * 9 / 16,
                scheme: chart.data['colors'] || scheme14
            };
            switch (figure.data('type')) {
                case 'barchart':
                    drawBarChart(figure, chart, options);
                    break;
                case 'lineplot':
                    drawXYChart(figure, chart, options, 'line');
                    break;
                case 'histogram':
                    drawHistogram(figure, chart, options);
                    break;
                case 'pie':
                    drawPieChart(figure, chart, options);
                    break;
                case 'scatterplot':
                    drawXYChart(figure, chart, options, 'scatter');
                    break;
                case 'timeline':
                    drawTimeline(figure, chart, options);
                    break;
            }
            
            // caption
            if (chart.title) {
                figure.after(`<figcaption class="text-center">${chart.title}</figcaption>`);
            } else {
                figure.after(`<figcaption class="text-center"></figcaption>`);
            }

            // fix viewbox
            /*figure.find('svg[width]').each(function(){
                let viewbox = `0 0 ${$(this).width()} ${$(this).height()}`;
                $(this).attr('viewBox', viewbox);
            });*/

        });

    };
}(jQuery));