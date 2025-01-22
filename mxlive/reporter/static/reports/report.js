// d3.legend.js
// (C) 2012 ziggy.jonsson.nyc@gmail.com
// MIT licence

(function () {
    d3.legend = function (g) {
        g.each(function () {
            var g = d3.select(this),
                items = {},
                svg = d3.select(g.property("nearestViewportElement"));

            svg.selectAll("[data-legend]").each(function () {
                var self = d3.select(this);
                items[self.attr("data-legend")] = {
                    pos: self.attr("data-legend-pos") || this.getBBox().y,
                    color: self.attr("data-legend-color") != undefined ? self.attr("data-legend-color") : self.style("fill") != 'none' ? self.style("fill") : self.style("stroke")
                }
            });

            items = d3.entries(items).sort(function (a, b) {
                return a.value.pos - b.value.pos
            });

            g.selectAll("text")
                .data(items).enter()
                .append("text")
                .attr("y", function (d, i) {
                    return i + "em"
                })
                .attr("x", "1em")
                .text(function (d) {
                    return d.key
                });

            g.selectAll("circle")
                .data(items).enter()
                .append("circle")
                .attr("cy", function (d, i) {
                    return i - 0.35 + "em"
                })
                .attr("cx", 0)
                .attr("r", "0.4em")
                .style("fill", function (d) {
                    return d.value.color
                });

        });
        return g
    }
})();

function rounded(v) {
    var exp = Math.pow(10, -Math.ceil(Math.log(Math.abs(v), 10)));
    return Math.round(v * exp) / exp;
}

Array.cleanspace = function (a, b, steps) {
    var A = [];

    steps = steps || 7;
    var min = rounded((b - a) / 8);
    a = Math.ceil(a / min) * min;
    b = Math.floor(b / min) * min;
    var step = Math.ceil(((b - a) / steps) / min) * min;

    A[0] = a;
    while (a + step <= b) {
        A[A.length] = a += step;
    }
    //console.log(A);
    return A;

};

function inv_sqrt(a) {
    var A = [];
    for (var i = 0; i < a.length; i++) {
        A[i] = Math.pow(a[i], -0.5);
    }
    return A;
}


