function createNodes(data, envelope, calc_width, calc_height, detail) {
    var nodes = [], x, y;
    for (var key in data) {
        var coords = data[key];
        if(envelope=="circle") {
            y = (coords[0] * calc_height / 2 * Math.cos(coords[1])) + calc_height / 2;
            x = (coords[0] * calc_width / 2 * Math.sin(coords[1])) + calc_width / 2;
        } else {
            x = coords[0]*calc_width;
            y = coords[1]*calc_height;
        }
        if (detail && coords.length > 2) {
            nodes.push({
                'id': key,
                'x': x,
                'y': y,
                'sample': coords[2].sample,
                'accepts': coords[2].accepts,
                'group': coords[2].group,
                'started': coords[2].started
            });
        } else {
            nodes.push({
                'id': key,
                'x': x,
                'y': y
            });
        }

    }
    return nodes;
}

function drawLocations(id, nodes, labels, radius, svg) {
    var labels = svg.selectAll("text")
        .data(labels)
        .enter()
        .append("text");
    var labelsAttributes = labels
        .text(function(d) { return d.id; })
        .attr("text-anchor", "middle")
        .attr("port", function(d) { return d.id; })
        .attr("r", radius + "%" )
        .attr('dx', function(d) { return d.x; })
        .attr('dy', function(d) { return d.y + 3; });
    var circles = svg.selectAll("circle")
        .data(nodes)
        .enter()
        .append("circle");
    var circleAttributes = circles
        .attr("cx", function (d) { return d.x; })
        .attr("cy", function (d) { return d.y; })
        .attr("r", radius + "%" )
        .attr("port", function(d) { return d.id })
        .attr("title", function(d) {
            if(d.sample) {
                return d.id + ': ' + d.sample;
            } else {
                return d.id
            }
        })
        .attr("id", function(d) { return 'id-'+id+'-' + d.id; })
        .style("fill", "none")
        .style("opacity", 0.75)
        .attr("sample", function(d) { return d.sample; })
        .attr("group", function(d) { return d.group; })
        .attr("accepts", function(d) { return d.accepts; })
        .attr("class", function(d) {
            if(d.sample) {
                if(d.accepts) {
                    return d.accepts;
                }
                if(d.started) {
                    return 'started';
                }
                return 'full';
            }
            return 'empty';
        });
}

function drawChild(svg, info, accepts, brief) {
    var svgLocation = svg.append("svg")
        .attr("width", info.size.width)
        .attr("height", info.size.width)
        .attr("x", info.coords[0])
        .attr("y", info.coords[1])
        .attr('id', 'id-'+info.parent+'-'+info.location);

    if (!(accepts && brief)) {
        drawLocations(info.parent, info.nodes, info.labels, info.radius, svgLocation);
    }

    var svgLocationEnvelope = svgLocation.append(info.envelope)
        .attr('id', 'envelope' + '-' + info.parent + '-' + info.location)
        .attr("width", info.size.width)
        .attr("height", info.size.width)
        .attr("cx", "50%")
        .attr("cy", "50%")
        .attr("r", '50%')
        .attr("title", info.name)
        .style("pointer-events", "all")
        .attr("class", "cursor")
        .style("stroke", function () {
            if (info.envelope == 'circle') {
                return "#bbb";
            }
            return "none";
        })
        .style("fill", "none");

    if (accepts) {
        drawLocations(info.parent, info.nodes, info.labels, info.radius, svgLocation);
    } else if (brief) {
        $(info.envelope + '#envelope-'+info.parent + '-' + info.location).addClass('started').css('stroke', 'none');
    }

    return svgLocation;
}