import sys, os, json, frappe
from frappe.utils import now
from http import HTTPStatus

# ✅ Ensure Python can find `httpcore` inside `src`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

# ✅ Import after path setup
from httpcore.utils.CallbackUtils import decrypt_callback


@frappe.whitelist(allow_guest=True)
def callback():
    try:
        # Step 1: Get raw data from request
        data = frappe.request.get_data(as_text=True)
        frappe.log_error("Raw Callback Data", data)

        if not data:
            return {
                "http_status_code": HTTPStatus.BAD_REQUEST,
                "message": "Empty request body"
            }

        # Step 2: Parse JSON
        try:
            encrypted_payload = json.loads(data)
        except json.JSONDecodeError as json_err:
            return {
                "http_status_code": HTTPStatus.BAD_REQUEST,
                "message": f"Invalid JSON format: {json_err}"
            }

        # Step 3: Decrypt the payload
        decrypted_payload = decrypt_callback(encrypted_payload)
        if isinstance(decrypted_payload, str):
            decrypted_payload = json.loads(decrypted_payload)

        frappe.log_error("Decrypted Payload", json.dumps(decrypted_payload))

        if not decrypted_payload:
            return {
                "http_status_code": HTTPStatus.BAD_REQUEST,
                "message": "Failed to decrypt payload"
            }

        # Step 4: Get merchantTranId and update Bank API Log
        merchant_tran_id = decrypted_payload.get("merchantTranId")
        if not merchant_tran_id:
            return {
                "http_status_code": HTTPStatus.BAD_REQUEST,
                "message": "Missing merchantTranId"
            }

        docs = frappe.get_all("Bank API Log", filters={"merchanttranid": merchant_tran_id}, limit=1)
        if not docs:
            frappe.log_error("Not Found", f"No Bank API Log for {merchant_tran_id}")
            return {
                "http_status_code": HTTPStatus.NOT_FOUND,
                "message": f"No Bank API Log for {merchant_tran_id}"
            }

        doc = frappe.get_doc("Bank API Log", docs[0].name)

        # Step 5: Update fields
        doc.db_set("txn_status", decrypted_payload.get("TxnStatus"))
        doc.db_set("bank_rrn", decrypted_payload.get("BankRRN"))
        doc.db_set("payer_name", decrypted_payload.get("PayerName"))
        doc.db_set("payer_mobile", decrypted_payload.get("PayerMobile"))
        doc.db_set("payer_va", decrypted_payload.get("PayerVA"))
        doc.db_set("payer_amount", decrypted_payload.get("PayerAmount"))
        doc.db_set("txn_init_date", decrypted_payload.get("TxnInitDate"))
        doc.db_set("txn_completion_date", decrypted_payload.get("TxnCompletionDate"))
        doc.db_set("callback_received_at", now())

        return {
            "http_status_code": HTTPStatus.OK,
            "message": "Callback processed successfully",
            "status": "success"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "ICICI Webhook Failed")
        return {
            "http_status_code": HTTPStatus.INTERNAL_SERVER_ERROR,
            "message": f"Webhook Failed: {str(e)}"
        }


@frappe.whitelist(allow_guest=True)
def test_func():
    # Sample encrypted data
    encrypted_payload = {
        "requestId": "",
        "service": "UPI",
        "encryptedKey": "mvXXhDUz2WITAfAywLLwgzwRtyy8iUxk/7xNNP7YpSSJQsyhJUGMRPJjYt1mhZxfMlQE2bxiJcFdm67SKK5xybGk54wrL6Jr1w3sQohDeV6xJXJA3gQ4PQBX5U8IARUy0dvKOTM6+csBQiZ5p7O8ihuCUL8bzuXORqf+iJpgPNq0ffzr2c8sFslVkfhgawYe3whF/sgp7qycCHTH6dxko1HgKmFixfdNpLIyO5WxLB1XyizTiZG9Ceasl/48U5fLyc1qyPL2gRhwlJqqSkHVnXABlUZDa6uB3PHqNI6LhAEwqRO7WF8PKz3apTo+sdmQDJItT0DW2RDuXGldJ/ZUjecnNtmr9T5GTvcRx0hozDHgOJH8znIDA2bS3rer3+V3lW9BgTI4XeUiyumgpJrpNjFu0F3BVFTCYV6Fx+BNC2lxA6ZXJ36YoMK1WVlk3CqAe5Ht95QOyHlWZT+1GkwuWRB6zMfmRjnbsF/npuyx78C/qLABGfoex7z1O4U0DcSiByMyylMpAaIVtyy1XpjcqzXMjTg5zC5RsLqUuQ8Z5ItZsyt0hNuYX5HxvIBWQ4RnTNhw9vwIo1WufEgNeVoFcXa77xmUa99N7qK72nwEeq8WiAhM3yWUt7qfiPEXJ7/n98ORK0XA1Ca5kZpUU9MP1oYqfNEh0VxjJ3yFvEoyLvw=",
        "oaepHashingAlgorithm": "NONE",
        "iv": "",
        "encryptedData": "1K30Z/wvLFpc3inAqKsiU2wdvsECDMDFu0xcIrSqzQJh4qlLrGfGl/f9JQSnBbc5fePOWcFc/XKHO2veAuV1JK/4gfGaLPyaNYA/PTNEN+fOrumNXe33cg0ZjboffO/eujattGHaqdETkiyWQXcA+eRqDWLBD9+s3snN1lDaou8HUEBohUNEUM80V0nu7kWy5y7mi+qT0UrRzEEtrQ3Xg1jONpcVhokJLEH77VsLv21uE2wDzHJNih+NCchVnjklb9xQ1rRLusfRFENBCRA+6AavlTIsJ0j7vI/LxsmYNpAKlZYvc14Fi/On49imtQ0R2VSjcfmCSsZIRh+34fi0e1Hs1zgF6yf0g0HoekmV4NGLm3LfJtt5zNSmrLXphE0P0DUzoXH080LkmZJaVR9UsWoUE8xQ8I3RNDhKD1OV1shg7XqUO/bvYzaLhO1o+Nc50+B6Rv2ZZ7jtgY4u1rFBhQ==",
        "clientInfo": "",
        "optionalParam": ""
    }

    result = decrypt_callback(encrypted_payload)

    if isinstance(result, str):
        result = json.loads(result)

    print("🔓 Decrypted Response:\n", json.dumps(result, indent=2) if result else "❌ Decryption failed")
