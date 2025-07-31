import requests
import json
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import re
import time

# --- JIRA Configuration (Loaded from jira_config.py) ---
try:
    from jira_config import JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, PROJECT_KEY, ISSUE_TYPE_NAME
except ImportError:
    print("Error: jira_config.py not found or contains errors.")
    print("Please create a jira_config.py file with JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, PROJECT_KEY, and ISSUE_TYPE_NAME.")
    exit()

# --- LLM Configuration ---
# Set the device
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Update this path to your downloaded LLM (e.g., Zephyr or Mistral)
# Make sure the model is compatible with AutoModelForCausalLM and AutoTokenizer
LLM_MODEL_PATH = 'F:/PythonProjects/DXGPT/zephyr_local_model' # Default LLM path

# --- API Endpoint ---
# This is the standard endpoint for creating issues in JIRA Cloud REST API v3
CREATE_ISSUE_URL = f"{JIRA_URL}/rest/api/3/issue"

# --- Authentication ---
# Using Basic Authentication with email and API token
JIRA_AUTH = (JIRA_EMAIL, JIRA_API_TOKEN)

# --- Request Headers ---
JIRA_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# ===== LOAD LLM COMPONENTS =====
def load_llm_components(model_path):
    """Loads the LLM tokenizer and model."""
    try:
        print(f"Loading LLM tokenizer from {model_path}...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            print(f"LLM Tokenizer pad token set to EOS token: {tokenizer.pad_token}")

        print(f"Loading LLM model from {model_path}...")
        # Use torch_dtype=torch.float16 to save memory if needed
        model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16 if torch.cuda.is_available() else None).to(DEVICE)
        print("LLM Model loaded successfully.")

        return tokenizer, model
    except Exception as e:
        raise Exception(f"Failed to load LLM components from {model_path}: {str(e)}")

# ===== USE LLM TO PARSE USER REQUEST =====
def parse_jira_request(message, tokenizer, model):
    """
    Analyzes the user message using the LLM to extract JIRA ticket details.
    Predicts intent, summary, description, and acceptance criteria.
    """
    system_prompt = (
        "You are an intelligent assistant that helps create JIRA tickets. "
        "Given a user request, extract the key information and predict the following as JSON:\n"
        "- intent: one of ['create_jira', 'exit', 'unknown']\n"
        "- summary: (the title of the JIRA ticket - REQUIRED)\n"
        "- description: (the detailed description for the JIRA ticket, can be multi-line - REQUIRED)\n"
        "- acceptance_criteria: (the acceptance criteria for the JIRA ticket, can be multi-line - REQUIRED)\n"
        "Respond ONLY as valid JSON without extra text."
    )

    input_text = f"{system_prompt}\nUser Request: {message}\n"
    inputs = tokenizer(input_text, return_tensors="pt", padding=True, truncation=True)
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=300, # Increased max_new_tokens to accommodate Acceptance Criteria
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(output[0], skip_special_tokens=True)
    print(f"DEBUG: LLM raw response: {response}") # Debugging line to see LLM output

    # --- JSON extraction and flexible parsing ---
    json_matches = re.findall(r'\{.*?\}', response, re.DOTALL)
    # Default parsed output structure for JIRA creation, including acceptance_criteria
    parsed = {'intent': 'unknown', 'summary': None, 'description': None, 'acceptance_criteria': None}

    for json_str in json_matches:
        try:
            temp_parsed = json.loads(json_str)
            # Update the parsed dictionary with found keys relevant to JIRA creation
            parsed.update({k: v for k, v in temp_parsed.items() if k in parsed})

            # If a valid intent is found, potentially stop
            if parsed.get('intent') in ['create_jira', 'exit', 'unknown']:
                 break

        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"DEBUG: Error parsing potential JSON: {e} in string: {json_str}")
            continue

    # Basic validation and cleanup of parsed output
    valid_intents = ['create_jira', 'exit', 'unknown']
    if parsed.get('intent') not in valid_intents:
        parsed['intent'] = 'unknown'

    # Ensure summary, description, and acceptance_criteria are strings or None
    parsed['summary'] = str(parsed.get('summary')).strip() if parsed.get('summary') is not None else None
    parsed['description'] = str(parsed.get('description')).strip() if parsed.get('description') is not None else None
    parsed['acceptance_criteria'] = str(parsed.get('acceptance_criteria')).strip() if parsed.get('acceptance_criteria') is not None else None


    print(f"DEBUG: Parsed request: {parsed}") # Debugging line to see parsed output

    return parsed

