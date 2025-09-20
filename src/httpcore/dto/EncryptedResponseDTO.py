  



from pydantic import BaseModel
from typing import Optional


class EncryptedResponseDTO(BaseModel):
    requestId: str
    service: str
    oaepHashingAlgorithm: str 
    iv: Optional[str] = ""
    encryptedKey: str
    encryptedData: str
    clientInfo: Optional[str] = "" 
    optionalParam: Optional[str] = ""
