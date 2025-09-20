import frappe
import json
from bank_api.bank_api.doctype.bank_api_log.bank_api_log import send_qr3_request
def validate(doc, action):
    if doc.custom_amount__and_bank_api_details:
        tot_amt = 0
        for row in doc.custom_amount__and_bank_api_details:
            if row.amount:
                tot_amt += row.amount

        # Set total and difference
        doc.custom_total_amount_in_splitup = tot_amt
        diff_amt = doc.grand_total - tot_amt
        doc.custom_difference_amount = diff_amt

        # Show message if mismatch
        if diff_amt != 0:
            frappe.msgprint(
                f"⚠️ The split-up total ({tot_amt}) does not match the Grand Total ({doc.grand_total}). "
                f"Difference: {diff_amt}"
            )
    else:
        doc.custom_total_amount_in_splitup = 0
        doc.custom_difference_amount = 0

@frappe.whitelist()
def create_bank_api_log(doc):
    """Create Bank API Log without calling QR3 API"""
    try:
        # Convert doc string to dict if coming from JS
        doc = frappe._dict(json.loads(doc)) if isinstance(doc, str) else doc

        bank_api_log = frappe.new_doc("Bank API Log")
        bank_api_log.amount = doc.get("amount")
        bank_api_log.merchantid = doc.get("merchantid")
        bank_api_log.terminalid = doc.get("terminalid")
        bank_api_log.merchanttranid = doc.get("merchanttranid")
        bank_api_log.billnumber = doc.get("billnumber")
        bank_api_log.insert()
        frappe.db.commit()

        result = None
        if bank_api_log.name:
            result = send_qr3_request(bank_api_log.as_dict())

        return {
            "bank_api_log": bank_api_log.name,
            "response": result
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Bank API Log Creation Failed")
        frappe.throw(f"Bank API Log Creation Failed: {e}")

@frappe.whitelist()
def send_payment_sms(docname):
    """Send SMS with payment_url based on Common/Different Number option"""
    doc = frappe.get_doc("Sales Order", docname)  # or your parent doctype

    if doc.custom_common_number:
        mobile_number = doc.custom_moile_number
        if not mobile_number:
            frappe.throw("Please enter Mobile Number for sending SMS (Common Number).")

        urls = [d.payment_url for d in doc.custom_amount__and_bank_api_details if d.payment_url]
        if not urls:
            frappe.throw("No Payment URLs available to send.")

        message = "Payment Links:\n" + "\n".join(urls)
        resp = send_sms_via_settings(mobile_number, message)
        return {"status": "success", "response": resp}

    elif doc.different_number:
        for row in doc.custom_amount__and_bank_api_details:
            if row.sms_number and row.payment_url:
                message = f"Payment Link: {row.payment_url}"
                send_sms_via_settings(row.sms_number, message)
            elif row.sms_number and not row.payment_url:
                frappe.msgprint(f"No payment URL for row {row.name}, skipping SMS.")
            elif not row.sms_number:
                frappe.msgprint(f"No mobile number for row {row.name}, skipping SMS.")

        return {"status": "success", "response": "SMS sent to different numbers."}

    else:
        frappe.throw("Please select either Common Number or Different Number before sending SMS.")

import frappe
import urllib.request
import urllib.parse

def send_sms_via_settings(numbers, message):
    # Get SMS Settings
    sms_settings = frappe.get_doc("SMS Settings")

    # Base URL
    url = sms_settings.sms_gateway_url

    # Collect parameters from settings
    params = {}
    for p in sms_settings.parameters:
        params[p.parameter] = p.value

    # Add dynamic params
    params[sms_settings.message_parameter] = message
    params[sms_settings.receiver_parameter] = numbers

    # Encode params
    data = urllib.parse.urlencode(params).encode("utf-8")

    # Send request
    request = urllib.request.Request(url)
    f = urllib.request.urlopen(request, data)
    return f.read()
