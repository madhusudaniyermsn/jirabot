import spacy
import re


class NLUProcessor:
    """
    Processes natural language commands to extract intent and entities.
    Uses spaCy for basic NLP tasks and regular expressions for specific pattern matching.
    """

    def __init__(self):
        """
        Initializes the NLUProcessor by loading the spaCy English language model.
        """
        self.nlp = None
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("spaCy model 'en_core_web_sm' loaded successfully.")
        except OSError:
            print("spaCy model 'en_core_web_sm' not found.")
            print("Please run 'python -m spacy download en_core_web_sm' in your terminal.")
            print("NLU capabilities will be limited without the model.")

    def process_command(self, command_text: str) -> dict:
        """
        Analyzes the input command text to determine the user's intent
        (e.g., create, transition, modify) and extracts relevant entities
        (e.g., issue type, summary, project key, issue key, new values).

        :param command_text: The raw natural language command string from the user.
        :return: A dictionary containing 'intent' and 'entities' extracted.
                 Returns {"intent": "error"} if the spaCy model is not loaded.
        """
        if not self.nlp:
            return {"intent": "error", "message": "NLU model not loaded. Cannot process command."}

        # Process the command text using spaCy for linguistic features
        doc = self.nlp(command_text.lower())
        parsed_data = {"intent": "unknown", "entities": {}}

        # --- Intent: Create Issue ---
        # Examples:
        # "create a story called 'Implement login' in project MYPROJ"
        # "new task 'Refactor code' for PROJ"
        # "create defect 'Button click not working' in QA"
        if ("create" in doc.text or "new" in doc.text) and \
                any(t in doc.text for t in ["story", "task", "defect", "bug"]):
            parsed_data["intent"] = "create"

            # Extract issue type (story, task, defect, bug)
            for issue_type in ["story", "task", "defect", "bug"]:
                if issue_type in doc.text:
                    parsed_data["entities"]["issue_type"] = issue_type.capitalize()
                    break
            else:
                parsed_data["entities"]["issue_type"] = "Story"  # Default to Story if not explicitly mentioned

            # --- NEW & IMPROVED LOGIC FOR SUMMARY/DESCRIPTION/PROJECT KEY EXTRACTION ---

            # Step 1: Extract description first, as it's a very specific pattern.
            description_match = re.search(r"(?:with|and)\s+(?:description)\s*['\"](.+?)['\"]", command_text,
                                          re.IGNORECASE)
            if description_match:
                parsed_data["entities"]["description"] = description_match.group(1).strip()
                # Remove the description part from the command string to simplify summary extraction
                command_text = re.sub(r"(?:with|and)\s+(?:description)\s*['\"](.+?)['\"]", "", command_text,
                                      flags=re.IGNORECASE)

            # Step 2: Extract project key, which should be at the end.
            project_match = re.search(r"(?:in|for|on)\s*(?:project)?\s*(\b[A-Z]{2,10}\b)$", command_text, re.IGNORECASE)
            if project_match:
                parsed_data["entities"]["project_key"] = project_match.group(1).upper()
                # Remove the project key part from the command string
                command_text = re.sub(r"(?:in|for|on)\s*(?:project)?\s*(\b[A-Z]{2,10}\b)$", "", command_text,
                                      flags=re.IGNORECASE)

            # Step 3: Extract the summary from the remaining, cleaner command string.
            summary_match = re.search(r"(?:called|titled|for|summary)?\s*['\"](.+?)['\"]", command_text, re.IGNORECASE)
            if summary_match:
                parsed_data["entities"]["summary"] = summary_match.group(1).strip()
            else:
                # Fallback extraction for summaries without quotes
                type_keywords = "|".join(["story", "task", "defect", "bug"])
                fallback_summary_pattern = rf"(?:create|new)\s*(?:a|an)?\s*(?:{type_keywords})\s*(.+?)$"
                fallback_summary_match = re.search(fallback_summary_pattern, command_text, re.IGNORECASE)
                if fallback_summary_match and fallback_summary_match.group(1):
                    parsed_data["entities"]["summary"] = fallback_summary_match.group(1).strip()

            # If summary is still missing, set a specific unclear intent
            if not parsed_data["entities"].get("summary"):
                parsed_data["intent"] = "unclear_create"

        # --- Intent: Transition Issue (Close, Resolve, Abandon) ---
        # Examples:
        # "close MYPROJ-123"
        # "resolve issue PROJ-456"
        # "abandon this task TEST-789"
        # "transition WEBAPP-100 to Done"
        elif any(t in doc.text for t in ["close", "resolve", "abandon", "transition"]):
            parsed_data["intent"] = "transition"

            # Extract issue key first, as it's a distinct entity
            issue_key_match = re.search(r"(\b[A-Z]{1,10}-\d+\b)", command_text, re.IGNORECASE)
            if issue_key_match:
                parsed_data["entities"]["issue_key"] = issue_key_match.group(1).upper()

            # Determine transition name
            if "close" in doc.text:
                parsed_data["entities"]["transition_name"] = "Closed"
            elif "resolve" in doc.text:
                parsed_data["entities"]["transition_name"] = "Resolved"
            elif "abandon" in doc.text:
                parsed_data["entities"]["transition_name"] = "Abandoned"
            elif "transition" in doc.text and "to" in doc.text:
                # UPDATED LOGIC: Extract text after "to" for the transition name more reliably
                parts = command_text.lower().split("to", 1)  # Split only on the first 'to'
                if len(parts) > 1:
                    transition_phrase = parts[1].strip()
                    # Remove the issue key from the transition phrase if it was found at the end
                    if parsed_data["entities"].get("issue_key"):
                        transition_phrase = transition_phrase.replace(parsed_data["entities"]["issue_key"].lower(),
                                                                      "").strip()

                    # Clean up any remaining "issue" or other noise that might be part of the command structure
                    transition_phrase = re.sub(r"\bissue\b", "", transition_phrase).strip()

                    parsed_data["entities"][
                        "transition_name"] = transition_phrase.title()  # Capitalize each word (e.g., "in progress" -> "In Progress")
                else:
                    parsed_data["entities"]["transition_name"] = "Unknown"  # Fallback if status isn't clear

            if not parsed_data["entities"].get("issue_key"):
                parsed_data["intent"] = "unclear_transition"
            elif not parsed_data["entities"].get("transition_name"):  # Also unclear if transition name is missing
                parsed_data["intent"] = "unclear_transition"


        # --- Intent: Modify Issue ---
        # Examples:
        # "modify MYPROJ-123 summary to 'New Title'"
        # "update PROJ-456 description to 'Some new details'"
        elif any(t in doc.text for t in ["modify", "update"]):
            parsed_data["intent"] = "modify"

            # Extract issue key
            issue_key_match = re.search(r"(\b[A-Z]{1,10}-\d+\b)", command_text, re.IGNORECASE)
            if issue_key_match:
                parsed_data["entities"]["issue_key"] = issue_key_match.group(1).upper()

            # Extract what field to modify (summary, description) and its new value
            summary_to_match = re.search(r"(?:summary|title)\s*(?:to|as)\s*['\"](.+?)['\"]", command_text,
                                         re.IGNORECASE)
            if summary_to_match:
                parsed_data["entities"]["field"] = "summary"
                parsed_data["entities"]["new_value"] = summary_to_match.group(1).strip()
            else:
                desc_to_match = re.search(r"(?:description)\s*(?:to|as)\s*['\"](.+?)['\"]", command_text, re.IGNORECASE)
                if desc_to_match:
                    parsed_data["entities"]["field"] = "description"
                    parsed_data["entities"]["new_value"] = desc_to_match.group(1).strip()
                # Add more fields here as needed (e.g., assignee, priority)

            # If issue key or field/value is missing, set a specific unclear intent
            if not parsed_data["entities"].get("issue_key") or not parsed_data["entities"].get("field"):
                parsed_data["intent"] = "unclear_modify"

        return parsed_data


