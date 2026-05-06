# Call Quality Evaluator API

This is a small student project built using **FastAPI + Gemini + SQLite**.
The idea is simple: upload a customer support call transcript, and the app gives a quality evaluation like score, sentiment, summary, and improvement advice.

## Project Goal

I created this project to practice:
- Building REST APIs with FastAPI
- Calling an AI model (Gemini) from Python
- Storing results in a database using SQLAlchemy
- Working with file upload endpoints

## Tech Stack

- Python
- FastAPI
- Uvicorn
- Google Gemini (`google-genai`)
- SQLAlchemy
- SQLite
- python-dotenv

## Folder Overview

- `main.py` -> FastAPI app and API endpoints
- `ai_transcript_analyst.py` -> Gemini prompt + transcript analysis logic
- `database.py` -> SQLite config and `Evaluation` table model
- `evaluations.db` -> Local database file
- `text_call.txt` -> Sample transcript file

## Setup Instructions

1. Clone/download this project.
2. Create and activate virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root folder:

```env
GEMINI_API_KEY=your_api_key_here
```

5. Run the server:

```bash
uvicorn main:app --reload
```

6. Open:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## API Endpoints

### 1) GET `/`
Health check endpoint.

**Response example**
```json
{
  "message": "Call Quality Evaluation API is ready"
}
```

### 2) POST `/evaluate/`
Upload a transcript file (`.txt`) and get AI evaluation.

- Input type: `multipart/form-data`
- Field name: `file`

**What it does:**
- Reads transcript text from uploaded file
- Sends transcript to Gemini
- Gets JSON result (`score`, `sentiment`, etc.)
- Saves result into SQLite database
- Returns saved record

**Response keys**
- `id`
- `filename`
- `score`
- `summary`
- `sentiment`
- `improvement_points`
- `is_issue_resolved`

### 3) GET `/evaluations/`
Returns all saved evaluations from database.

**Response includes**
- `id`
- `filename`
- `score`
- `sentiment`
- `summary`
- `improvement_points`
- `is_issue_resolved`
- `created_at`

### 4) GET `/evaluations/{evaluation_id}`
Returns one evaluation by ID.

- If ID does not exist, returns `404 Evaluation not found`

## Database Schema

Table: `evaluations`

- `id` (Integer, primary key)
- `filename` (String)
- `score` (Float)
- `sentiment` (String)
- `summary` (Text)
- `improvement_points` (Text)
- `is_issue_resolved` (Boolean)
- `created_at` (DateTime)

## Notes / Limitations

- This project currently assumes uploaded file content is UTF-8 text.
- Gemini response parsing is basic and may fail if output is not valid JSON.
- No authentication added yet (student-level prototype).

## Future Improvements

- Add authentication and rate limiting
- Better Gemini JSON validation with fallback handling
- Add unit tests and integration tests
- Add filtering/pagination for evaluations list

---
Made as a learning project by a student exploring AI + backend development.
