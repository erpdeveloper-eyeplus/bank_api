// Copyright (c) 2025, Eyeplus and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bank API Log", {
	refresh: function(frm) {
        frm.add_custom_button(__('Send Request'), function() {
            if (frm.doc.ref_id) {
                frappe.throw(
                    __("This document already has a Ref ID ({0}). You cannot send again.", [frm.doc.ref_id])
                );
                return;
            }
            frappe.call({
                method: "bank_api.bank_api.doctype.bank_api_log.bank_api_log.send_qr3_request",
                args: {
                    doc: frm.doc
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint({
                            title: __('API Response'),
                            message: __('Transaction Initiated Successfully. Ref ID: ') + r.message.refId,
                            indicator: 'green'
                        });
                        frm.reload_doc();  // Refresh the form to show updated fields
                    } else {
                        frappe.msgprint({
                            title: __('Error'),
                            message: __('No response from server'),
                            indicator: 'red'
                        });
                    }
                },
                error: function(err) {
                    frappe.msgprint(__('Server error: ') + err.message);
                },
                freeze: true,
                freeze_message: __('Sending request...')
            });
        });
        frm.add_custom_button(__('Generate QR Code'), function() {
            frappe.call({
                method: "bank_api.bank_api.doctype.bank_api_log.bank_api_log.generate_qr_code",
                args: {
                    docname: frm.doc.name
                },
                callback: function(r) {
                    if (!r.exc) {
                        frappe.msgprint("QR Code Generated");
                        frm.reload_doc();
                    }
                }
            });
        });
    }
});
