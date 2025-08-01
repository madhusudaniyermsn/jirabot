from jira import JIRA
from jira.exceptions import JIRAError # Import JiraError for specific exception handling
from config import JiraConfig # Import the configuration

class JiraService:
    """
    Handles all interactions with the Jira API.
    Encapsulates creation, modification, and transition of issues.
    """
    def __init__(self):
        """
        Initializes the JiraService by loading configuration and connecting to Jira.
        """
        JiraConfig.validate() # Validate configuration before attempting connection
        self.jira_client = None # Initialize client to None
        try:
            # Corrected: Pass server URL directly to the 'server' parameter
            self.jira_client = JIRA(server=JiraConfig.JIRA_URL, basic_auth=(JiraConfig.JIRA_USERNAME, JiraConfig.JIRA_API_TOKEN))
            print("Connected to Jira successfully.")
        except JiraError as e: # Catch specific JiraError for connection issues
            # Catch any exceptions during connection and print an informative error
            print(f"Failed to connect to Jira: {e}")
            print("Please check your JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN in the config.py file.")
        except Exception as e: # Catch any other unexpected exceptions
            print(f"An unexpected error occurred during Jira connection: {e}")
            print("Please check your network connection or Jira server status.")


    def _is_connected(self) -> bool:
        """
        Helper method to check if the Jira client was successfully initialized.
        This method is intended for internal use within the JiraService class.
        :return: True if connected, False otherwise.
        """
        if not self.jira_client:
            print("Error: Not connected to Jira. Please ensure a successful connection before making API calls.")
            return False
        return True

    def create_issue(self, project_key: str, summary: str, description: str = "", issue_type: str = "Story"):
        """
        Creates a new Jira issue with the specified details.
        :param project_key: The key of the Jira project (e.g., "MYPROJ").
        :param summary: The summary (title) of the new issue.
        :param description: A detailed description for the issue. Defaults to an empty string.
        :param issue_type: The type of issue (e.g., "Story", "Task", "Bug", "Defect"). Defaults to "Story".
        :return: The created Jira issue object if successful, None otherwise.
        """
        if not self._is_connected():
            return None

        issue_dict = {
            'project': {'key': project_key},
            'summary': summary,
            'description': description,
            'issuetype': {'name': issue_type},
        }
        try:
            new_issue = self.jira_client.create_issue(fields=issue_dict)
            print(f"Successfully created issue: {new_issue.key} - '{new_issue.fields.summary}'")
            return new_issue
        except JiraError as e: # Specific exception for Jira API errors
            print(f"Jira API Error creating issue in project '{project_key}': {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred while creating issue: {e}")
            return None

    def get_issue(self, issue_key: str):
        """
        Retrieves a Jira issue by its unique key.
        :param issue_key: The key of the issue to retrieve (e.g., "MYPROJ-123").
        :return: The Jira issue object if found, None otherwise.
        """
        if not self._is_connected():
            return None
        try:
            issue = self.jira_client.issue(issue_key)
            return issue
        except JiraError as e:
            # This error is often for "Issue Does Not Exist", so we'll handle it quietly
            # and let the calling function decide how to report "not found".
            # print(f"Jira API Error getting issue '{issue_key}': {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred while getting issue '{issue_key}': {e}")
            return None

    def update_issue(self, issue_key: str, **kwargs):
        """
        Updates specific fields of an existing Jira issue.
        :param issue_key: The key of the issue to update.
        :param kwargs: Keyword arguments representing the fields to update.
                       Supported fields: 'summary', 'description'.
                       For assignee, pass 'assignee': 'username' (Jira will try to resolve).
        :return: True if the update was successful, False otherwise.
        """
        if not self._is_connected():
            return False

        issue = self.get_issue(issue_key)
        if not issue:
            print(f"Issue '{issue_key}' not found or inaccessible for update.")
            return False

        fields_to_update = {}
        if 'summary' in kwargs and kwargs['summary']:
            fields_to_update['summary'] = kwargs['summary']
        if 'description' in kwargs and kwargs['description']:
            fields_to_update['description'] = kwargs['description']
        if 'assignee' in kwargs and kwargs['assignee']:
            # Note: Assignee can be tricky. Jira's API often prefers accountId.
            # This attempts to assign by name, which might require exact matching or user lookup.
            fields_to_update['assignee'] = {'name': kwargs['assignee']}

        if not fields_to_update:
            print(f"No valid fields provided to update for issue '{issue_key}'.")
            return False

        try:
            issue.update(fields=fields_to_update)
            print(f"Successfully updated issue: {issue_key}")
            return True
        except JiraError as e: # Specific exception for Jira API errors
            print(f"Jira API Error updating issue '{issue_key}': {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred while updating issue: {e}")
            return False

    def transition_issue(self, issue_key: str, transition_name: str):
        """
        Transitions a Jira issue to a new status based on a transition name.
        :param issue_key: The key of the issue to transition.
        :param transition_name: The name of the desired transition (e.g., "Done", "Resolved", "Closed", "Abandoned").
                                This must match a valid transition in your Jira workflow.
        :return: True if the transition was successful, False otherwise.
        """
        if not self._is_connected():
            return None

        issue = self.get_issue(issue_key)
        if not issue:
            print(f"Issue '{issue_key}' not found or inaccessible for transition.")
            return False

        transitions = self.jira_client.transitions(issue)
        transition_id = None
        # Find the ID of the desired transition by matching its name (case-insensitive)
        for t in transitions:
            if t['name'].lower() == transition_name.lower():
                transition_id = t['id']
                break

        if transition_id:
            try:
                self.jira_client.transition_issue(issue, transition_id)
                print(f"Successfully transitioned issue '{issue_key}' to '{transition_name}'.")
                return True
            except JiraError as e: # Specific exception for Jira API errors
                print(f"Jira API Error transitioning issue '{issue_key}' to '{transition_name}': {e}")
                return False
            except Exception as e:
                print(f"An unexpected error occurred while transitioning issue: {e}")
                return False
        else:
            valid_transitions = [t['name'] for t in transitions]
            print(f"No valid transition named '{transition_name}' found for issue '{issue_key}'.")
            if valid_transitions:
                print(f"Available transitions for '{issue_key}': {', '.join(valid_transitions)}")
            else:
                print("No transitions available for this issue (check Jira workflow permissions).")
            return False

