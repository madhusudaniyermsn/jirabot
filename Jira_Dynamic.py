import requests
import json
import os
# Import configuration from the separate file
try:
    from jira_config import JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, PROJECT_KEY, ISSUE_TYPE_NAME
except ImportError:
    print("Error: jira_config.py not found or contains errors.")
    print("Please create a jira_config.py file with JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, PROJECT_KEY, and ISSUE_TYPE_NAME.")
    exit()

print(f'{JIRA_URL}, {JIRA_EMAIL}, {JIRA_API_TOKEN}, {PROJECT_KEY}, {ISSUE_TYPE_NAME}')

# --- API Endpoint ---
# This is the standard endpoint for creating issues in JIRA Cloud REST API v3
CREATE_ISSUE_URL = f"{JIRA_URL}/rest/api/3/issue"

# --- Authentication ---
# Using Basic Authentication with email and API token
auth = (JIRA_EMAIL, JIRA_API_TOKEN)

# --- Request Headers ---
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# ===== MAIN EXECUTION =====
if __name__ == "__main__":
    print("--- JIRA Ticket Creation Bot ---")

    # Get ticket details from user input
    ticket_summary = input("Enter Ticket Summary: ").strip()
    ticket_description = input("Enter Ticket Description (optional, press Enter to skip): ").strip()

    if not ticket_summary:
        print("Ticket summary cannot be empty. Aborting.")
        exit()

    # --- Request Body (JSON Payload) ---
    # This is the data structure required by the JIRA API to create an issue
    payload_fields = {
        "project": {
            "key": PROJECT_KEY
        },
        "summary": ticket_summary,
        "issuetype": {
            "name": ISSUE_TYPE_NAME
        }
    }

    # Add description only if provided
    if ticket_description:
         payload_fields["description"] = {
             "type": "doc",
             "version": 1,
             "content": [
                 {
                     "type": "paragraph",
                     "content": [
                         {
                             "type": "text",
                             "text": ticket_description
                         }
                     ]
                 }
             ]
         }

    # Construct the full payload
    payload = json.dumps({"fields": payload_fields})


    # --- Make the API Request ---
    print(f"\nAttempting to create JIRA ticket in project '{PROJECT_KEY}'...")
    try:
        response = requests.post(
            CREATE_ISSUE_URL,
            data=payload,
            headers=headers,
            auth=auth
        )

        # --- Handle the Response ---
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # Parse the JSON response
        response_json = response.json()

        # Print success message and ticket details
        print("JIRA ticket created successfully!")
        print(f"Ticket Key: {response_json['key']}")
        print(f"Ticket URL: {JIRA_URL}/browse/{response_json['key']}")

    except requests.exceptions.RequestException as e:
        # Handle API request errors
        print(f"Error creating JIRA ticket: {e}")
        if response is not None and response.text:
            print(f"Response body: {response.text}")
    except Exception as e:
        # Handle other potential errors
        print(f"An unexpected error occurred: {e}")