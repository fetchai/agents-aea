/*
 * JavaScript file for the application to demonstrate
 * using the API
 */

// Create the namespace instance
let ns = {};

let elements = [{"location": "local", "type": "agents"},
                {"location": "registered", "type": "protocols"}]



function makeCombineName(element){
    return element["location"] + element["type"].slice(0, 1).toUpperCase() + element["type"].slice(1) ;
}


// Create the model instance
ns.model = (function() {
    'use strict';

    let $event_pump = $('body');

    // Return the API
    return {
        readData: function(element) {
            let ajax_options = {
                type: 'GET',
                url: 'api/' + element["type"],
                accepts: 'application/json',
                dataType: 'json'
            };
            $.ajax(ajax_options)
            .done(function(data) {
                $event_pump.trigger('model_' + makeCombineName(element) + 'ReadSuccess', [data]);
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
                $event_pump.trigger('model_' + makeCombineName(element) + 'CreateSuccess', [data]);
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
                $event_pump.trigger('model_' + makeCombineName(element) + 'DeleteSuccess', [data]);
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
        let combineName = makeCombineName(element)
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


        $('.' + combineName + ' table > tbody ').on('click', 'tr', function(e) {
            let $target = $(e.target),
                id,
                description;

            id = $target
                .parent()
                .find('td.id')
                .text();

            view.setSelectedId(combineName, id);
        });
        // Handle the model events
        $event_pump.on('model_'+ combineName + 'ReadSuccess', function(e, data) {
            view.build_table(data, combineName);
        });

        $event_pump.on('model_'+ combineName + 'CreateSuccess', function(e, data) {
            model.readData(element);
            view.setSelectedId(combineName, data)
            view.setCreateId(combineName, "")
        });

        $event_pump.on('model_'+ combineName + 'DeleteSuccess', function(e, data) {
            model.readData(element);
            view.setSelectedId(combineName, "NONE")
        });
    }


    $event_pump.on('model_error', function(e, xhr, textStatus, errorThrown) {
        let error_msg = textStatus + ': ' + errorThrown + ' - ' + xhr.responseJSON.detail;
        view.error(error_msg);
        console.log(error_msg);
    })
}(ns.model, ns.view ));