if __name__ == '__main__':
    # This block provides a way to test the JiraService independently.
    # Uncomment and replace placeholders with your actual Jira project key and issue keys.
    jira_service = JiraService()
    # Corrected: Check if jira_client is initialized directly to avoid protected member warning
    if jira_service.jira_client: # Check if the client object exists
        print("\nJiraService is connected. You can uncomment the lines below to test operations.")

        # Example: Create a test issue (replace "YOUR_PROJECT_KEY" with an actual project key)
        # new_issue = jira_service.create_issue("YOUR_PROJECT_KEY", "Test Issue from Script", "This is a test description.", "Task")
        # if new_issue:
        #     print(f"Created test issue: {new_issue.key}")

        #     # Example: Update the test issue
        #     # jira_service.update_issue(new_issue.key, summary="Updated Test Summary", description="New detailed description.")

        #     # Example: Transition the test issue
        #     # You MUST replace "YourTransitionName" with a valid transition name for your workflow (e.g., "Done", "Resolved", "Closed")
        #     # jira_service.transition_issue(new_issue.key, "YourTransitionName")
        #     pass
        # else:
        #     print("Could not create test issue (check project key and permissions).")

        # Example: Try to transition a known issue (replace "EXISTING-123" with an actual issue key from your Jira)
        # jira_service.transition_issue("EXISTING-123", "Closed") # Ensure "Closed" is a valid transition for EXISTING-123
        pass
