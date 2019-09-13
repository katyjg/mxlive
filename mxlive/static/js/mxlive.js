function drawContainer(parent, data) {
    var width = $(parent).width();
    var height = width * (data.height || 1);

    var svg = d3.select(parent)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    svg.selectAll("circle")
        .data(data.children)
        .enter()
        .append("circle")
        .attr("cx", function(d, i){ return d.x*100 + '%'; })
        .attr("cy", function(d, i){ return d.y*100 + '%'; })
        .attr("r", function(d, i){ return d.radius + '%'; })
        .style('stroke', "rgba(0,0,0,0.2)")
        .style("fill", function(d, i){
            if (d.occupied > 0) {
                return "rgba(74, 23, 112, 0.1)";
            } else {
                return "none";
            }
        });
    svg.selectAll("text")
        .data(data.children)
        .enter()
        .append("text")
        .attr("x", function(d, i){ return d.x*100 + '%'; })
        .attr("y", function(d, i){ return d.y*100 + '%'; })
        .attr("font-size", "10px")
        .attr("text-anchor", 'middle')
        .attr("stroke", "rgba(0,0,0,0.2)")
        .attr('dominant-baseline', 'middle')
        .text(function(d, i) {
            if (d.radius*width > 20) {
                return d.location;
            } else {
                return null;
            }
        });
}