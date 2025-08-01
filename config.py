# config.py

class JiraConfig:
    """
    Configuration class for Jira API credentials.
    Credentials are hardcoded directly into this file.

    *** SECURITY WARNING ***
    Hardcoding sensitive credentials is NOT recommended for production environments.
    For better security, consider using environment variables, a secrets manager,
    or a configuration file that is not committed to version control.
    """
    # --- REPLACE THESE PLACEHOLDER VALUES WITH YOUR ACTUAL JIRA CREDENTIALS ---
    JIRA_URL = "https://madhusudaniyer.atlassian.net"  # e.g., "https://mycompany.atlassian.net"
    JIRA_USERNAME = "madhusudaniyer@msn.com"      # Your Jira email for Cloud, or username for Server
    JIRA_API_TOKEN = "ATATT3xFfGF0YntCF2RKInL9A9dDXfny_13zLJFVl63jt9hsn0fSpn5D-fMSLKz71PZN-rzjQ-JQ2VJ6nfnmDNJJejWJ9b2IwF-75LQYo9x1xEOmRK2CK5n9z_yMy2z59ZgtUNq7FiwZeTF2adbOVt9XlkLy9xC4O5-vfzpAeDC0aH_V2ChtnAM=8A988FB2"        # Your generated Jira API token
    # -------------------------------------------------------------------------

    @classmethod
    def validate(cls):
        """
        Checks if the hardcoded Jira configuration variables are present (not empty strings).
        Raises a ValueError if any are missing.
        """
        if not all([cls.JIRA_URL, cls.JIRA_USERNAME, cls.JIRA_API_TOKEN]):
            raise ValueError(
                "Jira configuration is incomplete. Please ensure JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN "
                "are set directly in the 'config.py' file."
            )
        print("Jira configuration loaded successfully.")

if __name__ == '__main__':
    # This block allows you to test if your hardcoded credentials are set up correctly
    # by running `python config.py`
    try:
        JiraConfig.validate()
        print(f"Jira URL: {JiraConfig.JIRA_URL}")
        print(f"Jira Username: {JiraConfig.JIRA_USERNAME}")
        print("Jira API Token: ********* (hidden for security)")
    except ValueError as e:
        print(f"Configuration Error: {e}")