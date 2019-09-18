(function ($) {
    $.fn.layoutContainer = function (options) {
        let settings = $.extend({
            'detailed': true,
            'labelled': false,
            'loadable': false,
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

                // draw envelope if container is final
                if (settings.detailed && data.id && data.final) {
                    main.append(data.envelope || 'circle')
                        .attrs({cx: '50%', cy: '50%', r: '49%', x: '0%', y: '0%', width: '100%', height: '100%'})
                        .attr('fill', 'none')
                        .attr('stroke', 'black');
                }

                // Draw Container Children
                drawContainers("#cnt-null-" + pk, data, settings.detailed, settings.labelled);
                listLoaded('#loaded-projects', '#loaded-containers', data);
                $(selector + ' [title]').tooltip();
                if (settings.loadable) {
                    $(document).on('click', selector + ' svg[data-accepts="true"]:not([data-id])', function(){
                        let url = "/users/containers/"+$(this).data('parent')+"/location/"+$(this).data('loc') + '/';
                        $('#modal-form').load(url);
                    });
                    $(document).on('click', selector + ' svg[data-final="true"]', function(){
                        let url = "/users/containers/"+$(this).data('id')+"/load/";
                        $('#modal-form').load(url);
                    });
                }

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
                x: (cx - 0.5 * sw).toFixed(3) + '%',
                y: (cy - 0.5 * sh).toFixed(3) + '%',
                width: sw.toFixed(3) + '%',
                height: sh.toFixed(3) + '%',
                class: cls,
                'data-width': (sw * cw / 100).toFixed(3),
                'data-height': (sh * ch / 100).toFixed(3),
                'data-accepts': d.accepts,
                'data-id': d.id,
                'data-parent': data.id,
                'data-loc': d.loc,
                'data-group': d.batch,
                'data-owner': d.owner,
                'data-final': d.final,
            };
            if (d.id) {
                options.id = 'cnt-' + data.id + '-' + d.id;
                options.title = (data.final ? d.name : d.owner + '|' + d.name)
            }
            return options;
        })
        .style('pointer-events', 'visible');

    // Draw children envelopes
    subs.append(d => document.createElementNS(d3.namespaces.svg, (d.envelope || 'circle')))
        .attrs(function (d) {
            let prj = (d.owner ? d.owner.toLowerCase() : 'null');
            return {x: '0%', y: '0%', width: '100%', height: '100%', project: prj, cx: '50%', cy: '50%', r: '49%'}
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
            if ((d.final && !detailed) || (detailed && d.id && d.sample)) {
                return '#17a2b8';
            } else if (d.id) {
                return 'none';
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

function extractProjects(results, data) {
    jQuery.each(data.children, function(i, obj){
        if (obj.owner && obj.final) {
            if (!(obj.owner in results)) {
                results[obj.owner] = [];
            }
            results[obj.owner].push({
                loc: obj.loc, id: obj.id,  project: obj.owner, type: obj.type,
                name: obj.name, parent: obj.parent,
                samples: obj.children.filter(function (d){return d.id;}).length
            });
        }
        if (obj.children) {
            extractProjects(results, obj.children);
        }

    });
    return results;
}


function compileProjects(data) {
    let raw = extractProjects({}, data);
    let results = {
        projects: [],
        containers: []
    };

    jQuery.each(raw, function(key, value){
        results.projects.push({name: key, parent: value[0].parent, details: value});
        results.containers = results.containers.concat(value)
    });
    results.containers.sort(function(a, b){
        return a.loc > b.loc;
    });
    return results;
}

var projTemplate = _.template(
    '<div class="row loaded-project" data-project="<%= name.toLowerCase() %>">' +
    '       <h5 class="col-1 text-condensed text-center align-self-center"><%= details.length %></h5>' +
    '       <div class="col d-flex flex-row justify-content-between">' +
    '           <div class="flex-grow-1"><h5 class="m-0"><%= name %></h5>' +
    '           <div class="loc-list">' +
    '<% _.each(details, function(container, i){ %><small class="text-muted d-inline-block"><%= container.loc %></small><% }); %></div>' +
    '           </div>' +
    '           <div class="tools-box">' +
    '               <a href="#!" title="Details"> ' +
    '                   <div class="icon-stack">' +
    '                       <i class="ti ti-1x ti-zoom-in"></i>' +
    '                   </div>' +
    '               </a>' +
    '               <a href="#!" title="Unload all" data-url="/users/containers/<%= parent %>/unload/<%= name.toLowerCase() %>/">' +
    '                   <div class="icon-stack">' +
    '                       <i class="ti ti-1x ti-share"></i>' +
    '                   </div>' +
    '               </a>' +
    '           </div>' +
    '       </div>' +
    '</div>'
);
var locTemplate = _.template(
    '<div class="row loaded-container" data-loc="<%= loc %>">' +
    '       <h6 class="col-1 text-condensed text-center align-self-center"><strong><%= loc %></strong></h6>' +
    '       <div class="col d-flex flex-row justify-content-between">' +
    '           <div class="flex-grow-1 align-self-center py-0">' +
    '               <h5 class="m-0"><%= project %>&nbsp;<span class="text-muted">|</span>&nbsp;<%= name %></h5>' +
    '               <div class="loc-list">' +
    '                   <small class="text-muted d-inline-block"><%= type %></small>' +
    '                   <small class="text-muted d-inline-block"><strong><%= samples %></strong> samples</small>' +
    '               </div>' +
    '           </div>' +
    '           <div class="tools-box">' +
    '               <a href="#!" title="Unload" data-url="/users/containers//history/">' +
    '                   <div class="icon-stack">' +
    '                       <i class="ti ti-1 ti-share"></i>' +
    '                   </div>' +
    '               </a>' +
    '           </div>' +
    '       </div>' +
    '</div>'
);

function listLoaded(proj_container, loc_container, data) {
    let info =compileProjects(data);
    console.log(info);
    d3.select(proj_container)
        .selectAll('div')
        .data(info.projects||[])
        .enter()
        .append("div")
        .attr("class", "list-group-item py-1")
        .attr("id", d => "proj-" + d.name.toLowerCase())
        .html(function(d){
            d.details.sort(function(a, b){
                return a.loc > b.loc;
            });
            return projTemplate(d)
        });
    d3.select(loc_container)
        .selectAll('div')
        .data(info.containers||[])
        .enter()
        .append("div")
        .attr("class", "list-group-item py-1")
        .attr("id", d => "loc-for-" + d.id)
        .html(function(d){
            return locTemplate(d)
        });
    $(proj_container + ' [title], ' + loc_container + ' [title]').tooltip();
}
