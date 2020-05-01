// d3.legend.js
// (C) 2012 ziggy.jonsson.nyc@gmail.com
// MIT licence

(function() {
d3.legend = function(g) {
  g.each(function() {
    var g= d3.select(this),
        items = {},
        svg = d3.select(g.property("nearestViewportElement"));

    svg.selectAll("[data-legend]").each(function() {
        var self = d3.select(this);
        items[self.attr("data-legend")] = {
          pos : self.attr("data-legend-pos") || this.getBBox().y,
          color : self.attr("data-legend-color") != undefined ? self.attr("data-legend-color") : self.style("fill") != 'none' ? self.style("fill") : self.style("stroke")
        }
      });

    items = d3.entries(items).sort(function(a,b) { return a.value.pos-b.value.pos});

    g.selectAll("text")
        .data(items).enter()
        .append("text")
        .attr("y",function(d,i) { return i+"em"})
        .attr("x","1em")
        .text(function(d) { return d.key});

    g.selectAll("circle")
        .data(items).enter()
        .append("circle")
        .attr("cy",function(d,i) { return i-0.35+"em"})
        .attr("cx",0)
        .attr("r","0.4em")
        .style("fill",function(d) { return d.value.color});

  });
  return g
}
})();