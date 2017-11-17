function rounded(v) {
    var exp = Math.pow(10, -Math.ceil(Math.log(Math.abs(v), 10)));
    return Math.round(v*exp)/exp;
}

Array.cleanspace = function(a, b, steps){
    var A= [];

    steps = steps || 7;
    var min =  rounded((b - a)/8);
    a = Math.ceil(a/min)*min;
    b = Math.floor(b/min)*min;
    var step = Math.ceil(((b - a)/steps)/min)*min;

    A[0]= a;
    while(a+step<= b){
        A[A.length]= a+= step;
    }
    return A;
};

function inv_sqrt(a) {
    var A = [];
    for (var i=0; i < a.length; i++) {
        A[i] = Math.pow(a[i], -0.5);
    }
    return A;
};


// Live Reports from MxLIVE
function draw_pie_chart() {

    function chart(selection) {
        selection.each(function (data) {
            var margin = {out: 10, left: width * 0.1};

            var svg = d3.select(this)
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.left + ")");

            var radius = width/2 - margin.left;

            var arc = d3.arc()
                    .innerRadius((radius)*innerRadius)
                    .outerRadius(radius)
                    .startAngle(function(d, i) {
                        return deg2rad(data[i]['start']);
                    })
                    .endAngle(function(d, i) {
                        return deg2rad(data[i]['start'] + data[i]['value']);
                    });

            function deg2rad(deg) {
                return deg * Math.PI / 180;
            }


            function centerTranslation() {
                return 'translate('+radius +','+ radius +')';
            }

            var centerTx = centerTranslation();

            var arcs = svg.append('g')
                    .attr('class', 'arc')
                .attr('transform', centerTx);
            arcs.selectAll('path')
                    .data(data)
                    .enter().append('path')
                    .attr('fill', function(d, i) {
                        return data[i]['color'];
                    })
                    .attr('d', arc);

            var lg = svg.append('g')
                    .attr('class', 'label')
                    .attr('transform', centerTx);

            var labels = [];
            $.each(data, function(i, d) {
                if (d['label']) {
                    labels.push(d['label']);
                }
            });

            if (labels.length > 1) {
                lg.selectAll('text')
                    .data(data)
                    .enter().append('text')
                    .attr('transform', function (d, i) {
                        var r = radius + margin.out;
                        var alpha = deg2rad((data[i]['value'] / 2) + data[i]['start'] - 90);
                        var x = r * Math.cos(alpha);
                        var y = r * Math.sin(alpha);
                        return 'translate(' + (x) + ',' + (y) + ')';
                    })
                    .text(function (d, i) {
                        return data[i]['label'];
                    })
                    .style("text-anchor", function (d, i) {
                        var r = radius + margin.out;
                        var alpha = deg2rad((data[i]['value'] / 2) + data[i]['start'] - 90);
                        var x = r * Math.cos(alpha);
                        if (x > 0) {
                            return 'start';
                        } else {
                            return 'end';
                        }
                    })
                    .attr('fill', function (d, i) {
                        return data[i]['color'];
                    });
            } else {
                lg.append('text').text(labels[0]).attr('class', 'text-large').attr('text-anchor', 'middle').attr('alignment-baseline', 'middle');
            }
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

    chart.innerRadius = function (value) {
        if (!arguments.length) return innerRadius;
        innerRadius = value;
        return chart;
    };

    return chart;
}

function draw_xy_chart() {

    function chart(selection) {
        selection.each(function (datasets) {
            var xoffset = notes.length && 40 || 0;
            var margin = {top: 20, right: width * 0.1, bottom: 50, left: width * 0.1},
                innerwidth = width - margin.left - margin.right,
                innerheight = height - margin.top - margin.bottom;

            var svg = d3.select(this)
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

            var color_scale = d3.scaleOrdinal(d3.schemeCategory10);
            var y1data = [], y2data = [];
            var y1datasets = [], y2datasets = [];

            if (scatter === 'bar') {
                var color = datasets['color'];
                var x_scale = d3.scaleLinear()
                    .range([0, innerwidth])
                    .domain([d3.min(datasets.data), d3.max(datasets.data)]);
                var bins = d3.histogram()
                    .value(function (d) {
                        return d;
                    })
                    .domain(x_scale.domain())
                    .thresholds(x_scale.ticks(50))(datasets['data']);
                var y1_scale = d3.scaleLinear()
                    .domain([0, d3.max(bins, function (d) {
                        return d.length;
                    })])
                    .range([innerheight, 0]);
            } else {
                var xmin = xlimits[0] || d3.min(datasets, function (d) { return d3.min(d.x);});
                var xmax = xlimits[1] || d3.max(datasets, function (d) { return d3.max(d.x);});
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

                switch(interpolation) {
                    case 'cardinal':
                        var fit = d3.curveCardinal;
                        break;
                    case 'step':
                        var fit = d3.curveStep;
                        break;
                    case 'step-after':
                        var fit = d3.curveStepAfter;
                        break;
                    case 'step-before':
                        var fit = d3.curveStepBefore;
                        break;
                    case 'basis':
                        var fit = d3.curveBasis;
                        break;
                    case 'linear':
                        var fit = d3.curveLinear;
                }

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
                    .domain([y1limits[0] || d3.min(y1data),
                        y1limits[1] || d3.max(y1data)]);

                var y2_scale = d3.scaleLinear()
                    .range([innerheight - xoffset, 0])
                    .domain([y2limits[0] || d3.min(y2data),
                        y2limits[1] || d3.max(y2data)]);
            }


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
                    if (y1datasets.length > 1 || !(y1datasets.length)) {
                        return "#000000";
                    }
                    return y1datasets.length && y1datasets[0]['color'];
                })
                .text(y1label);

            if (scatter === 'bar') {
                var bar = svg.selectAll(".bar")
                    .data(bins)
                    .enter().append("g")
                    .attr("class", "bar")
                    .attr("fill", color)
                    .attr("transform", function(d) { return "translate(" + x_scale(d.x0) + "," + y1_scale(d.length) + ")"; });

                bar.append("rect")
                    .attr("x", 1)
                    .attr("title", function(d) { return d.x0 + '-' + d.x1 + ': ' + d.length + ' entries'; })
                    .attr("width", x_scale(bins[0].x1) - (Math.max(0, x_scale(bins[0].x0) - 1)))
                    .attr("height", function(d) { return innerheight - y1_scale(d.length); });

            } else {

                var y1_draw_line = [], y2_draw_line = [];

                for (var p = 0; p < datasets.length; p++) {
                    if (datasets[p]['y1']) {
                        y1_draw_line.push(d3.line()
                            .curve(fit)
                            .x(function (d) {
                                return x_scale(d[0]);
                            })
                            .y(function (d) {
                                return y1_scale(d[1]);
                            }));
                    } else if (datasets[p]['y2']) {
                        y2_draw_line.push(d3.line()
                            .curve(fit)
                            .x(function (d) {
                                return x_scale(d[0]);
                            })
                            .y(function (d) {
                                return y2_scale(d[1]);
                            }));
                    }
                }

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

                var mouseX = svg.append("text")
                    .attr("transform", "translate(" + (innerwidth - 3) + ", " + (innerheight - 3) + ")")
                    .style("text-anchor", "end")
                    .style("opacity", "0");

                mouseG.append('rect')
                    .attr('width', innerwidth)
                    .attr('height', innerheight)
                    .attr('fill', 'none')
                    .attr('pointer-events', 'all')
                    .on('mouseout', function () {
                        svg.select(".mouse-line").style("opacity", "0");
                        svg.selectAll(".mouse-per-line circle").style("opacity", "0");
                        svg.selectAll(".mouse-per-line text").style("opacity", "0");
                        mouseX.style("opacity", "1");
                    })
                    .on('mouseover', function (e) {
                        svg.select(".mouse-line").style("opacity", "1");
                        svg.selectAll(".mouse-per-line circle").style("opacity", "1");
                        svg.selectAll(".mouse-per-line text").style("opacity", "1");
                        mouseX.style("opacity", "1");

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
                                mouseX.text("X = " + xPos.toFixed(2));
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
            }

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
        if (!arguments.length) return xlabel || '';
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
    chart.interpolation = function (value) {
        if (!arguments.length) return interpolation;
        interpolation = value;
        return chart;
    };
    chart.xlimits = function (value) {
        if (!arguments.length) return xlimits || [null, null];
        xlimits = value;
        return chart;
    };
        chart.y1limits = function (value) {
        if (!arguments.length) return y1limits || [null, null];
        y1limits = value;
        return chart;
    };
    chart.y2limits = function (value) {
        if (!arguments.length) return y2limits || [null, null];
        y2limits = value;
        return chart;
    };

    return chart;
}


function build_report(selector, report) {
    var converter = new showdown.Converter();
    $.each(report['details'], function (i, section) {
        var section_box = $(selector).append('<section class="container" id="section-' + i + '"></section>').children(":last-child");
        if (section['title']) {
            section_box.append("<div class='col-xs-12'><h3 class='section-title' >" + section['title'] + "</h3></div>");
        }
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
                var xlimits = entry['data']['x-limits'] || [null, null];
                var y1limits = entry['data']['y1-limits'] || [null, null];
                var y2limits = entry['data']['y2-limits'] || [null, null];
                var interpolation = entry['data']['interpolation'] || 'linear';
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
                    .xlimits(xlimits)
                    .y1limits(y1limits)
                    .y2limits(y2limits)
                    .xscale(xscale)
                    .notes([])
                    .interpolation(interpolation)
                    .scatter(entry['kind'] === 'scatterplot' && 'scatter' || entry['kind'] === 'lineplot' && 'line');
                var svg = d3.select('#figure-' + i + '-' + j).append("svg").attr('id', 'plot-' + i + "-" + j)
                    .datum(data)
                    .call(xy_chart);
                if (entry['title']) {
                    $('#figure-' + i + '-' + j).append("<figcaption class='text-center'>Figure " + ($('figure').length + 1) + '. ' + entry['title'] + "</figcaption>")
                }
            } else if (entry['kind'] === 'pie' || entry['kind'] === 'gauge') {
                $("#entry-" + i + "-" + j).append("<figure id='figure-" + i + "-" + j + "'></figure>");
                var data = [];
                var width = entry_row.width();
                var totalAngle = 0;

                $.each(entry['data'], function (l, wedge) {
                    if ((entry['data'][l]['start'] || totalAngle) != totalAngle) {
                        data.push({'start': totalAngle, 'value': entry['data'][l]['start'] - totalAngle, 'color': '#ffffff'});
                        totalAngle += entry['data'][l]['start'] - totalAngle;
                    }
                    wedge['start'] = wedge['start'] || totalAngle;
                    data.push(wedge);
                    totalAngle += entry['data'][l]['value'];
                });

                var pie_chart = draw_pie_chart()
                    .width(width)
                    .height(400)
                    .innerRadius(entry['kind'] === 'gauge' && 0.5 || 0);
                var svg = d3.select('#figure-' + i + '-' + j).append("svg").attr('id', 'plot-' + i + "-" + j).attr('class', 'gauge')
                    .datum(data)
                    .call(pie_chart);
                if (entry['title']) {
                    $('#figure-' + i + '-' + j).append("<figcaption class='text-center'>Figure " + ($('figure').length + 1) + '. ' + entry['title'] + "</figcaption>")
                }
            }
            if (entry['notes']) {
                entry_row.append("<div class='notes well'>" + converter.makeHtml(entry['notes']) + "</div>");
            }
        });
    });

}