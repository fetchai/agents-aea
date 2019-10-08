/*
 * JavaScript file for the application to demonstrate
 * using the API
 */

// Create the namespace instance
var ns = {};

// Get elements passed in from python as this is how they need to be passed into the html
// so best to have it in one place
var elements = []

{%for i in range(0, len)%}
    elements.push({"location": "{{htmlElements[i][0]}}", "type": "{{htmlElements[i][1]}}", "combined": "{{htmlElements[i][2]}}"});
 {% endfor %}



'use strict';

class Model{
    constructor(){
        this.$event_pump = $('body');
    }

    readData(element) {
        // This is massively hacky!
        if (element["location"] == "local" && element["type"] != "agent"){
            return;
        }
        var ajax_options = {
            type: 'GET',
            url: 'api/' + element["type"],
            accepts: 'application/json',
            dataType: 'json'
        };
        var self = this;
        $.ajax(ajax_options)
        .done(function(data) {
            self.$event_pump.trigger('model_' + element["combined"] + 'ReadSuccess', [data]);
        })
        .fail(function(xhr, textStatus, errorThrown) {
            self.$event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
        })
    }

    createItem(element, id){
        var ajax_options = {
            type: 'POST',
            url: 'api/' + element["type"],
            accepts: 'application/json',
            contentType: 'application/json',
            dataType: 'json',
            data: JSON.stringify(id)
        };
        var self = this;
        $.ajax(ajax_options)
        .done(function(data) {
            self.$event_pump.trigger('model_' + element["combined"] + 'CreateSuccess', [data]);
        })
        .fail(function(xhr, textStatus, errorThrown) {
            self.$event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
        })
    }

    deleteItem(element, id){
        var ajax_options = {
            type: 'DELETE',
            url: 'api/' + element["type"] +'/' + id,
            accepts: 'application/json',
            contentType: 'plain/text'
        };
        var self = this;
        $.ajax(ajax_options)
        .done(function(data) {
            self.$event_pump.trigger('model_' + element["combined"] + 'DeleteSuccess', [data]);
        })
        .fail(function(xhr, textStatus, errorThrown) {
            self.$event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
        })
    }

    addItem(element, agentId, itemId) {
        var propertyName = element["type"] +  "_id"
        var ajax_options = {
            type: 'POST',
            url: 'api/agent/' + agentId + '/' + element["type"],
            accepts: 'application/json',
            contentType: 'application/json',
            dataType: 'json',
            data: JSON.stringify(itemId)
        };
        var self = this;
        $.ajax(ajax_options)
        .done(function(data) {
            self.$event_pump.trigger('model_' + element["combined"] + 'AddSuccess', [data]);
        })
        .fail(function(xhr, textStatus, errorThrown) {
            self.$event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
        })
    }

    removeItem(element, agentId, itemId) {
        var propertyName = element["type"] +  "_id"
        var ajax_options = {
            type: 'DELETE',
            url: 'api/agent/' + agentId + '/' + element["type"]+ "/" + itemId,
            accepts: 'application/json',
            contentType: 'plain/text'
        };
        var self = this;
        $.ajax(ajax_options)
        .done(function(data) {
            self.$event_pump.trigger('model_' + element["combined"] + 'RemoveSuccess', [data]);
        })
        .fail(function(xhr, textStatus, errorThrown) {
            self.$event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
        })
    }

    readLocalData(element, agentId) {
        var ajax_options = {
            type: 'GET',
            url: 'api/agent/'+agentId+'/' + element["type"],
            accepts: 'application/json',
            dataType: 'json'
        };
        var self = this;
        $.ajax(ajax_options)
        .done(function(data) {
            self.$event_pump.trigger('model_' + element["combined"] + 'ReadSuccess', [data]);
        })
        .fail(function(xhr, textStatus, errorThrown) {
            self.$event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
        })
    }
    scaffoldItem(element, agentId, itemId){
        var ajax_options = {
            type: 'POST',
            url: 'api/agent/' + agentId + "/" + element["type"] + "/scaffold",
            accepts: 'application/json',
            contentType: 'application/json',
            dataType: 'json',
            data: JSON.stringify(itemId)
        };
        var self = this;
        $.ajax(ajax_options)
        .done(function(data) {
            self.$event_pump.trigger('model_' + element["combined"] + 'ScaffoldSuccess', [data]);
        })
        .fail(function(xhr, textStatus, errorThrown) {
            self.$event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
        })
    }

}

class View{
    constructor(){
        this.$event_pump = $('body');
    }

    setCreateId(tag, id) {
        $('#'+tag+'CreateId').val(id);
    }

    setSelectedId(tag, id) {
        $('#'+tag+'SelectionId').html(id);
    }

    setScaffoldId(tag, id) {
        $('#'+tag+'ScaffoldId').val(id);
    }

    build_table(data, tableName) {
        var rows = ''

        // clear the table
        $('.' + tableName + ' table > tbody').empty();

        // did we get a people array?
        if (tableName) {
            for (let i=0, l=data.length; i < l; i++) {
                rows += `<tr><td class="id">${data[i].id}</td><td class="description">${data[i].description}</td></tr>`;
            }
            $('.' + tableName + ' table > tbody').append(rows);
        }
    }

    error(error_msg) {
        $('.error')
            .text(error_msg)
            .css('visibility', 'visible');
        setTimeout(function() {
            $('.error').css('visibility', 'hidden');
        }, 3000)
    }

}

