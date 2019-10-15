(function ($) {
    $.fn.layoutContainer = function (options) {
        let parent = $(this);
        let settings = $.extend({
            'detailed': parent.data('detailed'),
            'labelled': parent.data('labelled'),
            'loadable' : parent.data('loadable'),
        }, options);

        let url = parent.data('layout-url');
        let selector = '#' + parent.attr('id');
        // fetch data and render
        $.ajax({
            dataType: "json",
            url: url,
            success: function (data, status, xhr) {
                let width = parent.width();
                let height = width * (data.height || 1);
                let svg_id = 'cnt-' + data.id;
                let main = d3.select(selector)
                    .selectAll("svg")
                    .data([data]);

                let added = main
                    .enter()
                    .append('svg')
                    .attr('viewBox', '0 0 ' + (width) + ' ' + (height))
                    .attr('data-detailed', settings.detailed)
                    .attr('data-labelled', settings.labelled)
                    .attr('id', svg_id);

                main
                    .exit()
                    .remove();

                // draw envelope if container is final
                if (settings.detailed && data.id && data.final) {
                    added.append(data.envelope || 'circle')
                        .attrs({cx: '50%', cy: '50%', r: '49%', x: '0%', y: '0%', width: '100%', height: '100%'})
                        .attr('fill', 'none')
                        .attr('stroke', 'black');
                }

                // Draw Container Children
                drawContainers("#" + svg_id, data, settings.loadable);
                listLoaded('#loaded-projects', '#loaded-containers', data);
                $(selector + ' [title]').tooltip();
                if (settings.loadable) {
                    $(document).on('click', '[data-unload-url]', function () {
                        unloadUpdateData(this, settings);
                    });
                }
            }
        });
    }
}(jQuery));


function drawContainers(parent, data, loadable=false) {
    let cw = $(parent).width() || $(parent).data('width');
    let ch = $(parent).height() || $(parent).data('height');
    let detailed = $(parent).data('detailed');
    let labelled = $(parent).data('labelled');
    let aspect = cw / ch;
    let factor = Math.sqrt(cw ** 2 + ch ** 2) / (100 * Math.sqrt(2));
    let subs = d3.select(parent)
        .selectAll("svg" + "[data-parent='" + data.id + "']")
        .data(data.children || []);

    subs.exit().remove(); // Remove deleted entries
    let added = subs
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
                id: 'cnt-' + d.parent + '-' + d.loc,
                'data-width': (sw * cw / 100).toFixed(3),
                'data-height': (sh * ch / 100).toFixed(3),
                'data-accepts': d.accepts,
                'data-detailed': detailed,
                'data-labelled': labelled,
                'data-id': d.id,
                'data-parent': data.id,
                'data-loc': d.loc,
                'data-group': d.batch,
                'data-final': d.final,
                'data-project': (d.owner ? d.owner.toLowerCase() : 'null')
            };

            if (d.id) {
                options.title = (data.final ? d.name : d.owner + '|' + d.name)
            } else {
                options.title = d.loc;
            }
            return options;
        })
        .style('pointer-events', 'all')
        .on('click', function(d){
            let url = "";
            if (loadable && (d.accepts||d.final)) {
                d3.event.stopPropagation();
                if (! d.id) {
                    url = "/users/containers/" + data.id + "/location/" + d.loc + '/';
                } else {
                    url = "/users/containers/" + d.id + "/load/";
                }
                $('#modal-target').asyncForm({
                    url: url,
                    complete: function(info){
                        let cnt_id = '#cnt-' + info.id;
                        $(cnt_id).empty();
                        drawContainers(cnt_id, info, loadable);
                        listLoaded('#loaded-projects', '#loaded-containers', info);
                    }
                });
            }
        });


    // Draw children envelopes
    added.append(d => document.createElementNS(d3.namespaces.svg, (d.envelope || 'circle')))
        .attrs(function (d) {
            let cls = 'empty';
            if (d.final && detailed) {
                cls = 'outline';
            } else if ((detailed && d.sample) || (!detailed && d.final)) {
                cls = 'occupied';
            } else if (d.id && !d.final) {
                cls = 'ignore';
            }
            if (d.sample && d.started) {
                cls += ' started'
            }
            return {
                x: '0%', y: '0%', width: '100%', height: '100%',
                cx: '50%', cy: '50%', r: '49%', class: cls
            }
        });

    // Labels and Children
    if ((!data.final) || labelled) {
        added.append("text")
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
    added.each(function (d) {
        if (detailed || (!d.final)) {
            drawContainers('#' + $(this).attr('id'), d, loadable);
        }
    });
}

