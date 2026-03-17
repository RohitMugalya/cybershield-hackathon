import requests
from datetime import datetime

VAPI_API_KEY = "1c68238b-9034-4631-9752-91102a92c892"
ASSISTANT_ID = "82bd7f1b-d40c-4a00-ae3f-be8dd6551de3"
PHONE_NUMBER_ID = "0290ec0c-e67e-4288-9b9e-f0df08a265ca"

def trigger_dispatch_call(incident_type, location):

    phone = +919443582753

    current_time = datetime.now().strftime("%I:%M %p")

    summary = f"{incident_type} detected at {location} at {current_time} by the surveillance system."

    url = "https://api.vapi.ai/call"

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "assistantId": ASSISTANT_ID,
        "phoneNumberId": PHONE_NUMBER_ID,
        "customer": {
            "number": phone
        },
        "assistantOverrides": {
            "variableValues": {
                "incident_type": incident_type,
                "location": location,
                "summary": summary
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    return response.json()