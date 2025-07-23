import requests
import json
import time  # For wait before activation

# Configuration
BASE_URL = "https://devrel-ga-14630.api.identitynow-demo.com"
INPUT_FILE = "campaign.txt"

# ----------------------------
# Get OAuth2 Token Function
# ----------------------------
def get_token(client_id, client_secret):
    token_url = f"{BASE_URL}/oauth/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    try:
        response = requests.post(token_url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"Failed to retrieve token. Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error while getting token: {e}")
        return None

# ----------------------------
# Load campaign.txt inputs
# ----------------------------
def load_inputs_from_file(filename):
    inputs = {}
    try:
        with open(filename, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    inputs[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"Input file '{filename}' not found.")
    except Exception as e:
        print(f"Error reading input file: {e}")
    return inputs

# ----------------------------
# Resolve Identity
# ----------------------------
def resolve_identity(identifier, label="Identity"):
    print(f"Searching for {label}: '{identifier}'")

    url = f"{BASE_URL}/v2024/identities?filters=name eq \"{identifier}\""
    response = requests.get(url, headers=headers)
    try:
        data = response.json()
        if isinstance(data, list) and data:
            result = data[0]
            print(f"{label} found by name: {result['name']} (ID: {result['id']})")
            return result["id"]
    except Exception as e:
        print(f"Name lookup failed: {e}")

    url = f"{BASE_URL}/v2024/identities?filters=email eq \"{identifier}\""
    response = requests.get(url, headers=headers)
    try:
        data = response.json()
        if isinstance(data, dict) and data.get("data"):
            result = data["data"][0]
            print(f"{label} found by email: {result['name']} (ID: {result['id']})")
            return result["id"]
    except Exception as e:
        print(f"Email lookup failed: {e}")

    url = f"{BASE_URL}/v3/search/identities"
    response = requests.post(url, headers=headers, json={"query": identifier})
    try:
        data = response.json()
        if isinstance(data, dict) and data.get("results"):
            result = data["results"][0]
            print(f"{label} found by full-text search: {result['name']} (ID: {result['id']})")
            return result["id"]
    except Exception as e:
        print(f"Full-text search failed: {e}")

    print(f"{label} '{identifier}' not found by name, email, or search.")
    return None

# ----------------------------
# Resolve Access Profiles
# ----------------------------
def resolve_access_profiles(profile_names_str):
    profile_ids = []
    not_found = []
    profile_names = [name.strip() for name in profile_names_str.split(",")]

    for name in profile_names:
        print(f"Searching for Access Profile: '{name}'")
        params = {"filters": f"name eq \"{name}\""}
        response = requests.get(f"{BASE_URL}/v3/access-profiles", headers=headers, params=params)

        if response.status_code == 200:
            results = response.json()
            if results:
                profile_id = results[0].get("id")
                profile_ids.append(profile_id)
                print(f"Found Access Profile '{name}' (ID: {profile_id})")
            else:
                print(f"Access Profile '{name}' not found.")
                not_found.append(name)
        else:
            print(f"Failed to search Access Profile '{name}'. Status: {response.status_code}")
            not_found.append(name)

    if not_found:
        print(f"Could not resolve the following Access Profile(s): {', '.join(not_found)}")
        return None
    return profile_ids

# ----------------------------
# Create and Activate Campaign
# ----------------------------
def create_and_activate_campaign(identity_id, reviewer_id, reviewer_name, access_profile_ids, name, description, query):
    payload = {
        "name": name,
        "type": "SEARCH",
        "description": description,
        "searchCampaignInfo": {
            "type": "ACCESS",
            "description": description,
            "query": query,
            "identityIds": [identity_id],
            "reviewer": {
                "type": "IDENTITY",
                "id": reviewer_id,
                "name": reviewer_name
            },
            "accessConstraints": [
                {
                    "type": "ACCESS_PROFILE",
                    "ids": access_profile_ids,
                    "operator": "SELECTED"
                }
            ]
        },
        "autoRevokeAllowed": False,
        "mandatoryCommentRequirement": "NO_DECISIONS"
    }

    print("Creating certification campaign...")
    response = requests.post(f"{BASE_URL}/v2024/campaigns", headers=headers, json=payload)
    if response.status_code in [200, 201]:
        campaign_id = response.json().get("id")
        print(f"Campaign created with ID: {campaign_id}")

        print("Waiting 10 seconds before activation...")
        time.sleep(10)

        print("Activating campaign...")
        activation = requests.post(
            f"{BASE_URL}/v2024/campaigns/{campaign_id}/activate",
            headers=headers,
            json={"timeZone": "Z"}
        )
        if activation.status_code in [200, 202, 204]:
            print("Campaign activated successfully.")
        else:
            print(f"Activation failed. Status: {activation.status_code}, Response: {activation.text}")
    else:
        print(f"Campaign creation failed. Status: {response.status_code}, Response: {response.text}")

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    inputs = load_inputs_from_file(INPUT_FILE)

    if not inputs:
        print("No valid inputs. Exiting.")
        exit()

    client_id = inputs.get("client_id")
    client_secret = inputs.get("client_secret")
    if not client_id or not client_secret:
        print("Missing client_id or client_secret in input file.")
        exit()

    TOKEN = get_token(client_id, client_secret)
    if not TOKEN:
        print("Failed to generate token. Exiting.")
        exit()

    # Global headers set after token is generated
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    identity_name = inputs.get("identity_name")
    reviewer_name = inputs.get("reviewer_name")
    access_profile_names = inputs.get("access_profile_names")
    campaign_name = inputs.get("campaign_name", "Default Campaign")
    campaign_description = inputs.get("campaign_description", "Default Description")
    query_string = inputs.get("query_string", "Access Profile Certification Query")

    if not identity_name or not reviewer_name or not access_profile_names:
        print("Missing one or more required fields in input file.")
        exit()

    identity_id = resolve_identity(identity_name, "Identity")
    if not identity_id:
        print("Cannot proceed without a valid identity.")
        exit()

    reviewer_id = resolve_identity(reviewer_name, "Reviewer")
    if not reviewer_id:
        print("Cannot proceed without a valid reviewer.")
        exit()

    access_profile_ids = resolve_access_profiles(access_profile_names)
    if not access_profile_ids:
        print("Cannot proceed without valid access profiles.")
        exit()

    print("All required inputs successfully resolved.")
    print(f"Identity ID: {identity_id}")
    print(f"Reviewer ID: {reviewer_id}")
    print(f"Access Profile IDs: {access_profile_ids}")

    create_and_activate_campaign(identity_id, reviewer_id, reviewer_name, access_profile_ids, campaign_name, campaign_description, query_string)