class Controller{
    constructor(m, v){
        this.model = m;
        this.view = v;
        this.$event_pump = $('body');

        // Get the data from the model after the controller is done initializing
        var self = this;
        setTimeout(function() {
            for (var i = 0; i < elements.length; ++i){
                self.model.readData(elements[i]);
            }
        }, 100)

        // Go through each of the element types setting up call-back and table building functions on the
        // Items which exist
        var self = this;
        for (var i = 0; i < elements.length; i++) {
            var element = elements[i]
            var combineName = element["combined"]
            $('#' + combineName + 'Create').click({el: element}, function(e){
                var id =$('#' + e.data.el["combined"] + 'CreateId').val();

                e.preventDefault();

                if (self.validateId(id)){
                    self.model.createItem(e.data.el, id)
                } else {
                    alert('Error: Problem with id');
                }
            });


            $('#' + combineName + 'Delete').click({el: element}, function(e) {
                var id =$('#' + e.data.el["combined"] + 'SelectionId').html();

                e.preventDefault();

                if (self.validateId(id)) {
                    self.model.deleteItem(e.data.el, id)
                } else {
                    alert('Error: Problem with selected id');
                }
                e.preventDefault();
            });

            $('#' + combineName + 'Add').click({el: element}, function(e) {
                var agentId = $('#localAgentsSelectionId').html();
                var itemId =$('#' + e.data.el["combined"] + 'SelectionId').html();

                e.preventDefault();

                if (self.validateId(agentId) && self.validateId(itemId) ) {
                    self.model.addItem(e.data.el, agentId, itemId)

                } else {
                    alert('Error: Problem with one of the selected ids (either agent or ' + element['type']);
                }
                e.preventDefault();
            });
            $('#' + combineName + 'Remove').click({el: element}, function(e) {
                var agentId = $('#localAgentsSelectionId').html();
                var itemId =$('#' + e.data.el["combined"] + 'SelectionId').html();

                e.preventDefault();

                if (self.validateId(agentId) && self.validateId(itemId) ) {
                    self.model.removeItem(e.data.el, agentId, itemId)

                } else {
                    alert('Error: Problem with one of the selected ids (either agent or ' + element['type']);
                }
                e.preventDefault();
            });

            $('.' + combineName + ' table > tbody ').on('click', 'tr', {el: element}, function(e) {
                var $target = $(e.target),
                    id,
                    description;

                id = $target
                    .parent()
                    .find('td.id')
                    .text();

                self.view.setSelectedId(e.data.el["combined"], id);
                if (e.data.el["combined"] == "localAgents"){
                    self.refreshAgentData(id)
                }
            });

            $('#' + combineName + 'Scaffold').click({el: element}, function(e){
                var agentId = $('#localAgentsSelectionId').html();
                var itemId =$('#' + e.data.el["combined"] + 'ScaffoldId').val();

                e.preventDefault();

                if (self.validateId(agentId) && self.validateId(itemId)){
                    self.model.scaffoldItem(e.data.el, agentId, itemId)
                } else {
                    alert('Error: Problem with id');
                }
            });
            // Handle the model events
            this.$event_pump.on('model_'+ combineName + 'ReadSuccess', {el: element}, function(e, data) {
                self.view.build_table(data, e.data.el["combined"]);
            });

            this.$event_pump.on('model_'+ combineName + 'CreateSuccess', {el: element}, function(e, data) {
                self.model.readData(e.data.el);
                self.view.setSelectedId(e.data.el["combined"], data)
                self.view.setCreateId(e.data.el["combined"], "")
                self.refreshAgentData(data)
            });

            this.$event_pump.on('model_'+ combineName + 'DeleteSuccess', {el: element}, function(e, data) {
                self.model.readData(e.data.el);
                self.view.setSelectedId(e.data.el["combined"], "NONE")
                self.refreshAgentData(data)
            });
            this.$event_pump.on('model_'+ combineName + 'AddSuccess', {el: element}, function(e, data) {
                self.refreshAgentData(data)
                self.view.setSelectedId(e.data.el["combined"], "NONE")
            });
            this.$event_pump.on('model_'+ combineName + 'RemoveSuccess', {el: element}, function(e, data) {
                self.refreshAgentData(data)
                self.view.setSelectedId(e.data.el["combined"], "NONE")
            });
            this.$event_pump.on('model_'+ combineName + 'ScaffoldSuccess', {el: element}, function(e, data) {
                self.refreshAgentData(data)
                self.view.setScaffoldId(e.data.el["combined"], "")
            });
        }


        this.$event_pump.on('model_error', {el: element}, function(e, xhr, textStatus, errorThrown) {
            var error_msg = textStatus + ': ' + errorThrown + ' - ' + xhr.responseJSON.detail;
            self.view.error(error_msg);
            console.log(error_msg);
        })
    }

    // Update lists of protocols, connections and skills for the selected agent
    refreshAgentData(agentId){
        for (var j = 0; j < elements.length; j++) {
            if (elements[j]["location"] == "local" && elements[j]["type"] != "agent"){
                this.model.readLocalData(elements[j], agentId);
            }
        }
    }


    validateId(agentId){
        return agentId != "" && agentId != "NONE";
    }


}


c = new Controller(new Model(), new View())
