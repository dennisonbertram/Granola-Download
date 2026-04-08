# API Reference

Documentation of the Granola API endpoints used by this tool.

## Authentication

### Refresh Access Token

Exchanges a refresh token for a new access token using WorkOS authentication.

**Endpoint:** `POST https://api.workos.com/user_management/authenticate`

**Request Body:**

```json
{
  "client_id": "string",
  "grant_type": "refresh_token",
  "refresh_token": "string"
}
```

**Response:**

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

**Important:** Refresh tokens are single-use. Each exchange invalidates the old token and returns a new one. The tool handles this automatically.

---

## Required Headers

All API requests require:

```
Authorization: Bearer {access_token}
Content-Type: application/json
User-Agent: Granola/5.354.0
X-Client-Version: 5.354.0
```

---

## Endpoints

### Get Documents

Retrieves a paginated list of your documents.

**Endpoint:** `POST https://api.granola.ai/v2/get-documents`

```json
{
  "limit": 100,
  "offset": 0,
  "include_last_viewed_panel": true
}
```

> **Note:** This endpoint only returns documents you own. For shared documents, use Get Documents Batch.

---

### Get Document Transcript

Retrieves the audio transcript for a specific document.

**Endpoint:** `POST https://api.granola.ai/v1/get-document-transcript`

```json
{
  "document_id": "string"
}
```

Returns `404` if the document has no transcript.

---

### Get Workspaces

Retrieves all workspaces (organizations) you have access to.

**Endpoint:** `POST https://api.granola.ai/v1/get-workspaces`

```json
{}
```

---

### Get Document Lists (Folders)

Retrieves all document lists (folders).

**Endpoints:**
- `POST https://api.granola.ai/v2/get-document-lists` (preferred)
- `POST https://api.granola.ai/v1/get-document-lists` (fallback)

```json
{}
```

---

### Get Documents Batch

Fetch multiple documents by ID. This is the only way to retrieve shared documents.

**Endpoint:** `POST https://api.granola.ai/v1/get-documents-batch`

```json
{
  "document_ids": ["id1", "id2"],
  "include_last_viewed_panel": true
}
```

**Recommended workflow:**
1. Use `get-document-lists` to get folder contents (returns document IDs)
2. Use `get-documents-batch` to fetch the actual documents (including shared ones)

---

## Data Structures

### Document

```json
{
  "id": "string",
  "title": "string",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "workspace_id": "string",
  "last_viewed_panel": {
    "content": {
      "type": "doc",
      "content": []
    }
  }
}
```

### Transcript Utterance

```json
{
  "source": "microphone|system",
  "text": "string",
  "start_timestamp": "ISO8601",
  "end_timestamp": "ISO8601",
  "confidence": 0.95
}
```
