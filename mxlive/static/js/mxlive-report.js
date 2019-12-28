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
    let b = row[row.length - 1];
    let min = ((b - a) / steps).toPrecision(1);
    return Math.max(0, Math.ceil(Math.log10(1 / min)) || 2)
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


const scheme4 = [
    "#8f9f9a", "#c56052", "#9f6dbf", "#a0b552"
];
const scheme8 = [
    "#67aec1", "#c7588a", "#64c192", "#cc5c3e",
    "#a39384", "#829aba", "#afc441", "#9565c9",
];
const scheme14 = [
    "#67aec1", "#c45a81", "#cdc339", "#ae8e6b",
    "#6dc758", "#a084b6", "#667ccd", "#cd4f55",
    "#805cd6", "#cf622d", "#a69e4c", "#9b9795",
    "#6db586", "#c255b6"
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


function drawXYChart(figure, chart, options, type = 'spline') {
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
    $.each(chart.data.y1, function (i, line) {  // y1
        columns.push(line);
        axes[line[0]] = 'y';
        colors[line[0]] = options.scheme[index++];
        axis_opts.y.label = line[0];
    });

    // gather y axes data
    $.each(chart.data.y2, function (i, line) {  // y2
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
        zoom: {enabled: true, type: 'drag'},
        onresize: function () {
            this.api.resize({
                width: figure.width(),
                height: figure.width() * options.height / options.width
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
                height: figure.width() * options.height / options.width
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
            y: {
                type: yscale
            }
        },
        legend: {hide: true},
        grid: {y: {show: true}},
        bar: {width: {ratio: 0.5}},
        onresize: function () {
            this.api.resize({
                width: figure.width(),
                height: figure.width() * options.height / options.width
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

    $.each(chart.data, function (i, item) {
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
                height: figure.width() * options.height / options.width
            });
        }
    });
}


function drawScatterChart(figure, chart, options) {
    drawXYChart(figure, chart, options, 'scatter');
}

function callout(g, value, color) {
    if (!value) return g.style("display", "none");

    if (g.attr('data-label')) {
        value = `${value} - ${g.attr('data-label')}`;
    }
    g.attr('data-label');

    g.style("display", null)
        .style("pointer-events", "none")
        .style("font", "10px sans-serif");

    const path = g.selectAll("path")
        .data([null])
        .join("path")
        .attr("fill", "var(--warning)")
        .attr("stroke", "black");

    const text = g.selectAll("text")
        .data([null])
        .join("text")
        .call(text => text
            .selectAll("tspan")
            .data((value + "").split(/\n/))
            .join("tspan")
            .attr("x", 0)
            .attr("y", (d, i) => `${i * 1.1}rem`)
            .style("font-weight", (_, i) => i ? null : "bold")
            .text(d => d));

    const {x, y, width: w, height: h} = text.node().getBBox();

    text.attr("transform", `translate(${-w / 2},${10 - y})`);
    path.attr("d", `M${-w / 2 - 10},5H-5l5,-5l5,5H${w / 2 + 10}v${h + 10}h-${w + 20}z`);
}


function drawTimeline(figure, chart, options) {

    let types = [];
    let margin = {top: 10, right: 10, bottom: 10, left: 10};
    let width = figure.width() - margin.left - margin.right;
    let height = 240;
    let xcenter = width / 2;
    // assign colors
    $.each(chart.data, function (i, entry) {
        if (!types.includes(entry.type)) {
            types.push(entry.type);
        }
    });

    types.sort();

    let colors = d3.scaleOrdinal().domain(types).range(scheme14);
    let timeline = d3.timeline()
        .size([width, 150])
        .extent([chart.start, chart.end])
        .bandStart(d => d.start)
        .bandEnd(d => d.end)
        .padding(2);

    let timelineBands = timeline(chart.data);
    let x_scale = d3.scaleLinear()
        .domain([chart.start, chart.end])
        .range([0, width]);

    let x_axis = d3.axisBottom()
        .scale(x_scale)
        .tickFormat(d3.timeFormat('%H:%M'));

    let svg = d3.select(`#${figure.attr('id')}`)
        .append('svg')
        .attr('viewBox', `-${margin.left} -${margin.top} ${figure.width()} ${height}`)
        .attr('class', 'w-100');

    // add events
    svg.selectAll("rect.event")
        .data(timelineBands)
        .enter()
        .append("rect")
        .attr('class', 'event')
        .attr("x", function (d) {
            return d.start
        })
        .attr("x", function (d) {
            return d.start
        })
        .attr("y", function (d) {
            return d.y
        })
        .attr("height", function (d) {
            return d.dy
        })
        .attr("width", function (d) {
            return d.end - d.start
        })
        .attr("data-label", d => `${d.label}`)
        .attr("data-type", d => d.type)
        .attr('shape-rendering', 'geometricPrecision')
        .style("fill", d => colors(d.type))
        .style("stroke", d => colors(d.type))
        .attr('pointer-events', 'all')
        .on('mouseover', function () {
            tooltip.attr('data-label', $(this).data("label"));
        })
        .on('mouseout', function () {
            tooltip.attr('data-label', null);
        });

    // add x-axis
    svg.append("g")
        .call(x_axis)
        .attr("transform", "translate(0, 160)");

    // Add legend
    let size = 10;
    let left = 0;
    let offset = 80;
    let legend = svg.append("g");
    let legends = legend.selectAll(".legend")
        .data(types)
        .enter()
        .append("g")
        .attr('class', "legend")
        .attr('data-type', function (d, i) {
            return d
        })
        .attr('transform', function (d, i) {
            if (i === 0) {
                left = d.length + offset;
                return "translate(0,0)"
            } else {
                let curpos = left;
                left += d.length + offset;
                return `translate(${curpos}, 0)`;
            }
        })
        .on('mouseover', function () {
            let selector = $(this).data('type');
            svg.selectAll(`rect.event:not([data-type="${selector}"])`)
                .style('opacity', .1);
        })
        .on('mouseout', function () {
            svg.selectAll('rect')
                .style('opacity', 1);
        });

    legends.append('rect')
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', size)
        .attr('height', size)
        .style("fill", d => colors(d));
    legends.append('text')
        .attr('x', size + 10)
        .attr('y', size)
        .text(function (d, i) {
            return d
        })
        .style('text-anchor', 'start')
        .style('font-size', '10');

    // center legend in position
    let legendx = xcenter - left / 2;
    let legendy = height - margin.bottom - 30;
    legend.attr('transform', `translate(${legendx}, ${legendy})`);


    // mouse cursor and tooltip
    const tooltip = svg.append("g");
    const cursor = svg.append("g")
        .attr('class', 'mouse-cursor')
        .append("path")
        .attr('class', "mouse-line")
        .style('stroke', "var(--warning)")
        .style('stroke-width', '1px')
        .style('opacity', "0")
        .attr('pointer-events', 'none');

    svg
        .on('mouseleave', function () {
            d3.select('.mouse-line').style('opacity', 0);
            tooltip.call(callout, null);
        })
        .on('touchmove mousemove', function () {
            const mouse = d3.mouse(this);
            const info = d3.timeFormat('%a %H:%M')(x_scale.invert(mouse[0]));
            if (mouse[1] < 165) {
                d3.select('.mouse-line')
                    .style("opacity", 1)
                    .attr("d", function () {
                        return `M ${mouse[0]}, 160, ${mouse[0]} 0`;
                    });
                tooltip
                    .attr("transform", `translate(${mouse[0]}, 164)`)
                    .call(callout, info);
            } else {
                d3.select('.mouse-line').style('opacity', 0);
                tooltip.call(callout, null);
            }
        });

    // remove raw data from dom
    figure.removeData('chart').removeAttr('data-chart');

    // adjust font-size on resize
    window.onresize = function () {
        let scale = width / figure.width();
        svg.selectAll("text")
            .attr('transform', `scale(${scale} ${scale})`);
        svg.selectAll("line")
            .attr('stroke-width', `${scale}px`);
    }
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
                    drawScatterChart(figure, chart, options);
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