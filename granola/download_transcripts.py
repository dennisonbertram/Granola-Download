#!/usr/bin/env python3
"""
Download all Granola transcripts (including shared docs via folder lists).
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import requests

from token_manager import TokenManager


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('granola_transcripts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def sanitize_filename(value, max_length=80):
    invalid_chars = '<>:"/\\|?*'
    cleaned = ''.join(c for c in value if c not in invalid_chars)
    cleaned = "_".join(cleaned.split())
    cleaned = cleaned.strip("_")
    if not cleaned:
        return ""
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip("_")
    return cleaned


def format_meeting_date(value):
    if not value:
        return "unknown-date"
    try:
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return "unknown-date"


def build_folder_name(doc_id, title, meeting_date, mode, used_folder_names):
    safe_title = sanitize_filename(title) or "untitled"
    date_str = format_meeting_date(meeting_date)

    if mode == "id":
        folder_name = doc_id
    elif mode == "title":
        folder_name = safe_title
    elif mode == "title-id":
        folder_name = f"{safe_title}__{doc_id}"
    elif mode == "date-title":
        folder_name = f"{date_str}__{safe_title}"
    elif mode == "date-id":
        folder_name = f"{date_str}__{doc_id}"
    else:
        folder_name = f"{date_str}__{safe_title}__{doc_id}"

    if used_folder_names.get(folder_name) not in (None, doc_id):
        folder_name = f"{folder_name}__{doc_id}"

    used_folder_names[folder_name] = doc_id
    return folder_name


def check_config_exists():
    config_path = Path('config.json')
    if not config_path.exists():
        logger.error("Config file 'config.json' not found!")
        logger.error("Please create config.json from config.json.template:")
        logger.error("  1. Copy config.json.template to config.json")
        logger.error("  2. Add your refresh_token and client_id")
        logger.error("  3. See GETTING_REFRESH_TOKEN.md for instructions on obtaining tokens")
        return False
    return True


def build_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "User-Agent": "Granola/5.354.0",
        "X-Client-Version": "5.354.0"
    }


def post_with_refresh(token_manager, url, payload, timeout):
    token = token_manager.get_valid_token()
    if not token:
        return None

    headers = build_headers(token)
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code == 401:
        logger.info("Access token expired, refreshing and retrying...")
        if not token_manager.refresh_access_token():
            logger.error("Failed to refresh access token")
            return None
        headers = build_headers(token_manager.access_token)
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)

    response.raise_for_status()
    return response


def fetch_granola_documents(token_manager, limit, timeout):
    url = "https://api.granola.ai/v2/get-documents"
    all_documents = []
    offset = 0

    while True:
        payload = {
            "limit": limit,
            "offset": offset,
            "include_last_viewed_panel": False
        }
        try:
            logger.info(f"Fetching documents: offset={offset}, limit={limit}")
            response = post_with_refresh(token_manager, url, payload, timeout)
            if response is None:
                return None
            result = response.json()
            docs = result.get("docs", [])
            if not docs:
                break
            all_documents.extend(docs)
            if len(docs) < limit:
                break
            offset += limit
        except Exception as e:
            logger.error(f"Error fetching documents at offset {offset}: {str(e)}")
            if offset == 0:
                return None
            break

    logger.info(f"Total documents fetched: {len(all_documents)}")
    return all_documents


def fetch_document_lists(token_manager, timeout):
    endpoints = [
        "https://api.granola.ai/v2/get-document-lists",
        "https://api.granola.ai/v1/get-document-lists"
    ]

    for url in endpoints:
        try:
            logger.info(f"Trying endpoint: {url}")
            response = post_with_refresh(token_manager, url, {}, timeout)
            if response is None:
                continue
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.info(f"Endpoint {url} not found (404), trying next...")
                continue
            logger.warning(f"HTTP error from {url}: {str(e)}, trying next...")
        except Exception as e:
            logger.warning(f"Error from {url}: {str(e)}, trying next...")

    logger.warning("All document list endpoints failed")
    return None


def extract_document_ids(lists_response):
    if not lists_response:
        return set()

    lists = []
    if isinstance(lists_response, list):
        lists = lists_response
    elif isinstance(lists_response, dict):
        if "lists" in lists_response:
            lists = lists_response["lists"]
        elif "document_lists" in lists_response:
            lists = lists_response["document_lists"]

    document_ids = set()
    for doc_list in lists:
        documents_in_list = doc_list.get("documents", [])
        if not documents_in_list:
            documents_in_list = doc_list.get("document_ids", [])

        for doc in documents_in_list:
            if isinstance(doc, dict):
                doc_id = doc.get("id") or doc.get("document_id")
            else:
                doc_id = doc
            if doc_id:
                document_ids.add(doc_id)

    return document_ids


def fetch_documents_batch(token_manager, document_ids, batch_size, timeout):
    if not document_ids:
        return []

    url = "https://api.granola.ai/v1/get-documents-batch"
    all_documents = []

    for i in range(0, len(document_ids), batch_size):
        batch = document_ids[i:i + batch_size]
        payload = {
            "document_ids": batch,
            "include_last_viewed_panel": False
        }
        try:
            logger.info(f"Fetching batch {i // batch_size + 1}: {len(batch)} documents")
            response = post_with_refresh(token_manager, url, payload, timeout)
            if response is None:
                continue
            result = response.json()
            docs = result.get("documents") or result.get("docs") or []
            all_documents.extend(docs)
        except Exception as e:
            logger.error(f"Error fetching batch at index {i}: {str(e)}")
            continue

    logger.info(f"Total documents fetched via batch: {len(all_documents)}/{len(document_ids)}")
    return all_documents


def fetch_document_transcript(token_manager, document_id, timeout):
    url = "https://api.granola.ai/v1/get-document-transcript"
    payload = {"document_id": document_id}
    try:
        response = post_with_refresh(token_manager, url, payload, timeout)
        if response is None:
            return None
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            logger.debug(f"No transcript found for document {document_id}")
            return None
        logger.error(f"Error fetching transcript for {document_id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error fetching transcript for {document_id}: {str(e)}")
        return None


def convert_transcript_to_markdown(transcript_data):
    if not transcript_data or not isinstance(transcript_data, list):
        return "# Transcript\n\nNo transcript content available.\n"

    markdown = ["# Transcript\n\n"]
    for utterance in transcript_data:
        source = utterance.get('source', 'unknown')
        text = utterance.get('text', '')
        start_timestamp = utterance.get('start_timestamp', '')
        speaker = "Microphone" if source == "microphone" else "System"

        timestamp_str = ""
        if start_timestamp:
            try:
                dt = datetime.fromisoformat(start_timestamp.replace('Z', '+00:00'))
                timestamp_str = f"[{dt.strftime('%H:%M:%S')}]"
            except Exception:
                timestamp_str = ""

        markdown.append(f"**{speaker}** {timestamp_str}\n\n{text}\n\n")

    return ''.join(markdown)


def write_json(path, payload):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)


def load_existing_metadata(output_path):
    existing = {}
    for folder in output_path.iterdir():
        if not folder.is_dir():
            continue
        metadata_path = folder / "transcript_metadata.json"
        if not metadata_path.exists():
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        except Exception:
            continue
        doc_id = metadata.get("document_id")
        if not doc_id:
            continue
        existing[doc_id] = {
            "folder": folder.name,
            "title": metadata.get("title"),
            "meeting_date": metadata.get("meeting_date"),
        }
    return existing


def main():
    parser = argparse.ArgumentParser(
        description="Download all Granola transcripts (including shared docs)."
    )
    parser.add_argument(
        "output_dir",
        type=str,
        help="Directory to write transcripts into."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-download transcripts even if files already exist."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for get-documents-batch requests."
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Page size for get-documents pagination."
    )
    parser.add_argument(
        "--folder-name",
        type=str,
        default="id",
        choices=["id", "title", "title-id", "date-title", "date-title-id", "date-id"],
        help="Folder naming scheme: id, title, title-id, date-title, date-title-id, date-id."
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP request timeout in seconds."
    )
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if not check_config_exists():
        return

    token_manager = TokenManager()

    logger.info("Fetching document lists...")
    lists_response = fetch_document_lists(token_manager, args.timeout)
    list_doc_ids = extract_document_ids(lists_response)
    logger.info(f"Document IDs found in lists: {len(list_doc_ids)}")

    logger.info("Fetching documents from lists (includes shared docs)...")
    list_docs = fetch_documents_batch(
        token_manager,
        sorted(list_doc_ids),
        args.batch_size,
        args.timeout
    )

    logger.info("Fetching owned documents...")
    owned_docs = fetch_granola_documents(token_manager, args.page_size, args.timeout) or []

    docs_by_id = {}
    for doc in list_docs + owned_docs:
        doc_id = doc.get("id")
        if doc_id:
            docs_by_id[doc_id] = doc

    all_doc_ids = set(list_doc_ids) | set(docs_by_id.keys())
    logger.info(f"Total unique document IDs to check: {len(all_doc_ids)}")

    index_entries = []
    existing_by_doc_id = load_existing_metadata(output_path) if not args.overwrite else {}
    used_folder_names = {
        entry["folder"]: doc_id for doc_id, entry in existing_by_doc_id.items()
    }
    downloaded = 0
    skipped = 0
    missing = 0
    errors = 0

    for doc_id in sorted(all_doc_ids):
        existing = existing_by_doc_id.get(doc_id)
        if existing and not args.overwrite:
            skipped += 1
            index_entries.append({
                "document_id": doc_id,
                "title": existing.get("title"),
                "output_folder": existing.get("folder"),
                "status": "skipped",
                "reason": "transcript already exists"
            })
            continue

        doc = docs_by_id.get(doc_id, {})
        title = doc.get("title") or (existing.get("title") if existing else None) or "Untitled Granola Note"

        transcript_data = fetch_document_transcript(token_manager, doc_id, args.timeout)
        if not transcript_data:
            missing += 1
            index_entries.append({
                "document_id": doc_id,
                "title": title,
                "output_folder": None,
                "status": "no_transcript"
            })
            continue

        try:
            meeting_date = transcript_data[0].get('start_timestamp') if transcript_data else None
            if not meeting_date:
                meeting_date = doc.get("created_at") or existing.get("meeting_date") if existing else None

            folder_name = build_folder_name(
                doc_id,
                title,
                meeting_date,
                args.folder_name,
                used_folder_names
            )
            doc_folder = output_path / folder_name
            transcript_json_path = doc_folder / "transcript.json"
            transcript_md_path = doc_folder / "transcript.md"

            doc_folder.mkdir(parents=True, exist_ok=True)
            write_json(transcript_json_path, transcript_data)
            transcript_md = convert_transcript_to_markdown(transcript_data)
            with open(transcript_md_path, 'w', encoding='utf-8') as f:
                f.write(transcript_md)

            metadata = {
                "document_id": doc_id,
                "title": title,
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at"),
                "workspace_id": doc.get("workspace_id"),
                "output_folder": folder_name,
                "meeting_date": meeting_date,
                "sources": list({u.get('source', 'unknown') for u in transcript_data})
            }
            write_json(doc_folder / "transcript_metadata.json", metadata)

            index_entries.append({
                "document_id": doc_id,
                "title": title,
                "output_folder": folder_name,
                "status": "downloaded"
            })
            downloaded += 1
        except Exception as e:
            errors += 1
            logger.error(f"Failed to save transcript for {doc_id}: {str(e)}")
            index_entries.append({
                "document_id": doc_id,
                "title": title,
                "output_folder": folder_name,
                "status": "error",
                "error": str(e)
            })

    index_path = output_path / "transcripts_index.json"
    write_json(index_path, {
        "downloaded": downloaded,
        "skipped": skipped,
        "no_transcript": missing,
        "errors": errors,
        "total": len(all_doc_ids),
        "entries": index_entries
    })

    logger.info(
        "Done. downloaded=%s skipped=%s no_transcript=%s errors=%s total=%s",
        downloaded,
        skipped,
        missing,
        errors,
        len(all_doc_ids)
    )


if __name__ == "__main__":
    main()