if __name__ == '__main__':
    # This block allows you to test the NLUProcessor independently.
    nlu = NLUProcessor()
    if nlu.nlp:  # Only run tests if spaCy model loaded successfully
        test_commands = [
            "create a story called 'Implement authentication flow' in project WEBAPP",
            "new task 'Database Migration' for DEV",
            "create defect 'Login button not responsive' in QA",
            "close WEBAPP-789",
            "resolve DEV-123",
            "abandon QA-456",
            "modify WEBAPP-789 summary to 'User Authentication Workflow'",
            "update DEV-123 description to 'New migration script details'",
            "transition QA-456 to In Progress",  # Test case for multi-word transition
            "transition AIK-1 to Done",  # Test case for multi-word transition
            "create task 'Design UI in AJAX' in AIK",  # Test case for a project key issue
            "create task 'Design UI in JS' in AIK",  # Test case for a project key issue
            "what is the status of WEBAPP-100",  # Expected: Unknown intent
            "create a story in project ABC",  # Expected: Unclear create (missing summary)
            "close issue",  # Expected: Unclear transition (missing issue key)
            "modify MYPROJ-123 to 'New Value'",  # Expected: Unclear modify (missing field)
            "create a bug 'Payment gateway error' in PROJ",
            "create a task Implement UI for PROJ",  # Test without "called"
            "update TEST-101 description as 'Fixed the bug'",
            "create a story 'User profile' in project MYPROJ with description 'Add a user profile page with editable fields.'",
            "create story 'NLU TESTING' with description 'test all cases nlu' in AIK",  # The problematic prompt
        ]

        print("\n--- Testing NLU Processor ---")
        for cmd in test_commands:
            print(f"\nCommand: \"{cmd}\"")
            result = nlu.process_command(cmd)
            print(f"Parsed: {result}")
    else:
        print("\nNLU Processor tests skipped because spaCy model could not be loaded.")
