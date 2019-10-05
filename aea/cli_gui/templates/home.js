/*
 * JavaScript file for the application to demonstrate
 * using the API
 */

// Create the namespace instance
let ns = {};

// Get elements passed in from python as this is how they need to be passed into the html
// so best to have it in one place
let elements = []

{%for i in range(0, len)%}
    elements.push({"location": "{{htmlElements[i][0]}}", "type": "{{htmlElements[i][1]}}", "combined": "{{htmlElements[i][2]}}"});
//    console.log("htmlElements[i][0] = {{htmlElements[i][0]}} , htmlElements[i][1] = {{htmlElements[i][1]}}")
 {% endfor %}


// elements.push({"location": "local", "type": "agents"});
// elements.push({"location": "registered", "type": "protocols"});


// Create the model instance
ns.model = (function() {
    'use strict';

    let $event_pump = $('body');

    // Return the API
    return {
        readData: function(element) {
            // This is massively hacky!
            if (element["location"] == "local" && element["type"] != "agent"){
                return;
            }
            let ajax_options = {
                type: 'GET',
                url: 'api/' + element["type"],
                accepts: 'application/json',
                dataType: 'json'
            };
            $.ajax(ajax_options)
            .done(function(data) {
                $event_pump.trigger('model_' + element["combined"] + 'ReadSuccess', [data]);
            })
            .fail(function(xhr, textStatus, errorThrown) {
                $event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
            })
        },
        createItem: function(element, id) {
            let ajax_options = {
                type: 'POST',
                url: 'api/' + element["type"],
                accepts: 'application/json',
                contentType: 'application/json',
                dataType: 'json',
                data: JSON.stringify(id)
            };
            $.ajax(ajax_options)
            .done(function(data) {
                $event_pump.trigger('model_' + element["combined"] + 'CreateSuccess', [data]);
            })
            .fail(function(xhr, textStatus, errorThrown) {
                $event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
            })
        },

        deleteItem: function(element, id) {
            let ajax_options = {
                type: 'DELETE',
                url: 'api/' + element["type"] +'/' + id,
                accepts: 'application/json',
                contentType: 'plain/text'
            };
            $.ajax(ajax_options)
            .done(function(data) {
                $event_pump.trigger('model_' + element["combined"] + 'DeleteSuccess', [data]);
            })
            .fail(function(xhr, textStatus, errorThrown) {
                $event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
            })
        },
        fetchItem: function(element, agentId, itemId) {
            let propertyName = element["type"] +  "_id"
            let ajax_options = {
                type: 'POST',
                url: 'api/agent/' + agentId + '/' + element["type"],
                accepts: 'application/json',
                contentType: 'application/json',
                dataType: 'json',
                data: JSON.stringify(itemId)
            };
            $.ajax(ajax_options)
            .done(function(data) {
                $event_pump.trigger('model_' + element["combined"] + 'FetchSuccess', [data]);
            })
            .fail(function(xhr, textStatus, errorThrown) {
                $event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
            })
        },
        readLocalData: function(element, agentId) {
            let ajax_options = {
                type: 'GET',
                url: 'api/agent/'+agentId+'/' + element["type"],
                accepts: 'application/json',
                dataType: 'json'
            };
            $.ajax(ajax_options)
            .done(function(data) {
                $event_pump.trigger('model_' + element["combined"] + 'ReadSuccess', [data]);
            })
            .fail(function(xhr, textStatus, errorThrown) {
                $event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
            })
        },

    };
}());

