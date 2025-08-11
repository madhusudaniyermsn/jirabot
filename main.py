from jira_service import JiraService
from nlu_processor import NLUProcessor
import sys

def main():
    """
    Main entry point for the Jira NLP automation tool.
    Initializes the JiraService and NLUProcessor, then enters a command loop
    to process user instructions.
    """
    # Initialize the Jira service client
    jira_service = JiraService()
    # Initialize the Natural Language Understanding processor
    nlu_processor = NLUProcessor()

    # Exit if Jira connection failed or NLU model couldn't be loaded
    if not jira_service._is_connected():
        print("Exiting due to Jira connection failure. Please check your config.py configuration.")
        sys.exit(1)

    if not nlu_processor.nlp:
        print("Exiting due to NLU model loading failure. Please run 'python -m spacy download en_core_web_sm'")
        sys.exit(1)

    print("\n--- Jira NLP Automation Tool ---")
    print("Enter commands to interact with Jira (e.g., 'create a story...', 'close MYPROJ-123').")
    print("Type 'exit' or 'quit' to stop.")

    # Main command processing loop
    while True:
        try:
            command = input("\nEnter command: ").strip()

            # Check for exit commands
            if command.lower() in ["exit", "quit"]:
                print("Exiting Jira NLP Automation. Goodbye!")
                break

            # Process the natural language command
            parsed_data = nlu_processor.process_command(command)
            intent = parsed_data.get("intent")
            entities = parsed_data.get("entities", {})

            # --- Handle 'create' intent ---
            if intent == "create":
                project_key = entities.get("project_key")
                summary = entities.get("summary")
                issue_type = entities.get("issue_type", "Story") # Default to Story if not specified
                description = entities.get("description", "") # Get description from parsed data

                if project_key and summary:
                    print(f"Attempting to create {issue_type} '{summary}' in project '{project_key}'...")
                    jira_service.create_issue(
                        project_key,
                        summary,
                        description, # Pass only the description text
                        issue_type
                    )
                else:
                    print("Error: For 'create' command, please specify both a 'project' and a 'summary'.")
                    print("Example: `create a story called 'Setup CI/CD' in project DEVOPS`")

            # --- Handle 'transition' intent ---
            elif intent == "transition":
                issue_key = entities.get("issue_key")
                transition_name = entities.get("transition_name")
                if issue_key and transition_name:
                    print(f"Attempting to transition issue '{issue_key}' to '{transition_name}'...")
                    jira_service.transition_issue(issue_key, transition_name)
                else:
                    print("Error: For 'transition' command, please specify an 'issue key' and a 'transition name'.")
                    print("Example: `close MYPROJ-123` or `resolve PROJ-456`")

            # --- Handle 'assign' intent ---
            elif intent == "assign":
                issue_key = entities.get("issue_key")
                assignee = entities.get("assignee")
                if issue_key and assignee:
                    print(f"Attempting to assign issue '{issue_key}' to '{assignee}'...")
                    jira_service.update_issue(issue_key, assignee=assignee)
                else:
                    print("Error: For 'assign' command, please specify an 'issue key' and an 'assignee'.")
                    print("Example: `assign AIK-1 to John Doe` or `unassign AIK-2`")

            # --- Handle 'comment' intent ---
            elif intent == "comment":
                issue_key = entities.get("issue_key")
                comment_body = entities.get("comment_body")
                if issue_key and comment_body:
                    print(f"Attempting to add comment to issue '{issue_key}'...")
                    jira_service.add_comment(issue_key, comment_body)
                else:
                    print("Error: For 'comment' command, please specify an 'issue key' and a 'comment body'.")
                    print("Example: `add comment 'This is important' to AIK-1`")


            # --- Handle 'modify' intent (general updates) ---
            elif intent == "modify":
                issue_key = entities.get("issue_key")
                field = entities.get("field")
                new_value = entities.get("new_value")
                if issue_key and field and new_value:
                    print(f"Attempting to modify issue '{issue_key}' {field} to '{new_value}'...")
                    # Call update_issue with the appropriate keyword argument based on the field
                    if field == "summary":
                        jira_service.update_issue(issue_key, summary=new_value)
                    elif field == "description":
                        jira_service.update_issue(issue_key, description=new_value)
                    else:
                        print(f"Modification for field '{field}' is not yet supported.")
                        print("Currently supported fields for modification: 'summary', 'description'.")
                else:
                    print("Error: For 'modify' command, please specify 'issue key', 'field (summary/description)', and 'new value'.")
                    print("Example: `modify MYPROJ-123 summary to 'New Title'`")

            # --- Handle unclear intents (specific feedback) ---
            elif intent == "unclear_create":
                print("Error: I understood you want to create an issue, but the command is incomplete.")
                print("Please provide a summary and project key. Example: `create a story 'Build UI' in PROJ`")

            elif intent == "unclear_transition":
                print("Error: I understood you want to transition an issue, but the command is incomplete.")
                print("Please provide an issue key. Example: `close MYPROJ-123`")

            elif intent == "unclear_modify":
                print("Error: I understood you want to modify an issue, but the command is incomplete or unclear.")
                print("Please provide an issue key and what to modify (e.g., summary, description) with its new value.")
                print("Example: `modify MYPROJ-123 summary to 'New Title'`")

            elif intent == "unclear_assign":
                print("Error: I understood you want to assign an issue, but the command is incomplete or unclear.")
                print("Please provide an issue key and an assignee name. Example: `assign AIK-1 to John Doe`")

            elif intent == "unclear_comment":
                print("Error: I understood you want to add a comment, but the command is incomplete or unclear.")
                print("Please provide an issue key and the comment text. Example: `add comment 'This is a note' to AIK-1`")

            # --- Handle completely unknown commands ---
            else:
                print(f"Sorry, I didn't understand the command: '{command}'.")
                print("Please try a command like 'create a story...', 'close MYPROJ-123', 'assign AIK-1 to John', or 'add comment 'Hello' to AIK-2'.")

        except Exception as e:
            # Catch any unexpected errors during command processing
            print(f"An unexpected error occurred: {e}")
            print("Please try your command again or type 'exit' to quit.")

if __name__ == "__main__":
    main()
