from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
import logging
import os
import json


logger = logging.getLogger("Config")


test_config = "default.env"
config = ".env"

path = Path(os.path.dirname(__file__))           # → httpcore/config
env_path = os.path.join(path.parent.parent, "src", test_config)


# _resources_folder = os.path.join(path, "resources")
# _corporate_key = os.path.join(_resources_folder, "corporate_server_publickey.pem")
# _eazypay_key = os.path.join(_resources_folder, "eazypay_server_publickey.pem")
# _composite_key = os.path.join(_resources_folder, "composite_server_publickey.pem")
# _cibbulk_key = os.path.join(_resources_folder, "cibbulk_server_publickey.pem")

def get_key_path(env: str, filename: str) -> str:
    return os.path.join(path, "resources", env.lower(), filename)

class AppConstantsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file= env_path, env_file_encoding='utf-8')
    
    ENV_TYPE: Literal["UAT", "PROD"] = "UAT"

    BASE_URL: Optional[str] = None  # Set based on ENV_TYPE
    
    LOG_LEVEL: Literal['INFO', 'DEBUG', 'WARN', 'ERROR'] = 'INFO'
    APPLICATION_JSON_CHARSET_UTF_8: str 
    API_KEY: str 
    SHA_512: str 
    X_ID_FINGERPRINT: str 
    X_PRIORITY_HEADER: str 
    ASYMMETRIC_CYPHER_RSA: str 
    SYMMETRIC_CYPHER_AES: str 
    AES: str 
    CHAR_SET: str 
    KEY_LENGTH: int 
    IV_KEY_LENGTH: int 
    WITH_RESPONSE_MODELS: bool = False
    
    EAZYPAY_PUBLIC_KEY_PATH: Optional[str] = ""
    CORPORATE_PUBLIC_KEY_PATH: Optional[str] = ""
    COMPOSITE_PUBLIC_KEY_PATH: Optional[str] = ""
    CIBBULK_PUBLIC_KEY_PATH: Optional[str] = ""
    EAZYPAY_API_KEY: Optional[str] = ""
    CORPORATE_API_KEY: Optional[str] =  ""
    COMPOSITE_API_KEY: Optional[str] = ""
    CIBBULK_API_KEY: Optional[str] = ""
    KEYSTORE_PATH: str
    KEYSTORE_PASSWORD: str
    KEYSTORE_ALIAS: str
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set BASE_URL based on ENV_TYPE
        if self.ENV_TYPE == "PROD":
            self.BASE_URL = "https://apibankingone.icicibank.com/api"
        elif self.ENV_TYPE == "UAT":
            self.BASE_URL = "https://apibankingonesandbox.icicibank.com/api"
        else:
            raise ValueError(f"Unknown ENV_TYPE: {self.ENV_TYPE}")
        
        env_folder = self.ENV_TYPE.lower()
        self.COMPOSITE_PUBLIC_KEY_PATH = get_key_path(env_folder, "composite_server_publickey.pem")
        self.CORPORATE_PUBLIC_KEY_PATH = get_key_path(env_folder, "corporate_server_publickey.pem")
        self.EAZYPAY_PUBLIC_KEY_PATH = get_key_path(env_folder, "eazypay_server_publickey.pem")
        self.CIBBULK_PUBLIC_KEY_PATH = get_key_path(env_folder, "cibbulk_server_publickey.pem")


try:
    
    AppConstants = AppConstantsSettings()
    # AppConstants.COMPOSITE_PUBLIC_KEY_PATH = _composite_key
    # AppConstants.CORPORATE_PUBLIC_KEY_PATH = _corporate_key
    # AppConstants.EAZYPAY_PUBLIC_KEY_PATH = _eazypay_key
    # AppConstants.CIBBULK_PUBLIC_KEY_PATH = _cibbulk_key
except Exception as e: # Handle any potential errors during loading
    logger.debug("Use function load_dotenv_from_path to load .env first")
    AppConstants = None


def load_dotenv_from_path(dotenv_path: str):
    """Loads environment variables from a .env file at a specific path.

    Args:
        dotenv_path: The path to the .env file.  Can be a string or a Path object.

    Returns:
        True if the .env file was successfully loaded, False otherwise.
        Prints an error message if the file is not found.
    """
    global AppConstants
    if not os.path.exists(dotenv_path):  # Check if the file exists
        logger.error(f".env file not found at: {dotenv_path}")  # Informative message
        return False

    try:
        load_dotenv(dotenv_path)  # Load the environment variables
        AppConstants = AppConstantsSettings(** dotenv_values())
        # AppConstants.COMPOSITE_PUBLIC_KEY_PATH = _composite_key
        # AppConstants.CORPORATE_PUBLIC_KEY_PATH = _corporate_key
        # AppConstants.EAZYPAY_PUBLIC_KEY_PATH = _eazypay_key
        # AppConstants.CIBBULK_PUBLIC_KEY_PATH = _cibbulk_key
    except Exception as e: # Handle any potential errors during loading
        logger.error(f"Error loading .env file, check format: {e}")
        return None

