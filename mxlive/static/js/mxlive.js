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
                let svg_id = 'cnt-' + data.id;
                let main = d3.select(selector)
                    .append('svg')
                    .attr('viewBox', '0 0 ' + (width) + ' ' + (height))
                    .attr('data-detailed', settings.detailed)
                    .attr('data-labelled', settings.labelled)
                    .attr('id', svg_id);

                // draw envelope if container is final
                if (settings.detailed && data.id && data.final) {
                    main.append(data.envelope || 'circle')
                        .attrs({cx: '50%', cy: '50%', r: '49%', x: '0%', y: '0%', width: '100%', height: '100%'})
                        .attr('fill', 'none')
                        .attr('stroke', 'black');
                }

                // Draw Container Children
                drawContainers("#" + svg_id, data);
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
                    $(document).on('click', '[data-unload-url]', function (){
                        unloadUpdateData(this, settings);
                    });
                    $(document).on('mouseenter', '.loaded-project', function(){
                        let sel = "svg [project='" + $(this).data('project') +"']";
                        $(sel).addClass('active-envelope');
                    });
                    $(document).on('mouseenter', '.loaded-container', function(){
                        let sel = "svg [data-loc='" + $(this).data('loc') +"'] >:first-child";
                        $(sel).addClass('active-envelope');
                    });
                    $(document).on('mouseleave', '.loaded-container, .loaded-project', function(){
                        $('svg > .active-envelope').removeClass('active-envelope');
                    });
                }

            }
        });
    }
}(jQuery));



function drawContainers(parent, data) {
    let cw = $(parent).width() || $(parent).data('width');
    let ch = $(parent).height() || $(parent).data('height');
    let detailed = $(parent).data('detailed');
    let labelled = $(parent).data('labelled');
    let aspect = cw / ch;
    let factor = Math.sqrt(cw ** 2 + ch ** 2) / (100 * Math.sqrt(2));
    let subs = d3.select(parent)
        .selectAll("svg"+"[data-parent='"+ data.id +"']")
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
                'data-owner': d.owner,
                'data-final': d.final
            };
            if (d.id) {
                options.title = (data.final ? d.name : d.owner + '|' + d.name)
            } else {
                options.title = d.loc;
            }
            return options;
        })
        .style('pointer-events', 'visible');

    // Remove deleted entries
    //subs.exit().remove();

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
            drawContainers('#' + $(this).attr('id'), d);
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

var locTemplate = _.template(
    '<div class="row loaded-container cnt-<%= id %>" data-loc="<%= loc %>">' +
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
    '               <a href="#!" title="Unload" data-unload-url="/users/containers/<%= id %>/unload/" data-id="<%= id %>">' +
    '                   <div class="icon-stack">' +
    '                       <i class="ti ti-1 ti-share"></i>' +
    '                   </div>' +
    '               </a>' +
    '           </div>' +
    '       </div>' +
    '</div>'
);


var projTemplate = _.template(
    '<div class="row loaded-project" data-project="<%= name.toLowerCase() %>">' +
    '       <h5 class="col-1 text-condensed text-center align-self-center"><%= details.length %></h5>' +
    '       <div class="col d-flex flex-row justify-content-between">' +
    '           <div class="flex-grow-1"><h5 class="m-0"><%= name %></h5>' +
    '           <div class="loc-list">' +
    '<% _.each(details, function(container, i){ %><small class="text-muted d-inline-block cnt-<%= container.id %>"><%= container.loc %></small><% }); %></div>' +
    '           </div>' +
    '           <div class="tools-box">' +
    '               <a title="Details" data-toggle="collapse" href="#prj-<%= name.toLowerCase() %>-list"> ' +
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
    '</div>' +
    '<div class="collapse" id="prj-<%= name.toLowerCase() %>-list">' +
    '<div class="container bg-light">' +
    '     <% _.each(details, function(container, i){ %><%= locTemplate(container) %><% }); %>' +
    '</div></div>'
);

function listLoaded(proj_container, loc_container, data) {
    let info = compileProjects(data);
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
        })
        .exit().remove();
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

(function($){
    $.fn.shake = function(options) {
        let settings = $.extend({
            interval: 100,
            distance: 5,
            times: 4
        }, options );

        $(this).css('position','relative');

        for(let iter=0; iter<(settings.times+1); iter++){
            $(this).animate({ left:((iter % 2 === 0 ? settings.distance : settings.distance * -1)) }, settings.interval);
        }
        $(this).animate({ left: 0}, settings.interval, function(){});
    };
})(jQuery);


function unloadUpdateData(element, settings) {
    let src = $(element);
    $.ajax({
        type: 'post',
        dataType: "json",
        url: src.data('unload-url'),
        data: {},
        beforeSend: function(xhr, settings){
            xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
        },
        success: function(data, status, xhr) {
            let cnt_id = '#cnt-' + data.id;
            let cnt_nodes = '.cnt' + src.data('id');
            $(cnt_id).empty();
            $(cnt_nodes).slideUp(300, function (){
                $(cnt_nodes).remove();
            });
            drawContainers(cnt_id, data);

            // let child_sel = 'svg#cnt-' + data.parent + '-' + data.id + ' > svg';
            // let envelope = 'svg#cnt-' + data.parent + '-' + data.id + ' *:first-child';
            // $(child_sel).remove();
            // d3.select(envelope)
            //     .style('fill', 'rgba(0,0,0,0.15)')
            //     .style('stroke', 'none');
        },
        error: function() {
            src.shake();
        }
    });
}
