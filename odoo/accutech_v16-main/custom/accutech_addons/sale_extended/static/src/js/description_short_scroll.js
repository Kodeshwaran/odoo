///** @odoo-module **/
//
//import { registry } from "@web/core/registry";
//import { FieldHtml } from "@web/views/fields/field_html";
//
//class ScrollableHtmlField extends FieldHtml {
//    setup() {
//        super.setup();
//    }
//
//    patched() {
//        super.patched();
//        const fieldElement = this.el.querySelector(".o_field_html");
//        if (fieldElement) {
//            fieldElement.style.maxHeight = "120px";  // Set the max height
//            fieldElement.style.overflowY = "auto";  // Enable vertical scrolling
//        }
//    }
//}
//
//// Register the custom field widget
//registry.category("fields").add("scrollable_html", ScrollableHtmlField);
