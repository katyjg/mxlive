(function ($) {
    $.fn.layoutContainer = function (options) {
        let settings = $.extend({
            'detailed': true,
            'labelled': false
        }, options);
        let parent = $(this);
        let pk = parent.data('pk');
        let url = parent.data('layout-url');
        let selector = '#' + parent.attr('id');

        // fetch data and render
        $.ajax({
            dataType: "json",
            url: url,
            success: function (data, status, xhr) {
                let width = parent.width();
                let height = width * (data.height || 1);
                let main = d3.select(selector)
                    .append('svg')
                    .attr('viewBox', '0 0 ' + (width) + ' ' + (height))
                    .attr('id', 'cnt-null-' + pk);

                // draw enlvelope if container is final
                if (settings.detailed && data.id && data.final) {
                    main.append(data.envelope || 'circle')
                        .attrs({cx: '50%', cy: '50%', r: '49%', x: '0%', y: '0%', width: '100%', height: '100%'})
                        .attr('fill', 'none')
                        .attr('stroke', 'black');
                }

                // Draw Container Children
                drawContainers("#cnt-null-" + pk, data, settings.detailed, settings.labeled);
                $(selector + ' [title]').tooltip();
                console.log(data);
            }
        });
    }
}(jQuery));


function drawContainers(parent, data, detailed = true, labelled = false) {
    let cw = $(parent).width() || $(parent).data('width');
    let ch = $(parent).height() || $(parent).data('height');
    let aspect = cw / ch;
    let factor = Math.sqrt(cw ** 2 + ch ** 2) / (100 * Math.sqrt(2));
    let subs = d3.select(parent)
        .selectAll("svg")
        .data(data.children || [])
        .enter()
        .append("svg")
        .attrs(function (d) {
            let sw = 2 * (d.radius * factor / cw) * 100;
            let sh = sw * aspect;
            let cx = d.x * 100;
            let cy = d.y * 100;
            let cls = 'loc-' + data.loc + '-' + d.loc;
            if (data.envelope === 'circle') {
                cx = d.x * 0.5 * Math.sin(d.y) * 100 + 50;
                cy = d.x * 0.5 * Math.cos(d.y) * 100 + 50;
            }
            if (data.accepts) {
                cls += ' cursor';
            }
            let options = {
                x: (cx - 0.5 * sw) + '%',
                y: (cy - 0.5 * sh) + '%',
                width: sw + '%',
                height: sh + '%',
                class: cls,
                title: d.name,
                'data-width': sw * cw / 100,
                'data-height': sh * ch / 100,
                'data-id': d.id,
                'data-group': d.batch,
                'data-owner': d.owner,
                'data-final': d.final,
            };
            if (d.id) {
                options.id = 'cnt-' + data.id + '-' + d.id
            }
            return options;
        })
        .style('pointer-events', 'all');

    // Draw children envelopes
    subs.append(d => document.createElementNS(d3.namespaces.svg, (d.envelope || 'circle')))
        .attrs(function (d) {
            if (d.envelope === 'rect') {
                return {x: '0%', y: '0%', width: '100%', height: '100%'}
            } else {
                return {cx: '50%', cy: '50%', r: '49%'}
            }
        })
        .style('opacity', d => (d.started > 0) ? 0.3 : 0.7)
        .style('stroke', function (d) {
            if (detailed && d.final && d.id) {
                return 'black';
            } else {
                return 'none';
            }
        })
        .style('fill', function (d) {
            if ((d.envelope === 'rect') || (detailed && d.final)) {
                return 'none';
            } else if (d.id) {
                return '#17a2b8';
            } else {
                return 'rgba(0,0,0,0.15)';
            }
        });

    // Labels and Children
    if ((!data.final) || labelled) {
        subs.append("text")
            .attr("x", '50%')
            .attr("y", '50%')
            .attr("font-size", 0.9 + 'rem')
            .attr("fill", "black")
            .attr("text-anchor", 'middle')
            .attr("opacity", d => (d.id) ? 0.7 : 0.3)
            .attr('dominant-baseline', 'middle')
            //.attr('class', d => (d.id)? 'occupied': 'empty')
            .text(function (d, i) {
                return d.loc;
            });
    }
    subs.each(function (d) {
        if (detailed || (!d.final)) {
            drawContainers('#' + $(this).attr('id'), d, detailed, labelled);
        }
    });
}