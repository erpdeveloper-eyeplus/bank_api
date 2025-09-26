import frappe
import json
from bank_api.bank_api.doctype.bank_api_log.bank_api_log import send_qr3_request
def validate(doc, action):
    # --- Bank API Splitup Details ---
    has_payment_url = False
    tot_amt = 0
    rece_cash_amt = 0

    if doc.custom_amount__and_bank_api_details:
        for row in doc.custom_amount__and_bank_api_details:
            if row.amount:
                tot_amt += row.amount
            if row.paid_amount:
                rece_cash_amt += row.paid_amount
            if row.payment_url:  
                has_payment_url = True

        # Set totals
        doc.custom_total_amount_in_splitup = tot_amt
        diff_amt = doc.grand_total - tot_amt
        doc.custom_difference_amount = diff_amt
        doc.custom_received_amount_bank = rece_cash_amt

        # Show warning if mismatch
        # if diff_amt != 0:
        #     frappe.msgprint(
        #         f"⚠️ The split-up total ({tot_amt}) does not match the Grand Total ({doc.grand_total}). "
        #         f"Difference: {diff_amt}"
        #     )
    else:
        doc.custom_total_amount_in_splitup = 0
        doc.custom_difference_amount = 0
        doc.custom_received_amount_bank = 0

    # --- Service Order Payment Details ---
    rece_cash_amt = 0
    if doc.custom_service_order_payment_details:
        for i in doc.custom_service_order_payment_details:
            if i.amount:
                rece_cash_amt += i.amount
    doc.custom_received_amount = rece_cash_amt

    # --- Payment Status Logic ---
    total_received = (doc.custom_received_amount or 0) + (doc.custom_received_amount_bank or 0)
    if total_received == 0:
        if has_payment_url:  
            doc.custom_payment_status = "Payment Link Created"
        else:
            doc.custom_payment_status = "Not Received"
    else:
        if total_received >= doc.grand_total:
            doc.custom_payment_status = "Fully Payment Received"
        else:
            doc.custom_payment_status = "Partial Payment Received"


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

import frappe
import http.client
import json

@frappe.whitelist()
def send_payment_sms(docname):
    """Send payment SMS via MSG91 Flow API"""
    doc = frappe.get_doc("Sales Order", docname)

    if doc.custom_common_number:
        mobile_number = doc.custom_moile_number
        if not mobile_number:
            frappe.throw("Please enter Mobile Number for sending SMS (Common Number).")

        # ✅ Ensure +91 country code
        mobile_number = format_mobile_with_country_code(mobile_number)

        for row in doc.custom_amount__and_bank_api_details:
            if not row.payment_url:
                frappe.throw(f"No payment URL for row {row.name}, cannot send SMS.")

            send_sms_via_msg91(
                mobiles=mobile_number,
                customer_name=doc.customer_name,
                amount=row.amount,
                order_no=doc.name,
                payment_url=row.payment_url
            )

        return {"status": "success", "response": "SMS sent to common number."}

    elif doc.custom_different_number:
        for row in doc.custom_amount__and_bank_api_details:
            if not row.sms_number:
                frappe.throw(f"No mobile number for row {row.name}, cannot send SMS.")

            if not row.payment_url:
                frappe.throw(f"No payment URL for row {row.name}, cannot send SMS.")

            # ✅ Ensure +91 country code
            sms_number = format_mobile_with_country_code(row.sms_number)

            send_sms_via_msg91(
                mobiles=sms_number,
                customer_name=doc.customer_name,
                amount=row.amount,
                order_no=doc.name,
                payment_url=row.payment_url
            )

        return {"status": "success", "response": "SMS sent to different numbers."}

    else:
        frappe.throw("Please select either Common Number or Different Number before sending SMS.")


def send_sms_via_msg91(mobiles, customer_name, amount, order_no, payment_url):
    """Helper to send SMS using MSG91 Flow API and log it in SMS Log"""
    try:
        conn = http.client.HTTPSConnection("control.msg91.com")

        payload = json.dumps({
            "template_id": "68cfc806b798b0676a4aab05",  # Replace with your actual template_id
            "short_url": "1",
            "short_url_expiry": "3600",
            "realTimeResponse": "1",
            "recipients": [
                {
                    "mobiles": str(mobiles),
                    "var1": customer_name,
                    "var2": str(amount),
                    "var3": order_no,
                    "var4": payment_url
                }
            ]
        })

        headers = {
            'accept': "application/json",
            'authkey': get_msg91_authkey(),
            'content-type': "application/json"
        }

        conn.request("POST", "/api/v5/flow", payload, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")

        # ✅ Build the actual SMS text (same as what customer receives)
        message_text = (
            f"Dear {customer_name}, your payment of Rs. {amount} for Invoice/Order {order_no} "
            f"towards purchase from Eyeplus Electronics is pending. "
            f"Please click the link to complete the payment: {payment_url} "
            f"EYEPLUS ELECTRONICS INDIA LLP"
        )

        # ✅ Create SMS Log entry
        frappe.get_doc({
            "doctype": "SMS Log",
            "sent_on": frappe.utils.now(),
            "message": message_text,
            "no_of_requested_sms": 1,
            "no_of_sent_sms": 1 if res.status == 200 else 0,
            "requested_numbers": mobiles,
            "sent_to": mobiles
        }).insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.logger().info(f"MSG91 SMS Response: {data}")
        return data

    except Exception as e:
        frappe.log_error(f"MSG91 SMS Sending Failed: {str(e)}")
        return str(e)
    

def get_msg91_authkey():
    """Fetch MSG91 Authkey from SMS Settings Parameters table"""
    authkey = frappe.db.get_value(
        "SMS Parameter",
        {"parent": "SMS Settings", "parameter": "apiKey"},
        "value"
    )
    if not authkey:
        frappe.throw("MSG91 API Key is missing in SMS Settings Parameters (parameter = apiKey).")
    return authkey


def format_mobile_with_country_code(mobile):
    """Ensure mobile number has country code (default 91 for India)"""
    mobile = str(mobile).strip()
    if not mobile.startswith("91"):
        mobile = "91" + mobile
    return mobile





