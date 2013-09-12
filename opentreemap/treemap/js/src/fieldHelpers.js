// Helper functions for fields defined by the field.html template

"use strict";

var $ = require('jquery'),
    _ = require('underscore');

exports.getField = function getField($fields, name) {
    return $fields.filter('[data-field="' + name + '"]');
};

exports.formToDictionary = function ($form, $editFields) {
    var result = {};
    _.each($form.serializeArray(), function(item) {
        var type = exports.getField($editFields, item.name).data('type');
        if (type === 'bool'){
            return;
        } else if (item.value === '' && (type === 'int' || type === 'float')) {
            // convert empty numeric fields to null
            result[item.name] = null;
        } else if (item.name === 'tree.species' && item.value === '') {
            // convert empty species id strings to null

            result[item.name] = null;
        } else {
            result[item.name] = item.value;
        }
    });
    $form.find('input[name][type="checkbox"]').each(function() {
        result[this.name] = this.checked;
    });
    return result;
};
