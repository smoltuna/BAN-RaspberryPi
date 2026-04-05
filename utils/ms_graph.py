import json
import requests


def get_new_access_token_using_refresh_token():
    """
    Refreshes the access token using the refresh token stored in "utils/token.json".

    Reads the refresh token from the JSON file, sends a request to refresh the token,
    and updates the JSON file with the new token.

    Returns:
    - token (dict): A dictionary containing the new access token and other token information.
    """
    # Read old token from json file
    with open("utils/token.json", "r") as file:
        data = json.load(file)
    old_refresh_token = data.get("refresh_token")
    if not old_refresh_token:
        raise RuntimeError("Missing refresh_token in utils/token.json. Run generate_token.py to authenticate.")

    # Refresh old token
    request_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    scope_list = ["https://graph.microsoft.com/Files.ReadWrite.All"]
    scope = "%20".join(scope_list)
    redirect_uri = (
        f"http://localhost:8000/callback"
    )
    payload = {
        "scope": scope,
        "redirect_uri": redirect_uri,
        "grant_type": "refresh_token",
        "refresh_token": old_refresh_token,
    }
    response = requests.post(url=request_url, headers=headers, data=payload)
    responseText = response.text
    token = json.loads(responseText)
    if "access_token" not in token:
        error_text = token.get("error_description", responseText)
        raise RuntimeError(f"Token refresh failed: {error_text}")

    # Overwrite the json file with the new token
    with open("utils/token.json", "w") as file:
        json.dump(token, file, indent=4)

    return token

