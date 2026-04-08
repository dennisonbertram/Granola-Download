#!/usr/bin/env python3
"""
List Granola Workspaces

This script fetches and displays all workspaces from your Granola account.
"""

import json
import logging
from pathlib import Path
from token_manager import TokenManager
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_workspaces(token):
    """
    Fetch workspaces from Granola API

    Args:
        token: Access token

    Returns:
        dict: Workspaces data or None if failed
    """
    url = "https://api.granola.ai/v1/get-workspaces"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "User-Agent": "Granola/5.354.0",
        "X-Client-Version": "5.354.0"
    }

    try:
        response = requests.post(url, headers=headers, json={})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching workspaces: {str(e)}")
        return None


def main():
    """Main function to list workspaces"""
    print("=" * 80)
    print("Granola Workspaces")
    print("=" * 80)
    print()

    # Check config
    config_path = Path('config.json')
    if not config_path.exists():
        logger.error("config.json not found. Please create it first.")
        return

    # Get access token
    logger.info("Obtaining access token...")
    token_manager = TokenManager()
    access_token = token_manager.get_valid_token()

    if not access_token:
        logger.error("Failed to obtain access token")
        return

    logger.info("Access token obtained successfully")
    print()

    # Fetch workspaces
    logger.info("Fetching workspaces...")
    workspaces_response = fetch_workspaces(access_token)

    if not workspaces_response:
        logger.error("Failed to fetch workspaces")
        return

    # Save to file
    output_file = Path('workspaces.json')
    with open(output_file, 'w') as f:
        json.dump(workspaces_response, f, indent=2)
    logger.info(f"Workspaces data saved to {output_file}")
    print()

    # Display workspaces
    print("Workspaces found:")
    print("-" * 80)

    workspaces = []
    if isinstance(workspaces_response, list):
        workspaces = workspaces_response
    elif isinstance(workspaces_response, dict):
        if "workspaces" in workspaces_response:
            workspaces = workspaces_response["workspaces"]
        else:
            # If the response is a dict but not with a "workspaces" key,
            # treat the whole response as a single workspace
            workspaces = [workspaces_response]

    if not workspaces:
        print("No workspaces found or unexpected response format.")
        print(f"Response structure: {json.dumps(workspaces_response, indent=2)}")
        return

    for i, workspace in enumerate(workspaces, 1):
        workspace_id = workspace.get("id", "N/A")
        workspace_name = workspace.get("name", "Unnamed Workspace")
        created_at = workspace.get("created_at", "N/A")

        print(f"\n{i}. {workspace_name}")
        print(f"   ID: {workspace_id}")
        print(f"   Created: {created_at}")

        # Display any other interesting fields
        if "description" in workspace:
            print(f"   Description: {workspace.get('description')}")
        if "owner_id" in workspace:
            print(f"   Owner ID: {workspace.get('owner_id')}")
        if "members_count" in workspace:
            print(f"   Members: {workspace.get('members_count')}")

    print()
    print("=" * 80)
    print(f"Total workspaces: {len(workspaces)}")
    print(f"Full data saved to: {output_file}")


if __name__ == "__main__":
    main()
