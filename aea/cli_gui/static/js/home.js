/*
 * JavaScript file for the application to demonstrate
 * using the API
 */

// Create the namespace instance
let ns = {};

// Create the model instance
ns.model = (function() {
    'use strict';

    let $event_pump = $('body');

    // Return the API
    return {
        read_local_agents: function() {
            let ajax_options = {
                type: 'GET',
                url: 'api/agents',
                accepts: 'application/json',
                dataType: 'json'
            };
            $.ajax(ajax_options)
            .done(function(data) {
                $event_pump.trigger('model_local_agents_read_success', [data]);
            })
            .fail(function(xhr, textStatus, errorThrown) {
                $event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
            })
        },
        read: function() {
            let ajax_options = {
                type: 'GET',
                url: 'api/people',
                accepts: 'application/json',
                dataType: 'json'
            };
            $.ajax(ajax_options)
            .done(function(data) {
                $event_pump.trigger('model_read_success', [data]);
            })
            .fail(function(xhr, textStatus, errorThrown) {
                $event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
            })
        },
        createAgent: function(agentId) {
            let ajax_options = {
                type: 'POST',
                url: 'api/agents',
                accepts: 'application/json',
                contentType: 'application/json',
                dataType: 'json',
                data: JSON.stringify(agentId)
            };
            $.ajax(ajax_options)
            .done(function(data) {
                $event_pump.trigger('model_create_agent_success', [data]);
            })
            .fail(function(xhr, textStatus, errorThrown) {
                $event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
            })
        },
        deleteAgent: function(agentId) {
            let ajax_options = {
                type: 'DELETE',
                url: 'api/agents/' + agentId,
                accepts: 'application/json',
                contentType: 'plain/text'
            };
            $.ajax(ajax_options)
            .done(function(data) {
                $event_pump.trigger('model_delete_agent_success', [data]);
            })
            .fail(function(xhr, textStatus, errorThrown) {
                $event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
            })
        },
        create: function(fname, lname) {
            let ajax_options = {
                type: 'POST',
                url: 'api/people',
                accepts: 'application/json',
                contentType: 'application/json',
                dataType: 'json',
                data: JSON.stringify({
                    'fname': fname,
                    'lname': lname
                })
            };
            $.ajax(ajax_options)
            .done(function(data) {
                $event_pump.trigger('model_create_success', [data]);
            })
            .fail(function(xhr, textStatus, errorThrown) {
                $event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
            })
        },
        update: function(fname, lname) {
            let ajax_options = {
                type: 'PUT',
                url: 'api/people/' + lname,
                accepts: 'application/json',
                contentType: 'application/json',
                dataType: 'json',
                data: JSON.stringify({
                    'fname': fname,
                    'lname': lname
                })
            };
            $.ajax(ajax_options)
            .done(function(data) {
                $event_pump.trigger('model_update_success', [data]);
            })
            .fail(function(xhr, textStatus, errorThrown) {
                $event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
            })
        },
        delete: function(lname) {
            let ajax_options = {
                type: 'DELETE',
                url: 'api/agents/' + lname,
                accepts: 'application/json',
                contentType: 'plain/text'
            };
            $.ajax(ajax_options)
            .done(function(data) {
                $event_pump.trigger('model_delete_success', [data]);
            })
            .fail(function(xhr, textStatus, errorThrown) {
                $event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
            })
        }
    };
}());

// Create the view instance
ns.view = (function() {
    'use strict';

    let $fname = $('#fname'),
        $lname = $('#lname'),
        $selectedAgentId = $('#selectedAgentId'),
        $createAgentId = $('#createAgentId');

    // return the API
    return {
        reset: function() {
            $lname.val('');
            $fname.val('').focus();
        },
        update_editor: function(fname, lname) {
            $lname.val(lname);
            $fname.val(fname).focus();
        },
        setSelectedAgentId(agentId){
            $selectedAgentId.html(agentId);
        },
        setCreateAgentId(agentId){
            $createAgentId.val(agentId);
        },
        update_selected_agent: function(agentId) {
            $selectedAgentId.html(agentId);
        },
        build_people_table: function(people) {
            let rows = ''

            // clear the table
            $('.people table > tbody').empty();

            // did we get a people array?
            if (people) {
                for (let i=0, l=people.length; i < l; i++) {
                    rows += `<tr><td class="fname">${people[i].fname}</td><td class="lname">${people[i].lname}</td><td>${people[i].timestamp}</td></tr>`;
                }
                $('.people table > tbody').append(rows);
            }
        },
        build_local_agents_table: function(agents) {
            let rows = ''

            // clear the table
            $('.agents table > tbody').empty();

            // did we get a people array?
            if (agents) {
                for (let i=0, l=agents.length; i < l; i++) {
                    rows += `<tr><td class="agentId">${agents[i].agentId}</td><td class="description">${agents[i].description}</td></tr>`;
                }
                $('.agents table > tbody').append(rows);
            }
        },
        error: function(error_msg) {
            $('.error')
                .text(error_msg)
                .css('visibility', 'visible');
            setTimeout(function() {
                $('.error').css('visibility', 'hidden');
            }, 3000)
        }
    };
}());