function extractProjects(results, data) {
    jQuery.each(data.children, function (i, obj) {
        if (obj.owner && obj.final) {
            if (!(obj.owner in results)) {
                results[obj.owner] = [];
            }
            results[obj.owner].push({
                loc: obj.loc, id: obj.id, project: obj.owner, type: obj.type,
                port: obj.port,
                name: obj.name, parent: obj.parent, url: obj.url,
                samples: obj.children.filter(function (d) {
                    return d.id;
                }).length
            });
        }
        if (obj.children) {
            extractProjects(results, obj);
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

    jQuery.each(raw, function (key, value) {
        results.projects.push({name: key, parent: value[0].parent, details: value});
        results.containers = results.containers.concat(value)
    });
    results.containers.sort(function (a, b) {
        return a.loc > b.loc;
    });
    return results;
}

var locTemplate = _.template(
    '<div class="row  list-cnt-<%= id %>" data-highlight="id" data-reference="<%= id %>">' +
    '       <h6 class="col d-flex flex-row justify-content-between my-0">' +
    '           <div class="flex-grow-1 align-self-center py-0">' +
    '               <div class="loc-list row">' +
    '                   <strong class="col-2"><%= port %></strong>' +
    '                   <span class="col mr-2"><a href="<%= url %>" title="<%= type %>"><%= name %></a>&nbsp;<small class="float-right badge badge-pill badge-primary detail" title="samples"><%= samples %></small></span>' +
    '                   <span class="col text-center text-muted detail"><%= project %></span>' +
    '               </div>' +
    '           </div>' +
    '           <div class="tools-box">' +
    '               <a href="#!" data-unload-url="/users/containers/<%= id %>/unload/" data-id="<%= id %>">' +
    '                   <div class="icon-stack">' +
    '                       <i class="ti ti-1 ti-share"></i>' +
    '                   </div>' +
    '               </a>' +
    '           </div>' +
    '       </h6>' +
    '</div>'
);


var projTemplate = _.template(
    '<div class="row" data-highlight="project" data-reference="<%= name.toLowerCase() %>">' +
    '       <h4 class="col-2 text-condensed text-center align-self-center"><span class="badge badge-pill badge-primary py-1" title="Containers"><%= details.length %></span></h4>' +
    '       <div class="col d-flex flex-row justify-content-between">' +
    '           <div class="flex-grow-1"><h5 class="m-0"><%= name %></h5>' +
    '           <div class="loc-list">' +
    '<% _.each(details, function(container, i){ %><small class="text-muted d-inline-block list-cnt-<%= container.id %>"><%= container.port %></small><% }); %></div>' +
    '           </div>' +
    '           <div class="project-list-tools tools-box">' +
    '               <a title="Details" data-toggle="collapse" href="#prj-<%= name.toLowerCase() %>-list"> ' +
    '                   <div class="icon-stack">' +
    '                       <i class="ti ti-1x ti-zoom-in"></i>' +
    '                   </div>' +
    '               </a>' +
    '               <a href="#!" data-form-url="/users/containers/<%= parent %>/unload/<%= name.toLowerCase() %>/">' +
    '                   <div class="icon-stack">' +
    '                       <i class="ti ti-1x ti-share"></i>' +
    '                   </div>' +
    '               </a>' +
    '           </div>' +
    '       </div>' +
    '</div>' +
    '<div class="collapse detail-container-list row" id="prj-<%= name.toLowerCase() %>-list">' +
    '<div class="col ml-5 my-1 ">' +
    '     <% _.each(details, function(container, i){ %><%= locTemplate(container) %><% }); %>' +
    '</div></div>'
);

function listLoaded(proj_container, loc_container, data) {
    let info = compileProjects(data);
    let projects = d3.select(proj_container)
        .selectAll(proj_container + ' > div')
        .data(info.projects || []);

    projects.exit().remove();
    projects.enter()
        .append("div")
        .attr("class", "list-group-item py-1")
        .attr("id", d => "proj-" + d.name.toLowerCase())
        .attr("data-reference", d => d.name.toLowerCase())
        .attr("data-reference", "project")
        .html(function (d) {
            d.details.sort(function (a, b) {
                return a.loc > b.loc;
            });
            return projTemplate(d)
        });
    projects
        .attr("id", d => "proj-" + d.name.toLowerCase())
        .attr("data-reference", d => d.name.toLowerCase())
        .attr("data-reference", "project")
        .html(function (d) {
            d.details.sort(function (a, b) {
                return a.loc > b.loc;
            });
            return projTemplate(d)
        });

    let containers = d3.select(loc_container)
        .selectAll(loc_container + ' > div')
        .data(info.containers || []);

    containers.exit().remove();
    containers.enter()
        .append("div")
        .attr("class", d => "list-group-item py-1 list-cnt-" + d.id)
        .html(function (d) {
            return locTemplate(d)
        });
    containers
        .html(function (d) {
            return locTemplate(d)
        });
    $(proj_container + ' [title], ' + loc_container + ' [title]').tooltip();
}

function unloadUpdateData(element, settings) {
    let src = $(element);
    $.ajax({
        type: 'post',
        dataType: "json",
        url: src.data('unload-url'),
        data: {},
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
        },
        success: function (data, status, xhr) {
            let cnt_id = '#cnt-' + data.id;
            $(cnt_id).empty();
            drawContainers(cnt_id, data, true);
            listLoaded('#loaded-projects', '#loaded-containers', data);
        },
        error: function () {
            src.shake();
        }
    });
}

// Initialize global Layout Event handlers
$(document).ready(function () {
    $(document).on('mouseenter', '[data-highlight]', function () {
        let sel = "svg[data-" + $(this).data('highlight') + "='" + $(this).data('reference') + "'] >:first-child";
        $(sel).addClass('active-envelope');
    });
    $(document).on('mouseleave', '[data-highlight]', function () {
        $('svg > .active-envelope').removeClass('active-envelope');
    });
});