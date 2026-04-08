#!/usr/bin/env python3
"""
List Granola Document Lists (Folders)

This script fetches and displays all document lists (folders) from your Granola account.
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


def fetch_document_lists(token):
    """
    Fetch document lists (folders) from Granola API

    Args:
        token: Access token

    Returns:
        dict: Document lists data or None if failed
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "User-Agent": "Granola/5.354.0",
        "X-Client-Version": "5.354.0"
    }

    # Try v2 endpoint first, then v1
    endpoints = [
        "https://api.granola.ai/v2/get-document-lists",
        "https://api.granola.ai/v1/get-document-lists"
    ]

    last_error = None
    for url in endpoints:
        try:
            logger.info(f"Trying endpoint: {url}")
            response = requests.post(url, headers=headers, json={})
            response.raise_for_status()
            logger.info(f"Successfully fetched document lists from {url}")
            return response.json()
        except requests.exceptions.HTTPError as e:
            last_error = e
            if e.response.status_code == 404:
                logger.info(f"Endpoint {url} not found (404), trying next...")
                continue
            else:
                logger.warning(f"HTTP error from {url}: {str(e)}, trying next...")
                continue
        except Exception as e:
            last_error = e
            logger.warning(f"Error from {url}: {str(e)}, trying next...")
            continue

    logger.error(f"All document list endpoints failed. Last error: {last_error}")
    return None


def main():
    """Main function to list document lists (folders)"""
    print("=" * 80)
    print("Granola Document Lists (Folders)")
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

    # Fetch document lists
    logger.info("Fetching document lists...")
    lists_response = fetch_document_lists(access_token)

    if not lists_response:
        logger.error("Failed to fetch document lists")
        return

    # Save to file
    output_file = Path('document_lists.json')
    with open(output_file, 'w') as f:
        json.dump(lists_response, f, indent=2)
    logger.info(f"Document lists data saved to {output_file}")
    print()

    # Display document lists
    print("Document Lists (Folders) found:")
    print("-" * 80)

    lists = []
    if isinstance(lists_response, list):
        lists = lists_response
    elif isinstance(lists_response, dict):
        if "lists" in lists_response:
            lists = lists_response["lists"]
        elif "document_lists" in lists_response:
            lists = lists_response["document_lists"]
        else:
            # If the response is a dict but not with expected keys,
            # treat the whole response as a single list
            lists = [lists_response]

    if not lists:
        print("No document lists found or unexpected response format.")
        print(f"Response structure: {json.dumps(lists_response, indent=2)}")
        return

    for i, doc_list in enumerate(lists, 1):
        list_id = doc_list.get("id", "N/A")
        list_name = doc_list.get("name") or doc_list.get("title", "Unnamed List")
        created_at = doc_list.get("created_at", "N/A")
        workspace_id = doc_list.get("workspace_id", "N/A")

        # Count documents in list
        documents = doc_list.get("documents", [])
        if not documents:
            documents = doc_list.get("document_ids", [])
        doc_count = len(documents) if isinstance(documents, list) else 0

        print(f"\n{i}. {list_name}")
        print(f"   ID: {list_id}")
        print(f"   Documents: {doc_count}")
        print(f"   Workspace ID: {workspace_id}")
        print(f"   Created: {created_at}")

        # Display any other interesting fields
        if "description" in doc_list:
            desc = doc_list.get('description')
            if desc:
                # Truncate long descriptions
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                print(f"   Description: {desc}")
        if "owner_id" in doc_list:
            print(f"   Owner ID: {doc_list.get('owner_id')}")
        if "is_favourite" in doc_list:
            print(f"   Favourite: {doc_list.get('is_favourite')}")

        # Show first few documents if available
        if doc_count > 0:
            # Extract document IDs (handle both dict and string formats)
            doc_ids = []
            for doc in documents[:5]:
                if isinstance(doc, dict):
                    doc_ids.append(doc.get('id', doc.get('document_id', 'unknown')))
                else:
                    doc_ids.append(str(doc))

            if doc_count <= 5:
                print(f"   Document IDs: {', '.join(doc_ids)}")
            else:
                print(f"   First 5 Document IDs: {', '.join(doc_ids)}...")

    print()
    print("=" * 80)
    print(f"Total document lists: {len(lists)}")
    print(f"Full data saved to: {output_file}")


if __name__ == "__main__":
    main()
