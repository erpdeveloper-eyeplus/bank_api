frappe.ui.form.on("Sales Order", {
    refresh: function(frm) {
        update_payment_status(frm);
    },
    custom_received_amount: function(frm) {
        update_payment_status(frm);
    },
    custom_received_amount_bank: function(frm) {
        update_payment_status(frm);
    },
    custom_amount__and_bank_api_details: function(frm) {
        update_payment_status(frm);
    },
    // validate: function(frm) {
    //     update_payment_status(frm);
    // },
    custom_splitup_count: function(frm) {

        let split_count = cint(frm.doc.custom_splitup_count || 0);
        let total_amount = flt(frm.doc.grand_total || 0);

        if (split_count <= 0) {
            return;
        }

        // Step 1: Check if any row already has Bank API Log
        let has_bank_log = false;
        (frm.doc.custom_amount_and_bank_api_details || []).forEach((row, idx) => {
            if (row.bank_api_log) {
                has_bank_log = true;
                frappe.msgprint(
                    __("Row {0}: Bank API Log already created, please add your amount manually.", [idx + 1])
                );
            }
        });

        if (has_bank_log) {
            return; // Stop further processing
        }

        // Step 2: Clear old rows
        frm.clear_table("custom_amount__and_bank_api_details");

        // Step 3: Calculate split amount
        let split_amount = total_amount / split_count;

        // Step 4: Add rows
        for (let i = 0; i < split_count; i++) {
            let row = frm.add_child("custom_amount__and_bank_api_details");
            row.amount = split_amount;
        }

        frm.refresh_field("custom_amount__and_bank_api_details");
    },
    custom_send_sms: function(frm) {
        if (frm.is_dirty()) {
            frappe.msgprint(__('Please save the document before proceeding.'));
            return;
        }
        frappe.call({
            method: "bank_api.bank_api.utils.py.sales_order.final_function",
            args: { sales_order_name: frm.doc.name },
            freeze: true,
            freeze_message: __("Processing and Sending SMS..."),
            callback: function(r) {
                if (r.message) {
                    if (r.message.status === "success") {
                        let sms_msg = r.message.response.sms_result || "SMS sent successfully.";
                        frappe.msgprint(__(sms_msg));
                    }  else if (r.message.status === "error") {
                        frappe.msgprint(__(r.message.traceback || r.message.message));
                    }
                    frm.reload_doc();
                }
            }
        });
    }    
});

function update_payment_status(frm) {
    let total_received = (frm.doc.custom_received_amount || 0) + (frm.doc.custom_received_amount_bank || 0);
    let has_payment_url = (frm.doc.custom_amount__and_bank_api_details || []).some(row => row.payment_url);

    if (total_received == 0) {
        frm.set_value("custom_payment_status", has_payment_url ? "Payment Link Created" : "Not Received");
    } else {
        if (total_received >= frm.doc.grand_total) {
            frm.set_value("custom_payment_status", "Fully Payment Received");
        } else {
            frm.set_value("custom_payment_status", "Partial Payment Received");
        }
    }

    update_payment_status_color(frm);
}

function update_payment_status_color(frm) {
    let status = frm.doc.custom_payment_status;

    let color = "black"; // default
    if (status == "Not Received") color = "red";
    else if (status == "Payment Link Created") color = "orange";
    else if (status == "Partial Payment Received") color = "blue";
    else if (status == "Fully Payment Received") color = "green";

    $(frm.fields_dict.custom_payment_status.wrapper)
        .find(".control-value")
        .css("color", color);
}


frappe.ui.form.on("Bank API Amount Splitup Table", {
    // amount: function(frm, cdt, cdn) {
    //     let row = locals[cdt][cdn];
    //     if (row.amount) {
    //         frappe.model.set_value(cdt, cdn, "merchant_tran_id", row.name);
    //         frm.save();
    //     }
    // },
    create_bank_api_log: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        // ✅ Validation
        if (row.bank_api_log) {
            frappe.msgprint(
                __("Bank API Log {0} already created for this row", [row.bank_api_log])
            );
            return;
        }
        if (!row.amount) {
            frappe.msgprint(__("Please enter Amount before creating Bank API Log"));
            return;
        }
        if (!row.merchant_tran_id) {
            frappe.msgprint(__("Please enter Merchant Tran ID before creating Bank API Log"));
            return;
        }
        // ✅ Create Bank API Log
        frappe.call({
            method: "bank_api.bank_api.utils.py.sales_order.create_bank_api_log",
            args: {
                doc: {
                    doctype: "Bank API Log",
                    amount: row.amount,
                    merchantid: "9338921",    
                    terminalid: "5411",   
                    merchanttranid: row.merchant_tran_id,
                    billnumber: `${frm.doc.name} - ${row.name}`         
                }
            },
            callback: function(r) {
                if (r.message) {
                    let created_doc = r.message;
            
                    // ✅ Update Bank API Log link in child row
                    frappe.model.set_value(cdt, cdn, "bank_api_log", created_doc.bank_api_log);
            
                    // ✅ Update Ref ID in child row (from API response)
                    if (created_doc.response && created_doc.response.refId) {
                        frappe.model.set_value(cdt, cdn, "ref_id", created_doc.response.refId);
                    }
            
                    frappe.msgprint(
                        __("Bank API Log {0} created successfully. Ref ID: {1}", 
                          [created_doc.bank_api_log, created_doc.response?.refId || "N/A"])
                    );
            
                    // ✅ Refresh child table
                    frm.refresh_field("custom_amount__and_bank_api_details");
                }
            }            
        });
    },
    create_payment_url: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // ✅ Check Bank API Log exists
        if (!row.bank_api_log) {
            frappe.msgprint(__("Please create Bank API Log before generating Payment URL"));
            return;
        }

        frappe.call({
            method: "bank_api.bank_api.doctype.bank_api_log.bank_api_log.generate_qr_code",
            args: {
                docname: row.bank_api_log   // send the Bank API Log name
            },
            callback: function(r) {
                if (!r.exc && r.message) {
                    let result = r.message;
                    // ✅ Update payment_url in child row
                    frappe.model.set_value(cdt, cdn, "payment_url", result.upi_link);
                    frappe.msgprint(
                        __("Payment URL generated successfully for {0}", [row.bank_api_log])
                    );
                    frm.refresh_field("custom_amount__and_bank_api_details");
                }
            },
            freeze: true,
            freeze_message: __("Generating Payment URL...")
        });
    }
});

