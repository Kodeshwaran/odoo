odoo.define('employee_documents.front_end', function(require) {
    "use strict";

    var ajax = require("web.ajax")
    var rpc = require("web.rpc")
    require('web.dom_ready');
    var session = require('web.session');
    console.log("initial")

   $("#joining_date_proposed").change(function() {
        console.log("fergfdgbdgfgbgb")
        var joining_date_proposed = document.getElementById('joining_date_proposed').value
        var expected_joining_date = document.getElementById('expected_joining_date').value
        console.log("vdsfvdfvxc fbxdf")
        ajax.jsonRpc('/joining_date_proposed/check', 'call', { 'joining_date_proposed': joining_date_proposed, 'expected_joining_date': expected_joining_date })
            .then(function(result) {
                if (result == true) {
                    $(".joining_date_wrong").removeClass('d-none');
                    $(".submit").prop('disabled', true);
                } else if (result === false) {
                    $(".joining_date_wrong").addClass('d-none');
                    $(".submit").prop('disabled', false);
                }
            })
    });

});