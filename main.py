import csv

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

import database
from ai_transcript_analyst import analyze_transcript_with_gemini
from schemas import PathInputRequest

app = FastAPI()


@app.on_event("startup")
def startup_event():
    database.init_db()


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _build_evaluation_record(filename: str, analysis: dict) -> database.Evaluation:
    return database.Evaluation(
        filename=filename,
        score=analysis["score"],
        score_justification=analysis["score_justification"],
        summary=analysis["summary"],
        sentiment=analysis["sentiment"],
        sentiment_justification=analysis["sentiment_justification"],
        improvement_points=analysis["improvement_points"],
        is_issue_resolved=analysis["is_issue_resolved"],
        resolution_justification=analysis["resolution_justification"],
        score_evidence=analysis["verbatim_evidence"]["score_evidence"],
        sentiment_evidence=analysis["verbatim_evidence"]["sentiment_evidence"],
        resolution_evidence=analysis["verbatim_evidence"]["resolution_evidence"],
    )


def _save_evaluation(db: Session, evaluation: database.Evaluation) -> database.Evaluation:
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


def _evaluation_payload(evaluation: database.Evaluation) -> dict:
    return {
        "id": evaluation.id,
        "filename": evaluation.filename,
        "score": evaluation.score,
        "score_justification": evaluation.score_justification,
        "summary": evaluation.summary,
        "sentiment": evaluation.sentiment,
        "sentiment_justification": evaluation.sentiment_justification,
        "improvement_points": evaluation.improvement_points,
        "is_issue_resolved": evaluation.is_issue_resolved,
        "resolution_justification": evaluation.resolution_justification,
        "verbatim_evidence": {
            "score_evidence": evaluation.score_evidence,
            "sentiment_evidence": evaluation.sentiment_evidence,
            "resolution_evidence": evaluation.resolution_evidence,
        },
    }


def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file_obj:
        return file_obj.read()


def _read_csv_rows(path: str):
    with open(path, "r", encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        return [row for row in reader if row]


def _has_csv_header(row) -> bool:
    return len(row) >= 2 and (
        row[0].strip().lower() in ["call_transcript_path", "transcript_path"]
        or row[1].strip().lower() in ["gemini_prompt_path", "prompt_path"]
    )


@app.get("/")
def home_page():
    return {"message": "Call Quality Evaluation API is ready"}


@app.post("/evaluate/")
async def evaluate_call(file: UploadFile = File(...), db: Session = Depends(get_db)):
    print("hello")
    try:
        content = await file.read()
        transcript_text = content.decode("utf-8")
        analysis = analyze_transcript_with_gemini(transcript_text, False)
        print(analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    new_eval = _build_evaluation_record(file.filename, analysis)
    saved_eval = _save_evaluation(db, new_eval)

    return {
        "message": "Gemini has completed the evaluation",
        "evaluation": _evaluation_payload(saved_eval),
    }


@app.post("/path_input")
async def evaluate_call_from_path(payload: PathInputRequest, db: Session = Depends(get_db)):
    try:
        is_second_path_used = False
        transcript_text_1 = _read_text_file(payload.file_path)

        transcript_text_2 = None
        if payload.file_path_2:
            transcript_text_2 = _read_text_file(payload.file_path_2)
            is_second_path_used = True

        transcript_for_analysis = transcript_text_1
        if transcript_text_2:
            transcript_for_analysis = f"{transcript_text_1}\n\n{transcript_text_2}"

        analysis = analyze_transcript_with_gemini(transcript_for_analysis, is_second_path_used)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Transcript file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    new_eval = _build_evaluation_record(payload.file_path, analysis)
    saved_eval = _save_evaluation(db, new_eval)

    return {
        "message": "Gemini has completed the evaluation",
        "is_second_path_used": is_second_path_used,
        "evaluation": _evaluation_payload(saved_eval),
    }


@app.post("/csv_input")
async def evaluate_call_from_csv(payload: PathInputRequest, db: Session = Depends(get_db)):
    try:
        rows = _read_csv_rows(payload.file_path)
        if not rows:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        first_row = rows[0]
        if _has_csv_header(first_row):
            if len(rows) < 2:
                raise HTTPException(status_code=400, detail="CSV has header but no data row")
            data_row = rows[1]
        else:
            data_row = first_row

        if len(data_row) < 2:
            raise HTTPException(
                status_code=400,
                detail="CSV must contain two columns: call transcript path and gemini prompt path",
            )

        call_transcript_path = data_row[0].strip()
        gemini_prompt_path = data_row[1].strip()

        transcript_text = _read_text_file(call_transcript_path)
        prompt_text = _read_text_file(gemini_prompt_path)
        concatenated_text = f"{transcript_text}\n\n{prompt_text}"

        analysis = analyze_transcript_with_gemini(concatenated_text, True)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV or referenced text file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    new_eval = _build_evaluation_record(payload.file_path, analysis)
    saved_eval = _save_evaluation(db, new_eval)

    return {
        "message": "Gemini has completed the evaluation from CSV input",
        "is_second_path_used": True,
        "evaluation": _evaluation_payload(saved_eval),
        "csv_values": {
            "call_transcript_path": call_transcript_path,
            "gemini_prompt_path": gemini_prompt_path,
        },
    }


@app.post("/multiple_text_file")
async def evaluate_multiple_calls_from_csv(payload: PathInputRequest, db: Session = Depends(get_db)):
    try:
        rows = _read_csv_rows(payload.file_path)
        if not rows:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        start_index = 1 if _has_csv_header(rows[0]) else 0
        if len(rows[start_index:]) == 0:
            raise HTTPException(status_code=400, detail="CSV has no data rows")

        evaluations_output = []
        for row in rows[start_index:]:
            if len(row) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="Each CSV row must contain call transcript path and gemini prompt path",
                )

            call_transcript_path = row[0].strip()
            gemini_prompt_path = row[1].strip()

            transcript_text = _read_text_file(call_transcript_path)
            prompt_text = _read_text_file(gemini_prompt_path)
            concatenated_text = f"{transcript_text}\n\n{prompt_text}"
            analysis = analyze_transcript_with_gemini(concatenated_text, True)

            new_eval = _build_evaluation_record(call_transcript_path, analysis)
            saved_eval = _save_evaluation(db, new_eval)

            payload_item = _evaluation_payload(saved_eval)
            payload_item["call_transcript_path"] = call_transcript_path
            payload_item["gemini_prompt_path"] = gemini_prompt_path
            evaluations_output.append(payload_item)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV or referenced text file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Gemini has completed evaluations for all CSV rows",
        "count": len(evaluations_output),
        "evaluations": evaluations_output,
    }


@app.get("/evaluations/")
def get_all_evaluations(db: Session = Depends(get_db)):
    evaluations = db.query(database.Evaluation).all()
    return [
        {
            **_evaluation_payload(evaluation),
            "created_at": evaluation.created_at,
        }
        for evaluation in evaluations
    ]


@app.get("/evaluations/{evaluation_id}")
def get_evaluation_by_id(evaluation_id: int, db: Session = Depends(get_db)):
    evaluation = db.query(database.Evaluation).filter(database.Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return {
        **_evaluation_payload(evaluation),
        "created_at": evaluation.created_at,
    }
