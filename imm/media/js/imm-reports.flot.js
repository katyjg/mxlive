function plot_data(ph, data, labels, yaxes, xtitle, markings, crosshair) {
    for (d in data) { $.extend(data[d], {shadowSize: 0 }); }
    plot = $.plot(ph, data, {
                series: { lines: { show: true } },
                crosshair: crosshair,
                grid: { borderWidth: 1, borderColor: "#333333", markings: markings, hoverable: true, autoHighlight: false, },
                xaxis: { ticks: labels, axisLabel: xtitle },
                yaxes: yaxes, 
                legend: { position: 'nw' },
                pan: {interactive: true }
           });
}
var updateTimeout = null;
var latestPosition = null;
function updateValue(values) {
    updateTimeout = null;
    var pos = latestPosition;
    jQuery(values[0]).text(values[1]);
    jQuery(values[0]).css("background-color", "#fff");
}
