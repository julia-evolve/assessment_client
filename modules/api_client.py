import requests


def send_to_assessment_api(payload, api_url):
    """
    Send JSON payload to the assessment API.

    Args:
        email: Email address
        payload: JSON payload to send
        api_url: API endpoint URL

    Returns:
        Response object or error message
    """
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        return response
    except Exception as e:
        return str(e)