// Live Reports from MxLIVE
function draw_xy_chart() {

    function chart(selection) {
        selection.each(function (datasets) {
            var xoffset = 0; //notes && 40 || 0;
            var margin = {top: 20, right: width * 0.1, bottom: 50, left: width * 0.1},
                innerwidth = width - margin.left - margin.right,
                innerheight = height - margin.top - margin.bottom;
            var xmin = d3.min(datasets, function (d) {
                return d3.min(d.x);
            });
            var xmax = d3.max(datasets, function (d) {
                return d3.max(d.x);
            });
            switch (xscale) {
                case 'inv-square':

                    var x_scale = d3.scalePow().exponent(-2)
                        .range([0, innerwidth])
                        .domain([xmax, xmin]);
                    break;
                case 'pow':
                    var x_scale = d3.scalePow()
                        .range([0, innerwidth])
                        .domain([xmin, xmax]);
                    break;
                case 'log':
                    var x_scale = d3.scaleLog()
                        .range([0, innerwidth])
                        .domain([xmin, xmax]);
                    break;
                case 'identity':
                    var x_scale = d3.scaleIdentity()
                        .range([0, innerwidth])
                        .domain([xmin, xmax]);
                    break;
                case 'time':
                    var x_scale = d3.scaleTime()
                        .range([0, innerwidth])
                        .domain([xmin, xmax]);
                    break;
                case 'linear':
                    var x_scale = d3.scaleLinear()
                        .range([0, innerwidth])
                        .domain([xmin, xmax]);
                    break;
                case 'inverse':
                    var x_scale = d3.scaleLinear()
                        .range([0, innerwidth])
                        .domain([xmax, xmin]);
            }

            var color_scale = d3.scaleOrdinal(d3.schemeCategory10);

            var y1data = [], y2data = [];
            var y1datasets = [], y2datasets = [];
            for (var p = 0; p < datasets.length; p++) {
                datasets[p]['color'] = color_scale(p);
                if ((datasets[p]['y1'])) {
                    y1data = y1data.concat(datasets[p]['y1']);
                    y1datasets.push(datasets[p]);
                }
                if ((datasets[p]['y2'])) {
                    y2data = y2data.concat(datasets[p]['y2']);
                    y2datasets.push(datasets[p]);
                }
            }

            var y1_scale = d3.scaleLinear()
                .range([innerheight - xoffset, 0])
                .domain([d3.min(y1data),
                    d3.max(y1data)]);

            var y2_scale = d3.scaleLinear()
                .range([innerheight - xoffset, 0])
                .domain([d3.min(y2data),
                    d3.max(y2data)]);

            var x_axis = d3.axisBottom()
                .scale(x_scale)
                .tickSize(-innerheight);
            if (xscale === 'inv-square') {

                var ticks = inv_sqrt(Array.cleanspace(Math.pow(xmax, -2), Math.pow(xmin, -2), 8));
                x_axis.tickValues(ticks).tickFormat(d3.format(".3"));
            }

            var y1_axis = d3.axisLeft()
                .scale(y1_scale)
                .tickSize(-innerwidth);

            var y2_axis = d3.axisRight()
                .scale(y2_scale);

            var y1_draw_line = [], y2_draw_line = [];

            for (var p = 0; p < datasets.length; p++) {
                if (datasets[p]['y1']) {
                    y1_draw_line.push(d3.line()
                        .curve(d3.curveCatmullRom)
                        .x(function (d) {
                            return x_scale(d[0]);
                        })
                        .y(function (d) {
                            return y1_scale(d[1]);
                        }));
                } else if (datasets[p]['y2']) {
                    y2_draw_line.push(d3.line()
                        .curve(d3.curveLinear)
                        .x(function (d) {
                            return x_scale(d[0]);
                        })
                        .y(function (d) {
                            return y2_scale(d[1]);
                        }));
                }
            }

            var svg = d3.select(this)
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


            svg.append("g")
                .attr("class", "x axis")
                .attr("transform", "translate(0," + (innerheight) + ")")
                .call(x_axis);
            svg.append("text")
                .attr("transform", "translate(" + (innerwidth / 2) + "," + (height - margin.bottom / 2) + ")")
                .style("text-anchor", "middle")
                .text(xlabel);

            svg.append("g")
                .attr("class", "y axis")
                .call(y1_axis)
                .append("text")
                .attr("transform", "translate(0," + innerheight / 2 + "), rotate(-90)")
                .attr("y", 6)
                .attr("dy", "-3.5em")
                .style("text-anchor", "middle")
                .attr("fill", function (_, i) {
                    if (y1datasets.length > 1) {
                        return "#000000";
                    }
                    return y1datasets[0]['color'];
                })
                .text(y1label);


            if (y2data.length) {
                svg.append("g")
                    .attr("class", "y axis")
                    .attr("transform", "translate(" + innerwidth + ", 0)")
                    .call(y2_axis)
                    .append("text")
                    .attr("transform", "translate(0," + innerheight / 2 + "), rotate(-90)")
                    .attr("y", 55)
                    .attr("dy", 0)
                    .style("text-anchor", "middle")
                    .attr("fill", function (_, i) {
                        if (y2datasets.length > 1) {
                            return "#000000";
                        }
                        return y2datasets[0]['color'];
                    })
                    .text(y2label);
            }

            var y1_data_lines = svg.selectAll(".d3_xy1_chart_line")
                .data(y1datasets.map(function (d) {
                    return d3.zip(d.x, d.y1);
                }))
                .enter().append("g")
                .attr("class", "d3_xy1_chart_line");
            var y2_data_lines = svg.selectAll(".d3_xy2_chart_line")
                .data(y2datasets.map(function (d) {
                    return d3.zip(d.x, d.y2);
                }))
                .enter().append("g")
                .attr("class", "d3_xy2_chart_line");

            for (var p = 0; p < y1_draw_line.length; p++) {
                if (scatter === 'line') {
                    y1_data_lines.append("path")
                        .attr("class", "line")
                        .attr("d", function (d) {
                            return y1_draw_line[p](d);
                        })
                        .attr("data-legend", function (_, l) {
                            return y1datasets[l]['label'] || null;
                        })
                        .attr("stroke", function (_, l) {
                            return y1datasets[l]['color'];
                        })
                        .attr("fill", "none");
                } else {
                    for (k = 0; k < y1datasets.length; k++) {
                        var newdata = y1datasets[k]['x'].map(function (e, j) {
                            return [e, y1datasets[k]['y1'][j]];
                        });
                        var data_points = svg.selectAll("dot")
                            .data(newdata)
                            .enter().append("circle")
                            .attr("r", 2)
                            .attr("cx", function (d) {
                                return x_scale(d[0]);
                            })
                            .attr("cy", function (d) {
                                return y1_scale(d[1]);
                            })
                            .attr("fill", function (_, l) {
                                return y1datasets[k]['color'];
                            });
                    }
                }
            }

            for (var p = 0; p < y2_draw_line.length; p++) {
                if (scatter === 'line') {
                    y2_data_lines.append("path")
                        .attr("class", "line")
                        .attr("d", function (d) {
                            return y2_draw_line[p](d);
                        })
                        .attr("data-legend", function (_, l) {
                            return y2datasets[l]['label'] || null;
                        })
                        .attr("stroke", function (_, l) {
                            return y2datasets[l]['color'];
                        })
                        .attr("fill", "none");
                } else {
                    for (k = 0; k < y2datasets.length; k++) {
                        var newdata = y2datasets[k]['x'].map(function (e, j) {
                            return [e, y2datasets[k]['y2'][j]];
                        });
                        var data_points = svg.selectAll("dot")
                            .data(newdata)
                            .enter().append("circle")
                            .attr("r", 2)
                            .attr("cx", function (d) {
                                return x_scale(d[0]);
                            })
                            .attr("cy", function (d) {
                                return y2_scale(d[1]);
                            })
                            .attr("fill", function (_, l) {
                                return y2datasets[k]['color'];
                            });
                    }
                }
            }

            for (i = 0; i < notes.length; i++) {
                var xpos = notes[i]['x'] && x_scale(notes[i]['x']) || 0,
                    ystart = notes[i]['ystart'] && y1_scale(notes[i]['ystart']) || 0,
                    yend = notes[i]['yend'] && y1_scale(notes[i]['yend']) || innerheight - xoffset;

                svg.append("path")
                    .attr('class', notes[i]['label'] + ' ' + (notes[i]['class'] || '') + ' ' + (notes[i]['display'] !== null && (notes[i]['display'] === true && 'visible ' || 'hidden')) || 'visible')
                    .style("stroke", notes[i]['color'] || "#333")
                    .attr("d", function () {
                        var d = "M" + xpos + "," + yend;
                        d += " " + xpos + "," + ystart;
                        return d;
                    });
                svg.append("text")
                    .attr('class', notes[i]['label'] + ' ' + (notes[i]['class'] || '') + ' ' + (notes[i]['display'] !== null && (notes[i]['display'] === true && 'visible ' || 'hidden')) || 'visible')
                    .text(notes[i]['label'])
                    .style("fill", notes[i]['color'] || "#333")
                    .attr("transform", "translate(" + (xpos + 3) + "," + (y1_scale(0) + xoffset / 2) + "), rotate(-90)")
                    .style("text-anchor", "middle");
            }

            legend = svg.append("g")
                .attr("class", "legend")
                .attr("transform", "translate(50,30)")
                .call(d3.legend);


            /* Interactive stuff */
            var mouseG = svg.append("g")
                .attr("class", "mouse-over-effects");

            mouseG.append("path") // this is the black vertical line to follow mouse
                .attr("class", "mouse-line")
                .style("stroke", "#333")
                .style("stroke-width", "0.5px")
                .style("opacity", "0");

            var lines = this.getElementsByClassName('line');

            if (y2datasets) {
                var dualdatasets = [];
                for (var p = 0; p < y1datasets.length; p++) {
                    dualdatasets.push({'x': y1datasets[p]['x'], 'y1': y1datasets[p]['y1']});
                }
                for (var p = 0; p < y2datasets.length; p++) {
                    dualdatasets.push({'x': y2datasets[p]['x'], 'y1': y2datasets[p]['y2'], 'scale': y2_scale});
                }
                var mousePerLine = mouseG.selectAll('.mouse-per-line')
                    .data(dualdatasets)
                    .enter()
                    .append("g")
                    .attr("class", "mouse-per-line");
            } else {
                var mousePerLine = mouseG.selectAll('.mouse-per-line')
                    .data(datasets)
                    .enter()
                    .append("g")
                    .attr("class", "mouse-per-line");
            }

            mousePerLine.append("circle")
                .attr("r", 2)
                .style("fill", "none")
                .style("stroke-width", "4px")
                .style("opacity", "0");

            mousePerLine.append("text")
                .attr("transform", "translate(10,3)");

            mouseG.append('rect')
                .attr('width', innerwidth)
                .attr('height', innerheight)
                .attr('fill', 'none')
                .attr('pointer-events', 'all')
                .on('mouseout', function () {
                    svg.select(".mouse-line").style("opacity", "0");
                    svg.selectAll(".mouse-per-line circle").style("opacity", "0");
                    svg.selectAll(".mouse-per-line text").style("opacity", "0");
                })
                .on('mouseover', function () {
                    svg.select(".mouse-line").style("opacity", "1");
                    svg.selectAll(".mouse-per-line circle").style("opacity", "1");
                    svg.selectAll(".mouse-per-line text").style("opacity", "1");
                })
                .on('mousemove', function () {
                    var mouse = d3.mouse(this);
                    svg.select(".mouse-line")
                        .attr("d", function () {
                            var d = "M" + mouse[0] + "," + innerheight;
                            d += " " + mouse[0] + "," + 0;
                            return d;
                        });
                    svg.selectAll(".mouse-per-line")
                        .style("stroke", function (d, n) {
                            return color_scale(n);
                        })
                        .attr("transform", function (d, n) {
                            var xPos = x_scale.invert(mouse[0]);
                            var closest = d['x'].reduce(function (prev, curr) {
                                return (Math.abs(curr - xPos) < Math.abs(prev - xPos) ? curr : prev);
                            });
                            var i = d['x'].indexOf(closest);

                            var scale = d['scale'] || y1_scale;
                            var pos = scale(d['y1'][i]);
                            d3.select(this).select('text')
                                .style("stroke", "none")
                                .text(scale.invert(pos).toFixed(2));
                            return "translate(" + x_scale(closest) + "," + pos + ")";
                        });
                });
            /* End of interactive stuff */

        });

    }

    chart.width = function (value) {
        if (!arguments.length) return width;
        width = value;
        return chart;
    };

    chart.height = function (value) {
        if (!arguments.length) return height;
        height = value;
        return chart;
    };

    chart.xlabel = function (value) {
        if (!arguments.length) return xlabel;
        xlabel = value;
        return chart;
    };

    chart.y1label = function (value) {
        if (!arguments.length) return y1label;
        y1label = value;
        return chart;
    };

    chart.y2label = function (value) {
        if (!arguments.length) return y2label;
        y2label = value;
        return chart;
    };

    chart.xscale = function (value) {
        if (!arguments.length) return xscale;
        xscale = value;
        return chart;
    };
    chart.scatter = function (value) {
        if (!arguments.length) return scatter;
        scatter = value;
        return chart;
    };
    chart.notes = function (value) {
        if (!arguments.length) return notes || [];
        notes = value;
        return chart;
    };

    return chart;
}


