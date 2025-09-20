import os
import json
import frappe
from dotenv import load_dotenv
from pathlib import Path
from frappe.model.document import Document
import sys

# ✅ Fix path to point to the correct eazypay src folder
# sys.path.insert(0, r"/home/administrator/Downloads/banking integ/python_eazypay_callback/src/eazypay-1.0/src")
import eazypay
from eazypay.api import qr3, QR3RequestDTO

class BankAPILog(Document):
    pass

@frappe.whitelist()
def send_qr3_request(doc):
    try:
        doc = frappe._dict(json.loads(doc)) if isinstance(doc, str) else doc

        # env_path = Path("/home/administrator/Downloads/banking integ/test/devps.env")
        # load_dotenv(dotenv_path=env_path)
        # Build absolute path safely
        import os
        from dotenv import load_dotenv

        env_path = os.path.join(frappe.get_app_path('bank_api'), 'src', 'default.env')
        load_dotenv(env_path)


        qr3_input = {
            "merchantId": str(doc.get("merchantid") or ""),
            "terminalId": str(doc.get("terminalid") or ""),
            "merchantTranId": str(doc.get("merchanttranid") or ""),
            "amount": f"{doc.get('amount'):.2f}",
            "billNumber": str(doc.get("billnumber") or "")
        }

        frappe.errprint("✅ Payload:")
        frappe.errprint(json.dumps(qr3_input, indent=2))

        # dto = QR3RequestDTO(**qr3_input)
        # response = qr3(dto)

        response = qr3(QR3RequestDTO(**qr3_input))

        # Handle dictionary or pydantic response
        if isinstance(response, dict):
            result = response
        else:
            result = json.loads(response)

        frappe.errprint("✅ Final Response:")
        frappe.errprint(json.dumps(result, indent=2))

        # Save data back to your Bank API Log or DocType
        # Save data back to your Bank API Log or DocType
        frappe.db.set_value(doc["doctype"], doc["name"], {
            "ref_id": result.get("refId"),
            "api_message": result.get("message"),
            "response_status": result.get("response"),
            "success": result.get("success"),
            "merchanttranid": result.get("merchantTranId")
        })
        if not result.get("success") or result.get("success") == "false":
            frappe.throw(f"QR3 API Error: {result.get('message') or 'Unknown Error'}")
        return result

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "QR3 Request Failed")
        frappe.throw(f"QR3 API Call Failed: {e}")

# import qrcode

# upi_link = "upi://pay?pa=abc@icici&pn=MyStore&tr=EZY123456789012&am=150&cu=INR&mc=5411"
# img = qrcode.make(upi_link)
# img.save("upi_qr.png")

import frappe
import base64
import io
import string
import secrets
from india_compliance.gst_india.utils.jinja import get_qr_code
from frappe.utils.file_manager import save_file

@frappe.whitelist()
def generate_qr_code(docname):
    doc = frappe.get_doc("Bank API Log", docname)
    sett_doc = frappe.get_doc("Bank API Settings", "Bank API Settings")

    # Build UPI link dynamically
    params = []
    if sett_doc.bank_upi:
        params.append(f"pa={sett_doc.bank_upi}")
    if sett_doc.bank_upi:
        params.append(f"pn=test")
    if doc.ref_id:
        params.append(f"tr={doc.ref_id}")
    if doc.amount:
        params.append(f"am={doc.amount}")
    params.append("cu=INR")  # Required
    if doc.terminalid:
        params.append(f"mc={doc.terminalid}")

    upi_link = "upi://pay?" + "&".join(params)

    # Generate QR code (base64) using get_qr_code
    qr_code_base64 = get_qr_code(upi_link, scale=5)
    img_bytes = base64.b64decode(qr_code_base64)

    # Save QR image as attachment
    filedoc = save_file(
        f"{doc.name}_qr.png",
        img_bytes,
        doc.doctype,
        doc.name,
        is_private=0
    )

    # Update doc image field
    doc.qr_image = filedoc.file_url
    doc.upi_link = upi_link
    doc.save()

    return {"upi_link": upi_link, "qr_image_url": filedoc.file_url}

