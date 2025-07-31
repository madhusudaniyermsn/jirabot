import requests
import json
import os

# --- JIRA Configuration ---
# Your JIRA Cloud URL
JIRA_URL = 'https://madhusudaniyer.atlassian.net'
# Your Atlassian account email address
JIRA_EMAIL = 'madhusudaniyer@msn.com'
# Your generated JIRA API Token
# KEEP THIS TOKEN SECURE! Do not share it.
JIRA_API_TOKEN = 'ATATT3xFfGF0YntCF2RKInL9A9dDXfny_13zLJFVl63jt9hsn0fSpn5D-fMSLKz71PZN-rzjQ-JQ2VJ6nfnmDNJJejWJ9b2IwF-75LQYo9x1xEOmRK2CK5n9z_yMy2z59ZgtUNq7FiwZeTF2adbOVt9XlkLy9xC4O5-vfzpAeDC0aH_V2ChtnAM=8A988FB2' # Inserted your token

# Replace with the key of the JIRA project where you want to create the ticket
PROJECT_KEY = 'AIK' # Example project key from your URL

# Replace with the name or ID of the issue type you want to create (e.g., 'Task', 'Bug', 'Story')
# You might need to check your JIRA project settings for exact names/IDs
ISSUE_TYPE_NAME = 'Task' # Example issue type

# --- Ticket Details ---
TICKET_SUMMARY = 'APCD CT 63 runs'
TICKET_DESCRIPTION = 'As part of APCD CT 63 RUNS we need to tune the Informatica workflow'

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

# --- Request Body (JSON Payload) ---
# This is the data structure required by the JIRA API to create an issue
payload = json.dumps({
    "fields": {
        "project": {
            "key": PROJECT_KEY
        },
        "summary": TICKET_SUMMARY,
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": TICKET_DESCRIPTION
                        }
                    ]
                }
            ]
        },
        "issuetype": {
            "name": ISSUE_TYPE_NAME
        }
        # Add other fields here if needed, e.g.:
        # "assignee": {
        #   "accountId": "YOUR_ACCOUNT_ID" # Or "name": "username" for Server
        # },
        # "priority": {
        #   "name": "High"
        # },
        # "labels": [ "bot-created", "test" ]
    }
})

# --- Make the API Request ---
print(f"Attempting to create JIRA ticket in project '{PROJECT_KEY}'...")
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