// Report Builder from MxLIVE
function build_report(selector, report) {
    var converter = new showdown.Converter();
    $.each(report['details'], function (i, section) {
        var section_box = $(selector).append('<section class="container" id="section-' + i + '"></section>').children(":last-child");
        section_box.append("<div class='col-xs-12'><h3 class='section-title' >" + section['title'] + "</h3><hr class='hr-xs'/></div>");
        section_box.addClass(section['style'] || '');
        if (section['description']) {
            section_box.append("<div class='col-xs-12'>" + converter.makeHtml(section['description']) + "</div>");
        }
        $.each(section['content'], function (j, entry) {
            var entry_row = section_box.append("<div class='col-xs-12' id='entry-" + i + "-" + j + "'></div>").children(":last-child");
            entry_row.addClass(entry['style'] || '');
            if (entry['title']) {
                if (!entry['kind']) {
                    entry_row.append("<h4>" + entry['title'] + "</h4>")
                }
            }
            if (entry['description']) {
                entry_row.append("<div class='description'>" + converter.makeHtml(entry['description']) + "</div>")
            }
            if (entry['kind'] === 'table') {
                if (entry['data']) {
                    var table = $("<table id='table-" + i + "-" + j + "' class='table table-hover table-condensed'></table>");
                    var thead = $('<thead></thead>');
                    var tbody = $('<tbody></tbody>');

                    $.each(entry['data'], function (l, line) {
                        if (line) {
                            var tr = $('<tr></tr>');
                            for (k = 0; k < line.length; k++) {
                                if ((k === 0 && entry['header'] === 'column') || (l === 0 && entry['header'] === 'row')) {
                                    var td = $('<th></th>').text(line[k]);
                                } else {
                                    var td = $('<td></td>').text(line[k]);
                                }
                                tr.append(td);
                            }
                            if (entry['header'] === 'row' && l === 0) {
                                thead.append(tr);
                            } else {
                                tbody.append(tr);
                            }
                        }
                    });
                    if (entry['title']) {
                        table.append("<caption class='text-center'>Table " + ($('table').length + 1) + '. ' + entry['title'] + "</caption>");
                    }
                    table.append(thead);
                    table.append(tbody);
                    entry_row.append(table);
                }
            } else if (entry['kind'] === 'lineplot' || entry['kind'] === 'scatterplot') {
                $("#entry-" + i + "-" + j).append("<figure id='figure-" + i + "-" + j + "'></figure>");
                var data = [];
                var xlabel = entry['data']['x'].shift();
                var xscale = entry['data']['x-scale'] || 'linear';
                var y1label = '', y2label = '';
                $.each(entry['data']['y1'], function (l, line) {
                    y1label = line.shift();
                    data.push({'label': y1label, 'x': entry['data']['x'], 'y1': line});
                });
                $.each(entry['data']['y2'], function (l, line) {
                    y2label = line.shift();
                    data.push({'label': y2label, 'x': entry['data']['x'], 'y2': line});
                });
                var width = section_box.width();
                y1label = entry['data']['y1-label'] || y1label;
                y2label = entry['data']['y2-label'] || y2label;

                var xy_chart = draw_xy_chart()
                    .width(width)
                    .height(400)
                    .xlabel(xlabel)
                    .y1label(y1label)
                    .y2label(y2label)
                    .xscale(xscale)
                    .notes([])
                    .scatter(entry['kind'] === 'scatterplot' && 'scatter' || entry['kind'] === 'lineplot' && 'line');
                var svg = d3.select('#figure-' + i + '-' + j).append("svg").attr('id', 'plot-' + i + "-" + j)
                    .datum(data)
                    .call(xy_chart);
                if (entry['title']) {
                    $('#figure-' + i + '-' + j).append("<figcaption class='text-center'>Figure " + ($('svg').length) + '. ' + entry['title'] + "</figcaption>")
                }
            }
            if (entry['notes']) {
                entry_row.append("<div class='notes well'>" + converter.makeHtml(entry['notes']) + "</div>");
            }
        });

    });
}