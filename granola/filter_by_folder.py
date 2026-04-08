#!/usr/bin/env python3
"""
Filter Granola Documents by Folder (Document List)

This script helps you filter and list documents by folder/document list.
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


def load_document_lists(output_dir):
    """
    Load document lists information from saved document_lists.json

    Args:
        output_dir: Directory containing document_lists.json

    Returns:
        dict: List ID to list info mapping
    """
    lists_path = output_dir / "document_lists.json"
    list_map = {}

    if not lists_path.exists():
        logger.warning(f"No document_lists.json found at {lists_path}")
        return list_map

    try:
        with open(lists_path, 'r') as f:
            lists_data = json.load(f)

        # Handle different response formats
        lists = []
        if isinstance(lists_data, list):
            lists = lists_data
        elif isinstance(lists_data, dict):
            if "lists" in lists_data:
                lists = lists_data["lists"]
            elif "document_lists" in lists_data:
                lists = lists_data["document_lists"]

        for doc_list in lists:
            list_id = doc_list.get("id")
            if list_id:
                list_map[list_id] = doc_list

    except Exception as e:
        logger.error(f"Error loading document lists: {e}")

    return list_map


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


def filter_by_folder(documents, folder_id):
    """
    Filter documents by folder ID

    Args:
        documents: List of document metadata
        folder_id: Folder ID to filter by

    Returns:
        list: Filtered documents
    """
    filtered = []
    for doc in documents:
        folders = doc.get("folders", [])
        for folder in folders:
            if folder.get("id") == folder_id:
                filtered.append(doc)
                break
    return filtered


def filter_by_folder_name(documents, folder_name):
    """
    Filter documents by folder name (case-insensitive partial match)

    Args:
        documents: List of document metadata
        folder_name: Folder name to search for

    Returns:
        list: Filtered documents
    """
    filtered = []
    for doc in documents:
        folders = doc.get("folders", [])
        for folder in folders:
            if folder_name.lower() in folder.get("name", "").lower():
                filtered.append(doc)
                break
    return filtered


def group_by_folder(documents):
    """
    Group documents by folder

    Args:
        documents: List of document metadata

    Returns:
        dict: Folder ID to list of documents mapping
    """
    groups = defaultdict(list)
    no_folder = []

    for doc in documents:
        folders = doc.get("folders", [])
        if not folders:
            no_folder.append(doc)
        else:
            for folder in folders:
                folder_id = folder.get("id", "unknown")
                groups[folder_id].append({
                    "doc": doc,
                    "folder_name": folder.get("name", "Unknown")
                })

    return dict(groups), no_folder


def main():
    parser = argparse.ArgumentParser(
        description="Filter and list Granola documents by folder (document list)"
    )
    parser.add_argument(
        "output_dir",
        type=str,
        help="Directory containing saved documents"
    )
    parser.add_argument(
        "--folder-id",
        type=str,
        help="Filter by specific folder ID"
    )
    parser.add_argument(
        "--folder-name",
        type=str,
        help="Filter by folder name (case-insensitive partial match)"
    )
    parser.add_argument(
        "--list-folders",
        action="store_true",
        help="List all folders and their document counts"
    )
    parser.add_argument(
        "--no-folder",
        action="store_true",
        help="Show documents that are not in any folder"
    )

    args = parser.parse_args()
    output_path = Path(args.output_dir)

    if not output_path.exists():
        logger.error(f"Output directory {output_path} does not exist")
        return

    # Load folder information
    folder_map = load_document_lists(output_path)

    # Load all documents
    logger.info(f"Loading documents from {output_path}...")
    documents = get_all_documents(output_path)
    logger.info(f"Loaded {len(documents)} documents")
    print()

    if args.list_folders:
        # List all folders with document counts
        groups, no_folder = group_by_folder(documents)

        print("=" * 80)
        print("Folders Summary")
        print("=" * 80)
        print()

        # Sort by document count
        sorted_groups = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)

        for folder_id, docs in sorted_groups:
            folder_name = docs[0]["folder_name"] if docs else "Unknown"
            folder_info = folder_map.get(folder_id, {})

            print(f"Folder: {folder_name}")
            print(f"  ID: {folder_id}")
            print(f"  Documents: {len(docs)}")

            if folder_info:
                if "created_at" in folder_info:
                    print(f"  Created: {folder_info.get('created_at')}")
                if "workspace_id" in folder_info:
                    print(f"  Workspace ID: {folder_info.get('workspace_id')}")
            print()

        if no_folder:
            print(f"Documents not in any folder: {len(no_folder)}")
            print()

    elif args.no_folder:
        # Show documents not in any folder
        _, no_folder = group_by_folder(documents)

        print("=" * 80)
        print("Documents Not in Any Folder")
        print("=" * 80)
        print()

        if not no_folder:
            print("All documents are organized in folders!")
        else:
            for i, doc in enumerate(no_folder, 1):
                print(f"{i}. {doc.get('title', 'Untitled')}")
                print(f"   ID: {doc.get('document_id', 'N/A')}")
                print(f"   Created: {doc.get('created_at', 'N/A')}")
                print()

            print(f"Total: {len(no_folder)} documents")

    elif args.folder_id:
        # Filter by folder ID
        filtered = filter_by_folder(documents, args.folder_id)
        folder_info = folder_map.get(args.folder_id, {})
        folder_name = folder_info.get("name") or folder_info.get("title", "Unknown Folder")

        print("=" * 80)
        print(f"Documents in Folder: {folder_name}")
        print(f"Folder ID: {args.folder_id}")
        print("=" * 80)
        print()

        if not filtered:
            print("No documents found in this folder.")
        else:
            for i, doc in enumerate(filtered, 1):
                print(f"{i}. {doc.get('title', 'Untitled')}")
                print(f"   ID: {doc.get('document_id', 'N/A')}")
                print(f"   Created: {doc.get('created_at', 'N/A')}")
                print(f"   Updated: {doc.get('updated_at', 'N/A')}")
                print()

            print(f"Total: {len(filtered)} documents")

    elif args.folder_name:
        # Filter by folder name
        filtered = filter_by_folder_name(documents, args.folder_name)

        print("=" * 80)
        print(f"Documents with Folder Name Matching: '{args.folder_name}'")
        print("=" * 80)
        print()

        if not filtered:
            print(f"No documents found in folders matching '{args.folder_name}'")
        else:
            # Group by exact folder
            by_folder = defaultdict(list)
            for doc in filtered:
                for folder in doc.get("folders", []):
                    if args.folder_name.lower() in folder.get("name", "").lower():
                        by_folder[folder.get("name")].append(doc)

            for folder_name, docs in by_folder.items():
                print(f"\nFolder: {folder_name}")
                print(f"Documents: {len(docs)}")
                print("-" * 80)

                for i, doc in enumerate(docs, 1):
                    print(f"  {i}. {doc.get('title', 'Untitled')}")
                    print(f"     ID: {doc.get('document_id', 'N/A')}")
                print()

            print(f"Total: {len(filtered)} documents")

    else:
        # No filter - show all documents grouped by folder
        groups, no_folder = group_by_folder(documents)

        print("=" * 80)
        print("All Documents Grouped by Folder")
        print("=" * 80)
        print()

        for folder_id, docs in groups.items():
            folder_name = docs[0]["folder_name"] if docs else "Unknown"

            print(f"Folder: {folder_name}")
            print(f"ID: {folder_id}")
            print(f"Documents: {len(docs)}")
            print("-" * 80)

            for i, item in enumerate(docs[:5], 1):  # Show first 5
                doc = item["doc"]
                print(f"  {i}. {doc.get('title', 'Untitled')}")

            if len(docs) > 5:
                print(f"  ... and {len(docs) - 5} more")

            print()

        if no_folder:
            print(f"\nDocuments not in any folder: {len(no_folder)}")
            for i, doc in enumerate(no_folder[:5], 1):
                print(f"  {i}. {doc.get('title', 'Untitled')}")
            if len(no_folder) > 5:
                print(f"  ... and {len(no_folder) - 5} more")


if __name__ == "__main__":
    main()
