# app/const.py

from storage_server.app.config_loader import config

# ------------------------------------------------------------
# Salesforce REST API base URL
# ------------------------------------------------------------
SF_BASE_URL = (
    f"{config['salesforce']['base_url']}"
    f"/services/data/{config['salesforce']['api_version']}"
)

# ------------------------------------------------------------
# sObject endpoints (collection)
# ------------------------------------------------------------
SF_URL_CONTENT_VERSION = f"{SF_BASE_URL}/sobjects/ContentVersion"
SF_URL_DOWNLOADMASTER = f"{SF_BASE_URL}/sobjects/DownloadMaster__c"

def sf_url_contentversion_record(record_id: str) -> str:
    return f"{SF_URL_CONTENT_VERSION}/{record_id}"

def sf_url_downloadmaster_record(record_id: str) -> str:
    return f"{SF_URL_DOWNLOADMASTER}/{record_id}"

SF_URL_TOKEN = f"{config['salesforce']['base_url']}/services/oauth2/token"

# ------------------------------------------------------------
# Salesforce Auth (JWT Bearer Flow)
# ------------------------------------------------------------
# Salesforce OAuth2 JWT Bearer Flow grant_type
SF_GRANT_TYPE_JWT = "urn:ietf:params:oauth:grant-type:jwt-bearer"
SF_CLIENT_ID = config["salesforce"]["client_id"]
SF_USERNAME = config["salesforce"]["username"]
SF_AUDIENCE = config["salesforce"]["audience"]  # e.g. "http://127.0.0.1:8000"
SF_PRIVATE_KEY_PATH = config["security"]["sf_private_key"]

with open(SF_PRIVATE_KEY_PATH, "r") as f:
    SF_PRIVATE_KEY = f.read()

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
LOG_OUTPUT = config["log"]["output"]
LOG_LEVEL = config["log"]["level"].upper()

# ------------------------------------------------------------
# Queue directory (raw path string)
# ------------------------------------------------------------
QUEUE_DIR = config["paths"]["queue_dir"]

# ------------------------------------------------------------
# HTTP Retry Policy
# ------------------------------------------------------------
HTTP_RETRY_COUNT = 3
HTTP_RETRY_DELAY = 1.0  # seconds
