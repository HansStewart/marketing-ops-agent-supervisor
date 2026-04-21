import requests
from app.config import settings

BASE_URL = "https://api.hubapi.com"

def create_deal(properties: dict):
    """
    properties example:
    {
      "dealname": "...",
      "amount": "12000",
      "pipeline": "default",
      "dealstage": "appointmentscheduled"
    }
    """
    url = f"{BASE_URL}/crm/v3/objects/deals"
    headers = {
        "Authorization": f"Bearer {settings.hubspot_access_token}",
        "Content-Type": "application/json",
    }
    payload = {"properties": properties}
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    return resp.json()