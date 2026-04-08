#!/usr/bin/env python3
"""
Filter Granola Documents by Workspace

This script helps you filter and list documents by workspace/folder.
"""

import json
import argparse
import logging
from pathlib import Path
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_workspaces(output_dir):
    """
    Load workspace information from saved workspaces.json

    Args:
        output_dir: Directory containing workspaces.json

    Returns:
        dict: Workspace ID to name mapping
    """
    workspaces_path = output_dir / "workspaces.json"
    workspace_map = {}

    if not workspaces_path.exists():
        logger.warning(f"No workspaces.json found at {workspaces_path}")
        return workspace_map

    try:
        with open(workspaces_path, 'r') as f:
            workspaces_data = json.load(f)

        # Handle different response formats
        workspaces = []
        if isinstance(workspaces_data, list):
            workspaces = workspaces_data
        elif isinstance(workspaces_data, dict) and "workspaces" in workspaces_data:
            workspaces = workspaces_data["workspaces"]

        for workspace in workspaces:
            workspace_id = workspace.get("id")
            workspace_name = workspace.get("name")
            if workspace_id:
                workspace_map[workspace_id] = workspace_name

    except Exception as e:
        logger.error(f"Error loading workspaces: {e}")

    return workspace_map


def get_all_documents(output_dir):
    """
    Load all document metadata from the output directory

    Args:
        output_dir: Directory containing document folders

    Returns:
        list: List of document metadata dictionaries
    """
    documents = []

    if not output_dir.exists():
        logger.error(f"Output directory {output_dir} does not exist")
        return documents

    for doc_folder in output_dir.iterdir():
        if not doc_folder.is_dir():
            continue

        metadata_path = doc_folder / "metadata.json"
        if not metadata_path.exists():
            continue

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                documents.append(metadata)
        except Exception as e:
            logger.error(f"Error reading {metadata_path}: {e}")

    return documents


def filter_by_workspace(documents, workspace_id):
    """
    Filter documents by workspace ID

    Args:
        documents: List of document metadata
        workspace_id: Workspace ID to filter by

    Returns:
        list: Filtered documents
    """
    return [doc for doc in documents if doc.get("workspace_id") == workspace_id]


def group_by_workspace(documents):
    """
    Group documents by workspace

    Args:
        documents: List of document metadata

    Returns:
        dict: Workspace ID to list of documents mapping
    """
    groups = defaultdict(list)
    for doc in documents:
        workspace_id = doc.get("workspace_id", "unknown")
        groups[workspace_id].append(doc)
    return dict(groups)


def main():
    parser = argparse.ArgumentParser(
        description="Filter and list Granola documents by workspace"
    )
    parser.add_argument(
        "output_dir",
        type=str,
        help="Directory containing saved documents"
    )
    parser.add_argument(
        "--workspace-id",
        type=str,
        help="Filter by specific workspace ID"
    )
    parser.add_argument(
        "--workspace-name",
        type=str,
        help="Filter by workspace name (case-insensitive partial match)"
    )
    parser.add_argument(
        "--list-workspaces",
        action="store_true",
        help="List all workspaces and their document counts"
    )

    args = parser.parse_args()
    output_path = Path(args.output_dir)

    if not output_path.exists():
        logger.error(f"Output directory {output_path} does not exist")
        return

    # Load workspace names
    workspace_map = load_workspaces(output_path)

    # Load all documents
    logger.info(f"Loading documents from {output_path}...")
    documents = get_all_documents(output_path)
    logger.info(f"Loaded {len(documents)} documents")
    print()

    if args.list_workspaces:
        # List all workspaces with document counts
        groups = group_by_workspace(documents)

        print("=" * 80)
        print("Workspaces Summary")
        print("=" * 80)
        print()

        for workspace_id, docs in sorted(groups.items(), key=lambda x: len(x[1]), reverse=True):
            workspace_name = workspace_map.get(workspace_id, "Unknown Workspace")
            print(f"Workspace: {workspace_name}")
            print(f"  ID: {workspace_id}")
            print(f"  Documents: {len(docs)}")
            print()

    elif args.workspace_id:
        # Filter by workspace ID
        filtered = filter_by_workspace(documents, args.workspace_id)
        workspace_name = workspace_map.get(args.workspace_id, "Unknown Workspace")

        print("=" * 80)
        print(f"Documents in Workspace: {workspace_name}")
        print(f"Workspace ID: {args.workspace_id}")
        print("=" * 80)
        print()

        if not filtered:
            print("No documents found in this workspace.")
        else:
            for i, doc in enumerate(filtered, 1):
                print(f"{i}. {doc.get('title', 'Untitled')}")
                print(f"   ID: {doc.get('document_id', 'N/A')}")
                print(f"   Created: {doc.get('created_at', 'N/A')}")
                print(f"   Updated: {doc.get('updated_at', 'N/A')}")
                print()

            print(f"Total: {len(filtered)} documents")

    elif args.workspace_name:
        # Filter by workspace name
        matching_workspace_ids = [
            wid for wid, wname in workspace_map.items()
            if wname and args.workspace_name.lower() in wname.lower()
        ]

        if not matching_workspace_ids:
            print(f"No workspaces found matching '{args.workspace_name}'")
            return

        print(f"Found {len(matching_workspace_ids)} matching workspace(s):")
        print()

        for workspace_id in matching_workspace_ids:
            workspace_name = workspace_map[workspace_id]
            filtered = filter_by_workspace(documents, workspace_id)

            print("=" * 80)
            print(f"Workspace: {workspace_name}")
            print(f"ID: {workspace_id}")
            print("=" * 80)
            print()

            if not filtered:
                print("No documents found in this workspace.")
            else:
                for i, doc in enumerate(filtered, 1):
                    print(f"{i}. {doc.get('title', 'Untitled')}")
                    print(f"   ID: {doc.get('document_id', 'N/A')}")
                    print(f"   Created: {doc.get('created_at', 'N/A')}")
                    print()

                print(f"Total: {len(filtered)} documents")
            print()

    else:
        # No filter - show all documents grouped by workspace
        groups = group_by_workspace(documents)

        print("=" * 80)
        print("All Documents Grouped by Workspace")
        print("=" * 80)
        print()

        for workspace_id, docs in groups.items():
            workspace_name = workspace_map.get(workspace_id, "Unknown Workspace")

            print(f"Workspace: {workspace_name}")
            print(f"ID: {workspace_id}")
            print(f"Documents: {len(docs)}")
            print("-" * 80)

            for i, doc in enumerate(docs[:5], 1):  # Show first 5
                print(f"  {i}. {doc.get('title', 'Untitled')}")

            if len(docs) > 5:
                print(f"  ... and {len(docs) - 5} more")

            print()


if __name__ == "__main__":
    main()
