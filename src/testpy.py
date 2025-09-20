from httpcore.AppConstants import load_dotenv_from_path
env_path ="/home/administrator/Downloads/banking integ/test/devps.env"
load_dotenv_from_path(env_path)
from eazypay.api import  TransactionStatus1RequestDTO, transaction_status1 
from eazypay.api import  *
from httpcore.utils.CallbackUtils import decrypt_callback
from pydantic import BaseModel, Field
eazypay_transaction_status_payload = {
    "merchantId": "612333",
    "terminalId": "5411",
    "merchantTranId": "vuup9diupeisa5",
    "subMerchantId": "612333"
  }
# response = transaction_status1(TransactionStatus1RequestDTO( **eazypay_transaction_status_payload))
# print("EAZYPAY Transaction Status Response:\n" , response)
qr3_input = {
"amount": "1.00",
"merchantId" : "612333",
"terminalId": "5411",
"merchantTranId": "dres12",
"billNumber": "2305",
}
response4 = qr3(QR3RequestDTO(**qr3_input))
print("\n\nQR3Request:\n" , response4)
# def test_decryption():
#     encrypted_data = {
#         'requestId': '',
#         'service': 'UPI',
#         'encryptedKey':'ll9UqF/fWH/... ',
#         'oaepHashingAlgorithm': 'NONE',
#         'iv': '',
#         'encryptedData':'+v7vE3Tx/qCEop2GE0...',
#         'clientInfo': '',
#         'optionalParam': ''
#     }
#     decrypted = decrypt_callback(encrypted_data)
#     print("Decrypted response:", decrypted)
# if __name__ == "__main__":
#     test_decryption()
