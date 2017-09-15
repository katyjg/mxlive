function draw_xy_chart() {

    function chart(selection) {
        selection.each(function(datasets) {
            var margin = {top: 20, right: width*0.1+50, bottom: 50, left: width*0.1+50},
                innerwidth = width - margin.left - margin.right,
                innerheight = height - margin.top - margin.bottom ;

            if (xscale == 'ordinal') {
                var x_scale = d3.scale.ordinal()
                    .range([0, innerwidth])
                    .domain(datasets.map(function (d) {
                        return d.x;
                    }));
            } else {
                var x_scale = d3.scale.linear()
                    .range([0, innerwidth])
                    .domain([ d3.min(datasets, function(d) { return d3.min(d.x); }),
                              d3.max(datasets, function(d) { return d3.max(d.x); }) ]) ;
            }


            var y1_scale = d3.scale.linear()
                .range([innerheight, 0])
                .domain([ d3.min(datasets, function(d) { return d3.min(d.y1); }),
                          d3.max(datasets, function(d) { return d3.max(d.y1); }) ]) ;

            var color_scale = d3.scale.category10()
                .domain(d3.range(datasets.length)) ;

            var x_axis = d3.svg.axis()
                .scale(x_scale)
                .orient("bottom") ;

            var y1_axis = d3.svg.axis()
                .scale(y1_scale)
                .orient("left") ;

            var x_grid = d3.svg.axis()
                .scale(x_scale)
                .orient("bottom")
                .tickSize(-innerheight)
                .tickFormat("") ;

            var y1_grid = d3.svg.axis()
                .scale(y1_scale)
                .orient("left")
                .tickSize(-innerwidth)
                .tickFormat("") ;

            var draw_line1 = d3.svg.line()
                .interpolate("basis")
                .x(function(d) { return x_scale(d[0]); })
                .y(function(d) { return y1_scale(d[1]); }) ;


            var svg = d3.select(this)
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")") ;

            svg.append("g")
                .attr("class", "x grid")
                .attr("fill", "none")
                .attr("transform", "translate(0," + innerheight + ")")
                .call(x_grid) ;

            svg.append("g")
                .attr("class", "y grid")
                .attr("fill", "none")
                .call(y1_grid) ;

            svg.append("g")
                .attr("class", "x axis")
                .attr("transform", "translate(0," + innerheight + ")")
                .call(x_axis)
                .append("text")
                .attr("dy", "2.5em")
                .attr("x", innerwidth/2)
                .style("text-anchor", "middle")
                .text(xlabel) ;


            var data_lines = svg.selectAll(".d3_xy_chart_line")
                .data(datasets.map(function (d) {
                    return d3.zip(d.x, d.y1);
                }))
                .enter().append("g")
                .attr("class", "d3_xy_chart_line");

            if (scatter == 'line') {
                data_lines.append("path")
                    .attr("class", "line")
                    .attr("d", function (d) {
                        return draw_line1(d);
                    })
                    .attr("stroke", function (_, i) {
                        return color_scale(i);
                    })
                    .attr("fill", "none");
            } else {
                for (i = 0; i < datasets.length; i++) {
                    var newdata = datasets[i]['x'].map(function (e, j) {
                        return [e, datasets[i]['y1'][j]];
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
                        .attr("fill", function (_, k) {
                            return color_scale(i);
                        });
                }
            }

            if(!(datasets[0]['y2'])) {
                svg.append("g")
                    .attr("class", "y axis")
                    .call(y1_axis)
                    .append("text")
                    .attr("transform", "translate(0," + innerheight / 2 + "), rotate(-90)")
                    .attr("y", 6)
                    .attr("dy", "-2.5em")
                    .style("text-anchor", "middle")
                    .text(y1label);
            } else {
                svg.append("g")
                    .attr("class", "y axis")
                    .call(y1_axis)
                    .append("text")
                    .attr("transform", "translate(0," + innerheight / 2 + "), rotate(-90)")
                    .attr("y", 6)
                    .attr("dy", "-2.5em")
                    .style("text-anchor", "middle")
                    .attr("fill", function (_, i) {
                        return color_scale(i);
                    })
                    .text(y1label);

                var y2_scale = d3.scale.linear()
                    .range([innerheight, 0])
                    .domain([d3.min(datasets, function (d) {
                        return d3.min(d.y2);
                    }),
                        d3.max(datasets, function (d) {
                            return d3.max(d.y2);
                        })]);
                var y2_axis = d3.svg.axis()
                    .scale(y2_scale)
                    .orient("right") ;

                var draw_line2 = d3.svg.line()
                    .interpolate("cardinal")
                    .x(function(d) { return x_scale(d[0]); })
                    .y(function(d) { return y2_scale(d[1]); }) ;



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
                        return color_scale(i+1);
                    })
                    .text(y2label) ;

                var y2_data_lines = svg.selectAll(".xy2_chart_line")
                    .data(datasets.map(function(d) {return d3.zip(d.x, d.y2);}))
                    .enter().append("g")
                    .attr("class", "xy2_chart_line") ;

                if (scatter == 'line') {
                    y2_data_lines.append("path")
                        .attr("class", "line")
                        .attr("d", function (d) {
                            return draw_line2(d);
                        })
                        .attr("stroke", function (_, i) {
                            return color_scale(i + 1);
                        })
                        .attr("fill", "none");
                } else {
                    for (i = 0; i < datasets.length; i++) {
                        var newdata = datasets[i]['x'].map(function (e, j) {
                            return [e, datasets[i]['y2'][j]];
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
                            .attr("fill", function (_, k) {
                                return color_scale(i + 1);
                            });
                    }
                }
            }

            if (datasets.length > 1) {
                data_lines.append("text")
                    .datum(function (d, i) {
                        return {name: datasets[i].label, final: d[d.length - 1]};
                    })
                    .attr("transform", function (d) {
                        return ( "translate(" + x_scale(d.final[0]) + "," +
                        y1_scale(d.final[1]) + ")" );
                    })
                    .attr("x", 3)
                    .attr("dy", ".35em")
                    .attr("fill", function (_, i) {
                        return color_scale(i);
                    })
                    .text(function (d) {
                        return d.name;
                    });
            }

    /* Interactive stuff */
    var mouseG = svg.append("g")
        .attr("class", "mouse-over-effects");

    mouseG.append("path") // this is the black vertical line to follow mouse
        .attr("class", "mouse-line")
        .style("stroke", "#333")
        .style("stroke-width", "0.5px")
        .style("opacity", "0");

    var lines = this.getElementsByClassName('line');

    if (datasets[0]['y2']) {
        var dualdatasets = [
            {'x': datasets[0]['x'], 'y1': datasets[0]['y1']},
            {'x': datasets[0]['x'], 'y1': datasets[0]['y2'], 'scale': y2_scale}
        ];
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


    return chart;
}