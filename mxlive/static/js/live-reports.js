function draw_xy_chart() {

    function chart(selection) {
        selection.each(function(datasets) {
            var xoffset = notes && 40 || 0;
            var margin = {top: 20, right: width*0.1, bottom: 50, left: width*0.1},
                innerwidth = width - margin.left - margin.right,
                innerheight = height - margin.top - margin.bottom;

            switch (xscale) {
                case 'inv-square':
                    var x_scale = d3.scalePow().exponent(-0.5)
                                    .range([0, innerwidth])
                                    .domain([ d3.min(datasets, function(d) { return d3.max(d.x); }),
                                              d3.max(datasets, function(d) { return d3.min(d.x); }) ]) ;
                    break;
                case 'pow':
                    var x_scale = d3.scalePow()
                                    .range([0, innerwidth])
                                    .domain([ d3.min(datasets, function(d) { return d3.min(d.x); }),
                                              d3.max(datasets, function(d) { return d3.max(d.x); }) ]) ;
                    break;
                case 'log':
                    var x_scale = d3.scaleLog()
                                    .range([0, innerwidth])
                                    .domain([ d3.min(datasets, function(d) { return d3.min(d.x); }),
                                              d3.max(datasets, function(d) { return d3.max(d.x); }) ]) ;
                    break;
                case 'identity':
                    var x_scale = d3.scaleIdentity()
                                    .range([0, innerwidth])
                                    .domain([ d3.min(datasets, function(d) { return d3.min(d.x); }),
                                              d3.max(datasets, function(d) { return d3.max(d.x); }) ]) ;
                    break;
                case 'time':
                    var x_scale = d3.scaleTime()
                                    .range([0, innerwidth])
                                    .domain([ d3.min(datasets, function(d) { return d3.min(d.x); }),
                                              d3.max(datasets, function(d) { return d3.max(d.x); }) ]) ;
                    break;
                case 'linear':
                    var x_scale = d3.scaleLinear()
                                    .range([0, innerwidth])
                                    .domain([ d3.min(datasets, function(d) { return d3.min(d.x); }),
                                              d3.max(datasets, function(d) { return d3.max(d.x); }) ]) ;
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
                .range([innerheight-xoffset, 0])
                .domain([ d3.min(y1data),
                          d3.max(y1data) ]) ;

            var y2_scale = d3.scaleLinear()
                .range([innerheight-xoffset, 0])
                .domain([ d3.min(y2data),
                          d3.max(y2data) ]) ;

            var x_axis = d3.axisBottom()
                .scale(x_scale)
                .tickSize(-innerheight);

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
                        .curve(d3.curveCatmullRom)
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
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")") ;


            svg.append("g")
                .attr("class", "x axis")
                .attr("transform", "translate(0," + (innerheight) + ")")
                .call(x_axis);
            svg.append("text")
                .attr("transform", "translate("+ (innerwidth/2) +","+(height-margin.bottom/2)+")")
                .style("text-anchor", "middle")
                .text(xlabel) ;

            svg.append("g")
                .attr("class", "y axis")
                .call(y1_axis)
                .append("text")
                .attr("transform", "translate(0," + innerheight / 2 + "), rotate(-90)")
                .attr("y", 6)
                .attr("dy", "-3.5em")
                .style("text-anchor", "middle")
                .attr("fill", function (_, i) {
                    if (y1datasets.length > 1 ) { return "#000000"; }
                    return y1datasets[0]['color'];
                })
                .text(y1label);


            if (y2data.length) {
                svg.append("g")
                    .attr("class", "y axis")
                    .attr("transform", "translate("+ innerwidth +", 0)")
                    .call(y2_axis)
                    .append("text")
                    .attr("transform", "translate(0," + innerheight/2 + "), rotate(-90)")
                    .attr("y", 55)
                    .attr("dy", 0)
                    .style("text-anchor", "middle")
                    .attr("fill", function (_, i) {
                        if (y2datasets.length > 1 ) { return "#000000"; }
                        return y2datasets[0]['color'];
                    })
                    .text(y2label) ;
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
                if (scatter == 'line') {
                    y1_data_lines.append("path")
                        .attr("class", "line")
                        .attr("d", function (d) {
                            return y1_draw_line[p](d);
                        })
                        .attr("data-legend",function(_, l) { return y1datasets[l]['label'] || null;})
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
                if (scatter == 'line') {
                    y2_data_lines.append("path")
                        .attr("class", "line")
                        .attr("d", function (d) {
                            return y2_draw_line[p](d);
                        })
                        .attr("data-legend",function(_, l) { return y2datasets[l]['label'] || null;;})
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

    for (i=0; i < notes.length; i++) {
        var xpos = notes[i]['x'] && x_scale(notes[i]['x']) || 0,
            ystart = notes[i]['ystart'] && y1_scale(notes[i]['ystart']) || 0,
            yend = notes[i]['yend'] && y1_scale(notes[i]['yend']) || innerheight - xoffset;

        svg.append("path")
           .attr('class', notes[i]['label'] + ' ' + (notes[i]['class'] || '') + ' ' + (notes[i]['display'] != null && (notes[i]['display'] == true && 'visible ' || 'hidden')) || 'visible')
           .style("stroke", notes[i]['color'] || "#333")
           .attr("d", function() {
                var d = "M" + xpos + "," + yend;
                    d += " " + xpos + "," + ystart;
                    return d;
           });
        svg.append("text")
           .attr('class', notes[i]['label'] + ' ' + (notes[i]['class'] || '') + ' ' + (notes[i]['display'] != null && (notes[i]['display'] == true && 'visible ' || 'hidden')) || 'visible')
           .text(notes[i]['label'])
           .style("font-size","9px")
           .style("fill", notes[i]['color'] || "#333")
           .attr("transform", "translate("+ (xpos+3) +"," + (y1_scale(0) + xoffset/2) + "), rotate(-90)")
           .style("text-anchor", "middle");
    }

    legend = svg.append("g")
        .attr("class","legend")
        .attr("transform","translate(50,30)")
        .style("font-size","12px")
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
        .attr("r", 6)
        .style("fill", "none")
        .style("stroke-width", "2px")
        .style("opacity", "0");

    mousePerLine.append("text")
        .attr("transform", "translate(10,3)");

    mouseG.append('rect')
        .attr('width', innerwidth)
        .attr('height', innerheight)
        .attr('fill', 'none')
        .attr('pointer-events', 'all')
        .on('mouseout', function() {
            svg.select(".mouse-line").style("opacity", "0");
            svg.selectAll(".mouse-per-line circle").style("opacity", "0");
            svg.selectAll(".mouse-per-line text").style("opacity", "0");
        })
        .on('mouseover', function() {
            svg.select(".mouse-line").style("opacity", "1");
            svg.selectAll(".mouse-per-line circle").style("opacity", "1");
            svg.selectAll(".mouse-per-line text").style("opacity", "1");
        })
        .on('mousemove', function() {
            var mouse = d3.mouse(this);
            svg.select(".mouse-line")
                .attr("d", function() {
                    var d = "M" + mouse[0] + "," + innerheight;
                    d += " " + mouse[0] + "," + 0;
                    return d;
                });
            svg.selectAll(".mouse-per-line")
                .style("stroke", function(d, n) { return color_scale(n); })
                .attr("transform", function(d, n) {
                    var xPos = x_scale.invert(mouse[0]);
                    var closest = d['x'].reduce(function(prev, curr) {
                          return (Math.abs(curr - xPos) < Math.abs(prev - xPos) ? curr : prev);
                        });
                    var i = d['x'].indexOf(closest);

                    var scale = d['scale']  || y1_scale;
                    var pos = scale(d['y1'][i]);
                    d3.select(this).select('text')
                        .style("stroke", "none")
                        .text(scale.invert(pos).toFixed(2));
                    return "translate(" + x_scale(closest) + "," + pos + ")";
                });
        });
    /* End of interactive stuff */

    }) ;

    }

    chart.width = function(value) {
        if (!arguments.length) return width;
        width = value;
        return chart;
    };

    chart.height = function(value) {
        if (!arguments.length) return height;
        height = value;
        return chart;
    };

    chart.xlabel = function(value) {
        if(!arguments.length) return xlabel ;
        xlabel = value ;
        return chart ;
    } ;

    chart.y1label = function(value) {
        if(!arguments.length) return y1label ;
        y1label = value ;
        return chart ;
    } ;

    chart.y2label = function(value) {
        if(!arguments.length) return y2label ;
        y2label = value ;
        return chart ;
    } ;

    chart.xscale = function(value) {
        if(!arguments.length) return xscale ;
        xscale = value ;
        return chart ;
    } ;
    chart.scatter = function(value) {
        if(!arguments.length) return scatter ;
        scatter = value ;
        return chart ;
    } ;
    chart.notes = function(value) {
        if(!arguments.length) return notes || [] ;
        notes = value ;
        return chart ;
    } ;

    return chart;
}