// Create the view instance
ns.view = (function() {
    'use strict';


    // return the API
    return {

        setCreateId: function(tag, id) {
            $('#'+tag+'CreateId').html(id);
        },

        setSelectedId: function(tag, id) {
            $('#'+tag+'SelectionId').html(id);
        },

        build_table: function(data, tableName) {
            let rows = ''

            // clear the table
            $('.' + tableName + ' table > tbody').empty();

            // did we get a people array?
            if (tableName) {
                for (let i=0, l=data.length; i < l; i++) {
                    rows += `<tr><td class="id">${data[i].id}</td><td class="description">${data[i].description}</td></tr>`;
                }
                $('.' + tableName + ' table > tbody').append(rows);
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
        $event_pump = $('body');

    // Get the data from the model after the controller is done initializing
    setTimeout(function() {
        for (var i = 0; i < elements.length; ++i){
            model.readData(elements[i]);
        }
    }, 100)

    function validateId(agentId){
        return agentId != "" && agentId != "NONE";
    }

    // Go through each of the element types setting up cal back and table building functions on the
    // Items which exist
    for (var i = 0; i < elements.length; i++) {
        let element = elements[i]
        let combineName = element["combined"]
         $('#' + combineName + 'Create').click(function(e){
            let id =$('#' + combineName + 'CreateId').val();

            e.preventDefault();

            if (validateId(id)){
                model.createItem(element, id)
            } else {
                alert('Error: Problem with id');
            }
        });


        $('#' + combineName + 'Delete').click(function(e) {
            let id =$('#' + combineName + 'SelectionId').html();

            e.preventDefault();

            if (validateId(id)) {
                model.deleteItem(element, id)
            } else {
                alert('Error: Problem with selected id');
            }
            e.preventDefault();
        });

        $('#' + combineName + 'Fetch').click(function(e) {
            let agentId = $('#localAgentsSelectionId').html();
            let itemId =$('#' + combineName + 'SelectionId').html();

            e.preventDefault();

            if (validateId(agentId) && validateId(itemId) ) {
                model.fetchItem(element, agentId, itemId)

            } else {
                alert('Error: Problem with one of the selected ids (either agent or ' + element['type']);
            }
            e.preventDefault();
        });

        $('.' + combineName + ' table > tbody ').on('click', 'tr', function(e) {
            let $target = $(e.target),
                id,
                description;

            id = $target
                .parent()
                .find('td.id')
                .text();

            view.setSelectedId(combineName, id);
            if (combineName == "localAgents"){
                // This should be a function, vur can't do local functions with this hacky class setup
                for (var j = 0; j < elements.length; j++) {
                    if (elements[j]["location"] == "local" && elements[j]["type"] != "agent"){
                        model.readLocalData(elements[j], id);
                    }
                }

            }
        });
        // Handle the model events
        $event_pump.on('model_'+ combineName + 'ReadSuccess', function(e, data) {
            view.build_table(data, combineName);
        });

        $event_pump.on('model_'+ combineName + 'CreateSuccess', function(e, data) {
            model.readData(element);
            view.setSelectedId(combineName, data)
            view.setCreateId(combineName, "")
            // This should be a function, vur can't do local functions with this hacky class setup
            for (var j = 0; j < elements.length; j++) {
                if (elements[j]["location"] == "local" && elements[j]["type"] != "agent"){
                    model.readLocalData(elements[j], data);
                }
            }
        });

        $event_pump.on('model_'+ combineName + 'DeleteSuccess', function(e, data) {
            model.readData(element);
            view.setSelectedId(combineName, "NONE")
        });
        $event_pump.on('model_'+ combineName + 'FetchSuccess', function(e, data) {
            // This should be a function, vur can't do local functions with this hacky class setup
            for (var j = 0; j < elements.length; j++) {
                if (elements[j]["location"] == "local" && elements[j]["type"] != "agent"){
                    model.readLocalData(elements[j], data);
                }
            }
            view.setSelectedId(combineName, "NONE")
        });
    }


    $event_pump.on('model_error', function(e, xhr, textStatus, errorThrown) {
        let error_msg = textStatus + ': ' + errorThrown + ' - ' + xhr.responseJSON.detail;
        view.error(error_msg);
        console.log(error_msg);
    })
}(ns.model, ns.view ));