// Create the controller
ns.controller = (function(m, v) {
    'use strict';

    let model = m,
        view = v,
        $event_pump = $('body'),
        $fname = $('#fname'),
        $lname = $('#lname'),
        $createAgentId = $('#createAgentId'),
        $selectedAgentId = $('#selectedAgentId');

    // Get the data from the model after the controller is done initializing
    setTimeout(function() {
        model.read();
        model.read_local_agents();
    }, 100)

    // Validate input
    function validate(fname, lname) {
        return fname !== "" && lname !== "";
    }

    function validateAgentId(agentId){
        return agentId != "" && agentId != "NONE";
    }

    // Create our event handlers
    $('#create').click(function(e) {
        let fname = $fname.val(),
            lname = $lname.val();

        e.preventDefault();

        if (validate(fname, lname)) {
            model.create(fname, lname)
        } else {
            alert('Problem with first or last name input');
        }
    });

    $('#update').click(function(e) {
        let fname = $fname.val(),
            lname = $lname.val();

        e.preventDefault();

        if (validate(fname, lname)) {
            model.update(fname, lname)
        } else {
            alert('Problem with first or last name input');
        }
        e.preventDefault();
    });


    $('#delete').click(function(e) {
        let lname = $lname.val();

        e.preventDefault();

        if (validate('placeholder', lname)) {
            model.delete(lname)
        } else {
            alert('Problem with first or last name input');
        }
        e.preventDefault();
    });

    $('#reset').click(function() {
        view.reset();
    });

    $('#createAgent').click(function(e){
        let agentId = $createAgentId.val();

        e.preventDefault();

        if (validateAgentId(agentId)){
            model.createAgent(agentId)
        } else {
            alert('Error: Problem with agent id');
        }
    });


    $('#deleteAgent').click(function(e) {
        let agentId = $selectedAgentId.html();

        e.preventDefault();

        if (validateAgentId(agentId)) {
            model.deleteAgent(agentId)
        } else {
            alert('Error: Problem with selected agent id');
        }
        e.preventDefault();
    });


     $('.agents table > tbody ').on('click', 'tr', function(e) {
        let $target = $(e.target),
            agentId,
            description;

        agentId = $target
            .parent()
            .find('td.agentId')
            .text();

        view.update_selected_agent(agentId);
    });

    $('.people table > tbody ').on('dblclick', 'tr', function(e) {
        let $target = $(e.target),
            fname,
            lname;

        fname = $target
            .parent()
            .find('td.fname')
            .text();

        lname = $target
            .parent()
            .find('td.lname')
            .text();

        view.update_editor(fname, lname);
    });

    // Handle the model events
    $event_pump.on('model_read_success', function(e, data) {
        view.build_people_table(data);
        view.reset();
    });

    $event_pump.on('model_local_agents_read_success', function(e, data) {
        view.build_local_agents_table(data);
        view.reset();
    });

    $event_pump.on('model_create_success', function(e, data) {
        model.read();
    });

    $event_pump.on('model_update_success', function(e, data) {
        model.read();
    });

    $event_pump.on('model_delete_success', function(e, data) {
        model.read();
    });

    $event_pump.on('model_create_agent_success', function(e, data) {
        model.read_local_agents();
        view.setSelectedAgentId(data)
        view.setCreateAgentId("")
    });

    $event_pump.on('model_delete_agent_success', function(e, data) {
        model.read_local_agents();
        view.setSelectedAgentId("NONE")
    });


    $event_pump.on('model_error', function(e, xhr, textStatus, errorThrown) {
        let error_msg = textStatus + ': ' + errorThrown + ' - ' + xhr.responseJSON.detail;
        view.error(error_msg);
        console.log(error_msg);
    })
}(ns.model, ns.view));