# ===== CREATE JIRA TICKET =====
def create_jira_ticket(summary, description, acceptance_criteria):
    """Creates a JIRA ticket using the API with summary, description, and acceptance criteria."""
    # Validation for mandatory fields is done in the main loop before calling this function

    # --- Request Body (JSON Payload) ---
    payload_fields = {
        "project": {
            "key": PROJECT_KEY
        },
        "summary": summary,
        "issuetype": {
            "name": ISSUE_TYPE_NAME
        },
        # Description field using Atlassian Document Format (ADF)
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": description
                        }
                    ]
                }
            ]
        },
        # Acceptance Criteria field - NOTE: You will need to confirm the exact
        # custom field ID or name and its structure in your JIRA instance.
        # This is a placeholder using a generic custom field ID and ADF format.
        # Replace 'customfield_NNNNN' with the actual field ID for Acceptance Criteria.
        # If it's a standard text field, the structure might be simpler.
        'Acceptance criteria': { # !!! REPLACE 'customfield_NNNNN' with your Acceptance Criteria field ID !!!
             "type": "doc",
             "version": 1,
             "content": [
                 {
                     "type": "paragraph",
                     "content": [
                         {
                             "type": "text",
                             "text": acceptance_criteria
                         }
                     ]
                 }
             ]
         }
         # If Acceptance Criteria is a plain text field, the payload might be:
         # 'customfield_NNNNN': acceptance_criteria

    }

    payload = json.dumps({"fields": payload_fields})

    # --- Make the API Request ---
    print(f"\nAttempting to create JIRA ticket in project '{PROJECT_KEY}' with summary: '{summary}'...")
    try:
        response = requests.post(
            CREATE_ISSUE_URL,
            data=payload,
            headers=JIRA_HEADERS,
            auth=JIRA_AUTH
        )

        response.raise_for_status() # Raise an exception for bad status codes

        response_json = response.json()

        ticket_key = response_json.get('key')
        ticket_url = f"{JIRA_URL}/browse/{ticket_key}" if ticket_key else "N/A"

        print("JIRA ticket created successfully!")
        print(f"Ticket Key: {ticket_key}")
        print(f"Ticket URL: {ticket_url}")

        return ticket_key, ticket_url

    except requests.exceptions.RequestException as e:
        print(f"Error creating JIRA ticket: {e}")
        error_message = str(e)
        if response is not None and response.text:
            try:
                error_json = response.json()
                if 'errorMessages' in error_json:
                     error_message = "; ".join(error_json['errorMessages'])
                elif 'errors' in error_json:
                     error_message = json.dumps(error_json['errors'])
                else:
                     error_message = response.text
            except json.JSONDecodeError:
                error_message = response.text
        return None, f"Error creating JIRA ticket: {error_message}"
    except Exception as e:
        print(f"An unexpected error occurred during ticket creation: {e}")
        return None, f"An unexpected error occurred: {str(e)}"


# ===== MAIN INTERACTIVE BOT =====
if __name__ == "__main__":
    # Load LLM components
    try:
        llm_tokenizer, llm_model = load_llm_components(LLM_MODEL_PATH)
    except Exception as e:
        print(f"Fatal Error: {e}")
        exit()

    print("\n--- Interactive JIRA Ticket Creation Bot (LLM Powered) ---")
    print("Describe the JIRA ticket you want to create, including Summary, Description, and Acceptance Criteria (type 'exit' to quit).")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            print("Bot: Goodbye! 👋")
            break

        if not user_input:
            print("Bot: Please enter a request to create a JIRA ticket.")
            continue

        start_time = time.time()

        # Use LLM to parse the user's request
        parsed_request = parse_jira_request(user_input, llm_tokenizer, llm_model)

        intent = parsed_request.get('intent')
        summary = parsed_request.get('summary')
        description = parsed_request.get('description')
        acceptance_criteria = parsed_request.get('acceptance_criteria') # Get acceptance criteria

        if intent == 'create_jira':
            # --- Validate mandatory fields ---
            if not summary:
                print("Bot: I understood you want to create a JIRA ticket, but I couldn't extract the Summary. Please provide a clear summary.")
            elif not description:
                 print("Bot: I understood you want to create a JIRA ticket, but I couldn't extract the Description. Please provide a detailed description.")
            elif not acceptance_criteria:
                 print("Bot: I understood you want to create a JIRA ticket, but I couldn't extract the Acceptance Criteria. Please provide the acceptance criteria.")
            # --- End validation ---
            else:
                print("Bot: Okay, I will try to create a JIRA ticket.")
                # Create the JIRA ticket with all mandatory fields
                ticket_key, result_message = create_jira_ticket(summary, description, acceptance_criteria)

                if ticket_key:
                    print(f"Bot: Ticket created successfully! Key: {ticket_key}, URL: {result_message}")
                else:
                    print(f"Bot: Failed to create ticket. {result_message}")
        elif intent == 'unknown':
            print("Bot: I couldn't understand your request to create a JIRA ticket. Please describe the ticket you want to create, including Summary, Description, and Acceptance Criteria.")
        # Add handling for other potential intents if needed later

        elapsed = time.time() - start_time
        print(f"(Response time: {elapsed:.2f} seconds)\n")