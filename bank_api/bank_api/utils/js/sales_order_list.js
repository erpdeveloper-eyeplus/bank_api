frappe.listview_settings['Sales Order'] = {
    get_indicator: function(doc) {
        if (doc.custom_payment_status == "Not Received") {
            return ["Not Received", "red", "custom_payment_status,=,Not Received"];
        } 
        else if (doc.custom_payment_status == "Payment Link Created") {
            return ["Payment Link Created", "orange", "custom_payment_status,=,Payment Link Created"];
        } 
        else if (doc.custom_payment_status == "Partial Payment Received") {
            return ["Partial Payment Received", "blue", "custom_payment_status,=,Partial Payment Received"];
        } 
        else if (doc.custom_payment_status == "Fully Payment Received") {
            return ["Fully Payment Received", "green", "custom_payment_status,=,Fully Payment Received"];
        } 
        else {
            return [doc.custom_payment_status, "black"];
        }
    }
};
