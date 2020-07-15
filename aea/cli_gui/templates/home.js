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

    searchItems(itemType, searchTerm){
        var ajax_options = {
            type: 'GET',
            url: 'api/' + itemType + "/" + searchTerm,
            accepts: 'application/json',
            dataType: 'json'
        };
        var self = this;
        $.ajax(ajax_options)
        .done(function(data) {
            self.$event_pump.trigger('model_searchReadSuccess', [data]);
        })
        .fail(function(xhr, textStatus, errorThrown) {
            self.$event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
        })
    }

    readAgentStatus(agentId) {
        var ajax_options = {
            type: 'GET',
            url: 'api/agent/' + agentId + '/run',
            accepts: 'application/json',
            contentType: 'plain/text'
        };
        var self = this;
        $.ajax(ajax_options)
        .done(function(data) {
            self.$event_pump.trigger('model_AgentStatusReadSuccess', [data]);
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

    fetchAgent(agentId) {
        var ajax_options = {
            type: 'POST',
            url: 'api/fetch-agent',
            accepts: 'application/json',
            contentType: 'application/json',
            dataType: 'json',
            data: JSON.stringify(agentId)
        };
        var self = this;
        $.ajax(ajax_options)
        .done(function(data) {
          var element = {"type": $("#searchItemTypeSelected").html(), "combined": "localSkills"}
            self.$event_pump.trigger('model_' + element["combined"] + 'AddSuccess', [data]);
        })
        .fail(function(xhr, textStatus, errorThrown) {
            self.$event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
        })
    }


    removeItem(element, agentId, itemId) {
        var propertyName = element["type"] +  "_id"
        var ajax_options = {
            type: 'POST',
            url: 'api/agent/' + agentId  + '/' + element["type"]+ '/remove',
            accepts: 'application/json',
            contentType: 'application/json',
            dataType: 'json',
            data: JSON.stringify(itemId)
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
    startAgent(agentId, runConnectionId){
        var ajax_options = {
            type: 'POST',
            url: 'api/agent/' + agentId + '/run',
            accepts: 'application/json',
            contentType: 'application/json',
            dataType: 'json',
            data: JSON.stringify(runConnectionId)
        };
        var self = this;
        $.ajax(ajax_options)
        .done(function(data) {
            self.$event_pump.trigger('model_StartAgentSuccess', [data]);
        })
        .fail(function(xhr, textStatus, errorThrown) {
            self.$event_pump.trigger('model_error', [xhr, textStatus, errorThrown]);
        })
    }
    stopAgent(agentId){
        var ajax_options = {
            type: 'DELETE',
            url: 'api/agent/' + agentId + '/run',
            accepts: 'application/json',
            contentType: 'plain/text'
        };
        var self = this;
        $.ajax(ajax_options)
        .done(function(data) {
            self.$event_pump.trigger('model_StopAgentSuccess', [data]);
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
    setAgentStatus(status){
        $('#agentStatus').html(status);
    }
    setAgentTTY(tty){
        $('#agentTTY').html(tty);
        $('#agentTTY').scrollTop($('#agentTTY')[0].scrollHeight);
    }
    setAgentError(error){
        $('#agentError').html(error);
        $('#agentError').scrollTop($('#agentError')[0].scrollHeight);
    }
    setSearchType(itemType){
        $('#searchItemTypeTable').html(itemType);
        $('#searchItemTypeSelected').html(itemType);
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
                rows += `<tr><td class="id interactive">${data[i].public_id}</td><td class="description interactive">${data[i].description}</td></tr>`;
            }
            $('.' + tableName + ' table > tbody').append(rows);
        }
    }

    error(error_msg) {
        $('.error')
            .html("<br>" + error_msg)
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
                if (confirm("This will completely remove agent: " + id + "'s code and is non-recoverable. Press OK to do this - otherwise press cancel")){

                    e.preventDefault();

                    if (self.validateId(id)) {
                        self.model.deleteItem(e.data.el, id)
                        self.view.setSelectedId(e.data.el["combined"], "NONE")
                    } else {
                        alert('Error: Problem with selected id');
                    }
                    e.preventDefault();
                }
            });

            $('#' + combineName + 'Add').click({el: element}, function(e) {
                var agentId = $('#localAgentsSelectionId').html();
                var itemId =$('#' + e.data.el["combined"] + 'SelectionId').html();

                e.preventDefault();

                if (self.validateId(agentId) && self.validateId(itemId) ) {
                    self.model.addItem(e.data.el, agentId, itemId)
                    self.view.setSelectedId(e.data.el["combined"], "NONE")
                    var tableBody = $("."+ e.data.el["combined"] +"registeredTable");
                    self.clearTable(tableBody);


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
                    self.view.setSelectedId(e.data.el["combined"], "NONE")


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

                // Select the appropriate row
                var tableBody = $(e.target).closest("."+ e.data.el["combined"] +"registeredTable");
                self.clearTable(tableBody);

                $(this).addClass("aea_selected")
                if (e.data.el["combined"] == "localAgents"){
                    self.refreshAgentData(id)
                }
                self.handleButtonStates()
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
                self.handleButtonStates()
            });

            this.$event_pump.on('model_'+ combineName + 'DeleteSuccess', {el: element}, function(e, data) {
                self.model.readData(e.data.el);

                self.refreshAgentData("NONE")
                self.handleButtonStates()

            });
            this.$event_pump.on('model_'+ combineName + 'AddSuccess', {el: element}, function(e, data) {
                self.refreshAgentData(data)
                self.handleButtonStates()

            });
            this.$event_pump.on('model_'+ combineName + 'RemoveSuccess', {el: element}, function(e, data) {
                self.refreshAgentData(data)
                self.handleButtonStates()

            });
            this.$event_pump.on('model_'+ combineName + 'ScaffoldSuccess', {el: element}, function(e, data) {
                self.refreshAgentData(data)
                self.view.setScaffoldId(e.data.el["combined"], "")
                self.handleButtonStates()
            });

        }

        this.$event_pump.on('model_AgentStatusReadSuccess', function(e, data) {
            self.view.setAgentStatus("Agent Status: " + data["status"])
            self.view.setAgentTTY(data["tty"])
            self.view.setAgentError(data["error"])
            self.handleButtonStates()
        });

        this.$event_pump.on('model_searchReadSuccess', function(e, data) {
            self.view.setSearchType(data["item_type"])
            self.view.build_table(data["search_result"], 'searchItemsTable');
            self.handleButtonStates()
        });

        $('#startAgent').click({el: element}, function(e) {
            e.preventDefault();
            var agentId = $('#localAgentsSelectionId').html()
            var connectionId = $('#runConnectionId').val()
            if (self.validateId(agentId)){
                self.model.startAgent(agentId, connectionId)
            }
            else{
                alert('Error: Attempting to start agent with ID: ' + agentId);
            }

            e.preventDefault();
        });
        $('#stopAgent').click({el: element}, function(e) {
            e.preventDefault();
            var agentId = $('#localAgentsSelectionId').html()
            if (self.validateId(agentId)){
                self.model.stopAgent(agentId)
            }
            else{
                alert('Error: Attempting to stop agent with ID: ' + agentId);
            }

            e.preventDefault();
        });
        $('#searchInputButton').click({el: element}, function(e) {
            e.preventDefault();
            var searchTerm = $('#searchInput').val()
            if (self.validateId(searchTerm)){
                var itemType = $("input[name='itemType']:checked").attr('id')
                self.model.searchItems(itemType, searchTerm)
            }
            else{
                alert('Error: Attempting to stop search for: ' + searchTerm);
            }

            e.preventDefault();
        });

        $('.searchItemsTable table > tbody ').on('click', 'tr', {el: element}, function(e) {

            var $target = $(e.target),
                id,
                description;

            id = $target
                .parent()
                .find('td.id')
                .text();


            self.view.setSelectedId("searchItemsTable", id);

            // Select the appropriate row
            var tableBody = $(e.target).closest(".searchItemsTableRegisteredTable");
            self.clearTable(tableBody);

            $(this).addClass("aea_selected")

            self.handleButtonStates()
        });


        $('#searchItemsAdd').click({el: element}, function(e) {
            var agentId = $('#localAgentsSelectionId').html();
            var itemId = $('#searchItemsTableSelectionId').html();
            // It doesn't matter too much what the combined name is as long as it exists
            var itemType = {"type": $("#searchItemTypeSelected").html(), "combined": "localSkills"}

            e.preventDefault();

            if (self.validateId(agentId) && self.validateId(itemId) ) {
                self.model.addItem(itemType, agentId, itemId)
                self.view.setSelectedId("searchItemsTable", "NONE")
                var tableBody = $(e.target).closest(".searchItemsTableRegisteredTable");
                self.clearTable(tableBody);
            } else {
                alert('Error: Problem with one of the selected ids (either agent or ' + itemType);
            }
            e.preventDefault();
        });

        $('#searchAgentsFetch').click({el: element}, function(e) {
            var agentId = $('#searchItemsTableSelectionId').html();
            // It doesn't matter too much what the combined name is as long as it exists
            var itemType = {"type": $("#searchItemTypeSelected").html(), "combined": "localSkills"}

            e.preventDefault();

            if (self.validateId(agentId) ) {
                self.model.fetchAgent(agentId)
                self.view.setSelectedId("searchItemsTable", "NONE")
                var tableBody = $(e.target).closest(".searchItemsTableRegisteredTable");
                self.clearTable(tableBody);
            } else {
                alert('Error: Problem with one of the selected ids (either agent or ' + itemType);
            }
            e.preventDefault();
        });


        this.$event_pump.on('model_error', {el: element}, function(e, xhr, textStatus, errorThrown) {
            var error_msg = textStatus + ': ' + errorThrown + ' - ' + xhr.responseJSON.detail;
            self.view.error(error_msg);
            console.log(error_msg);
        })

        this.handleButtonStates(this);


        $('#localAgentsCreateId').on('input', function(e){
            self.handleButtonStates()
        });
        $('#localAgentsSelectionId').on('input', function(e){
            self.handleButtonStates()
        });
        $('#searchInput').on('input', function(e){
            self.handleButtonStates()
        });

        for (var j = 0; j < elements.length; j++) {
            $('#'+ elements[j]["combined"] + 'ScaffoldId').on('input', function(e){
                self.handleButtonStates()});
        }

        this.getAgentStatus();

    }

    clearTable (tableBody) {
       tableBody.children().each(function(i) {
            $(this).removeClass("aea_selected")
        });
    }

    handleButtonStates(){
        var agentCreateId = $('#localAgentsCreateId').val();
        var agentSelectionId = $('#localAgentsSelectionId').html();
        $('#localAgentsCreate').prop('disabled', !this.validateId(agentCreateId));
        $('#localAgentsDelete').prop('disabled', !this.validateId(agentSelectionId));

        for (var j = 0; j < elements.length; j++) {
            if (elements[j]["location"] == "local" && elements[j]["type"] != "agent"){
                var itemSelectionId = $('#' + elements[j]["combined"] + 'SelectionId').html();
                var isDisabled =  !this.validateId(itemSelectionId);
                $('#' + elements[j]["combined"] + 'Remove').prop('disabled', isDisabled);

                var itemScaffoldId = $('#' + elements[j]["combined"] + 'ScaffoldId').val();
                $('#' + elements[j]["combined"] + 'Scaffold').prop('disabled',
                    !this.validateId(itemScaffoldId) ||
                    !this.validateId(agentSelectionId));


            }
            if (elements[j]["location"] == "registered"){
                var itemSelectionId = $('#' + elements[j]["combined"] + 'SelectionId').html();
                var isDisabled =  !this.validateId(itemSelectionId) || !this.validateId(agentSelectionId);
                $('#' + elements[j]["combined"] + 'Add').prop('disabled', isDisabled);
            }
        }
        // Search buttons
        var searchTerm = $('#searchInput').val();
        $('#searchInputButton').prop('disabled', !this.validateId(searchTerm));
        var searchItem = $('#searchItemsTableSelectionId').html();
        var itemType = $("#searchItemTypeSelected").html();
        var isDisabled =  !this.validateId(searchItem) || !this.validateId(agentSelectionId) || (itemType == "agent");
        $('#searchItemsAdd').prop('disabled', isDisabled);

        var isDisabled =  !this.validateId(searchItem) || (itemType != "agent");
        $('#searchAgentsFetch').prop('disabled', isDisabled);
        if (agentSelectionId != "NONE"){
            $('.localItemHeading').html(agentSelectionId);
        }
        else{
            $('.localItemHeading').html("Local");

        }
    }

    getAgentStatus(){
        var agentId = $('#localAgentsSelectionId').html()
        self = this
        if (self.validateId(agentId)){
            this.model.readAgentStatus(agentId)
        }
        else{
            self.view.setAgentStatus("Agent Status: NONE")
            self.view.setAgentTTY("<br><br><br><br><br>")
            self.view.setAgentError("<br><br><br><br><br>")
        }
        setTimeout(function() {
            self.getAgentStatus()
        }, 500)

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

$( document ).ready(function() {
    c = new Controller(new Model(), new View())
});
