"""
ERPNext REST API integration.
Pushes raw HL7 messages into the "Lab Machine Message" doctype.
"""
import logging
import requests

logger = logging.getLogger(__name__)


class ERPNextClient:
    def __init__(self, url: str, api_key: str, api_secret: str):
        self.base_url = url.rstrip("/")
        self.headers = {
            "Authorization": f"token {api_key}:{api_secret}",
            "Content-Type": "application/json",
        }

    def _get(self, endpoint: str, params: dict = None):
        url = f"{self.base_url}{endpoint}"
        resp = requests.get(url, headers=self.headers, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _post(self, endpoint: str, data: dict):
        url = f"{self.base_url}{endpoint}"
        resp = requests.post(url, headers=self.headers, json=data, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def test_connection(self):
        """Verify API credentials are valid."""
        try:
            result = self._get("/api/method/frappe.auth.get_logged_user")
            return {"success": True, "user": result.get("message", "")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_lab_machine_message(self, machine_make, machine_model, lab_test_name, message, timestamp):
        """Create a Lab Machine Message record in ERPNext from a raw HL7 message."""
        data = {
            "date_and_time": timestamp,
            "machine_make": machine_make,
            "machine_model": machine_model,
            "lab_test_name": lab_test_name,
            "message": message,
        }
        result = self._post("/api/resource/Lab Machine Message", data)
        return result.get("data", {}).get("name")
