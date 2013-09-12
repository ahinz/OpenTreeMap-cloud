"use strict";

// For modal dialog on jquery
require('bootstrap');

var $ = require('jquery'),
    _ = require('underscore'),
    otmTypeahead = require('./otmTypeahead'),  // Override typeahead from bootstrap
    inlineEditForm = require('./inlineEditForm'),
    mapManager = require('./mapManager'),
    BU = require('BaconUtils'),
    plotMover = require('./plotMover'),
    plotMarker = require('./plotMarker'),
    uniqueIdForUdfRows = 0;

function addModalTrigger(element) {
    var $e = $(element);
    var $target = $($e.data('modal'));

    $e.click(function() {
        $target.modal('toggle');
    });
}

function nextUniqueIdForUdfRows() {
    uniqueIdForUdfRows += 1;
    return uniqueIdForUdfRows;
}

exports.init = function(options) {
    _.each(options.typeaheads, function(typeahead) {
        otmTypeahead.create(typeahead);
    });

    var udfRowTemplate = _.template(
        '<tr data-value-id="" data-ref-id="<%= refid %>">' +
            '<% _.each(fields, function (field) { %>' +
            '<td> <%= field %> </td>' +
            '<% }) %>' +
            '</tr>');

    // Wire up stewardships
    $('a[data-udf-id]').click(function() {
        var id = $(this).data('udf-id');
        var fields = $('table[data-udf-id="' + id + '"] * [data-field-name]').toArray();

        var data = _.map(fields, function(field) { return $(field).val(); });

        $(this).closest('table').append(udfRowTemplate({
            fields: data,
            refid: nextUniqueIdForUdfRows()
        }));
    });

    addModalTrigger(options.photos.show);
    var $form = $(options.photos.form);
    $(options.photos.upload).click(function() { $form.submit(); });

    inlineEditForm.init(
        _.extend(options.inlineEditForm, { onSaveBefore: onSaveBefore }));

    mapManager.init({
        config: options.config,
        selector: '#map',
        center: options.plotLocation.location,
        zoom: mapManager.ZOOM_PLOT
    });

    plotMarker.init(mapManager.map);

    plotMover.init({
        mapManager: mapManager,
        plotMarker: plotMarker,
        inlineEditForm: inlineEditForm,
        editLocationButton: options.plotLocation.edit,
        cancelEditLocationButton: options.plotLocation.cancel,
        location: options.plotLocation.location
    });

    function onSaveBefore(data) {
        plotMover.onSaveBefore(data);
    }
};
