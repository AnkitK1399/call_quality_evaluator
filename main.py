from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from ai_transcript_analyst import analyze_transcript_with_gemini
from schemas import PathInputRequest
import csv
import database 

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

@app.get("/")
def home_page():
    return {"message": "Call Quality Evaluation API is ready"}

@app.post("/evaluate/")
async def evaluate_call(file: UploadFile = File(...), db: Session = Depends(get_db)):
    print('hello')
    try:
        content = await file.read()
        transcript_text = content.decode("utf-8")

        analysis = analyze_transcript_with_gemini(transcript_text, False)

        print(analysis)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # 3. Store Gemini's judgment in SQLite
    new_eval = database.Evaluation(
    filename=file.filename,

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
    resolution_evidence=analysis["verbatim_evidence"]["resolution_evidence"]
)
    
    db.add(new_eval)
    db.commit()
    db.refresh(new_eval)
    
    return {
    "message": "Gemini has completed the evaluation",
    "evaluation": {
        "id": new_eval.id,
    "filename": new_eval.filename,

    "score": new_eval.score,
    "score_justification": new_eval.score_justification,

    "summary": new_eval.summary,

    "sentiment": new_eval.sentiment,
    "sentiment_justification": new_eval.sentiment_justification,

    "improvement_points": new_eval.improvement_points,

    "is_issue_resolved": new_eval.is_issue_resolved,
    "resolution_justification": new_eval.resolution_justification,

    "verbatim_evidence": {
        "score_evidence": new_eval.score_evidence,
        "sentiment_evidence": new_eval.sentiment_evidence,
        "resolution_evidence": new_eval.resolution_evidence
    }
    }
}


@app.post("/path_input")
async def evaluate_call_from_path(
    payload: PathInputRequest,
    db: Session = Depends(get_db)
):
    try:
        is_second_path_used = False

        with open(payload.file_path, "r", encoding="utf-8") as f:
            transcript_text_1 = f.read()

        transcript_text_2 = None
        if payload.file_path_2:
            with open(payload.file_path_2, "r", encoding="utf-8") as f:
                transcript_text_2 = f.read()
            is_second_path_used = True

        transcript_for_analysis = transcript_text_1
        if transcript_text_2:
            transcript_for_analysis = f"{transcript_text_1}\n\n{transcript_text_2}"

        analysis = analyze_transcript_with_gemini(
            transcript_for_analysis,
            is_second_path_used
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Transcript file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    new_eval = database.Evaluation(
    filename=payload.file_path,

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
    resolution_evidence=analysis["verbatim_evidence"]["resolution_evidence"]
)

    db.add(new_eval)
    db.commit()
    db.refresh(new_eval)

    return {
        "message": "Gemini has completed the evaluation",
        "is_second_path_used": is_second_path_used,
        "evaluation": {
           "id": new_eval.id,
    "filename": new_eval.filename,

    "score": new_eval.score,
    "score_justification": new_eval.score_justification,

    "summary": new_eval.summary,

    "sentiment": new_eval.sentiment,
    "sentiment_justification": new_eval.sentiment_justification,

    "improvement_points": new_eval.improvement_points,

    "is_issue_resolved": new_eval.is_issue_resolved,
    "resolution_justification": new_eval.resolution_justification,

    "verbatim_evidence": {
        "score_evidence": new_eval.score_evidence,
        "sentiment_evidence": new_eval.sentiment_evidence,
        "resolution_evidence": new_eval.resolution_evidence
    }
        }
    }


@app.post("/csv_input")
async def evaluate_call_from_csv(
    payload: PathInputRequest,
    db: Session = Depends(get_db)
):
    try:
        with open(payload.file_path, "r", encoding="utf-8", newline="") as csv_file:
            reader = csv.reader(csv_file)
            rows = [row for row in reader if row]

        if not rows:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        first_row = rows[0]
        if len(first_row) >= 2 and (
            first_row[0].strip().lower() in ["call_transcript_path", "transcript_path"]
            or first_row[1].strip().lower() in ["gemini_prompt_path", "prompt_path"]
        ):
            if len(rows) < 2:
                raise HTTPException(status_code=400, detail="CSV has header but no data row")
            data_row = rows[1]
        else:
            data_row = first_row

        if len(data_row) < 2:
            raise HTTPException(
                status_code=400,
                detail="CSV must contain two columns: call transcript path and gemini prompt path"
            )

        call_transcript_path = data_row[0].strip()
        gemini_prompt_path = data_row[1].strip()

        with open(call_transcript_path, "r", encoding="utf-8") as f:
            transcript_text = f.read()

        with open(gemini_prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()

        concatenated_text = f"{transcript_text}\n\n{prompt_text}"
        analysis = analyze_transcript_with_gemini(concatenated_text, True)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV or referenced text file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    new_eval = database.Evaluation(
    filename=payload.file_path,

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
    resolution_evidence=analysis["verbatim_evidence"]["resolution_evidence"]
)

    db.add(new_eval)
    db.commit()
    db.refresh(new_eval)

    return {
        "message": "Gemini has completed the evaluation from CSV input",
        "is_second_path_used": True,
        "evaluation": {
            "id": new_eval.id,
    "filename": new_eval.filename,

    "score": new_eval.score,
    "score_justification": new_eval.score_justification,

    "summary": new_eval.summary,

    "sentiment": new_eval.sentiment,
    "sentiment_justification": new_eval.sentiment_justification,

    "improvement_points": new_eval.improvement_points,

    "is_issue_resolved": new_eval.is_issue_resolved,
    "resolution_justification": new_eval.resolution_justification,

    "verbatim_evidence": {
        "score_evidence": new_eval.score_evidence,
        "sentiment_evidence": new_eval.sentiment_evidence,
        "resolution_evidence": new_eval.resolution_evidence
    }
        },
        "csv_values": {
            "call_transcript_path": call_transcript_path,
            "gemini_prompt_path": gemini_prompt_path
        }
    }


@app.post("/multiple_text_file")
async def evaluate_multiple_calls_from_csv(
    payload: PathInputRequest,
    db: Session = Depends(get_db)
):
    try:
        with open(payload.file_path, "r", encoding="utf-8", newline="") as csv_file:
            reader = csv.reader(csv_file)
            rows = [row for row in reader if row]

        if not rows:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        start_index = 0
        first_row = rows[0]
        if len(first_row) >= 2 and (
            first_row[0].strip().lower() in ["call_transcript_path", "transcript_path"]
            or first_row[1].strip().lower() in ["gemini_prompt_path", "prompt_path"]
        ):
            start_index = 1

        if len(rows[start_index:]) == 0:
            raise HTTPException(status_code=400, detail="CSV has no data rows")

        evaluations_output = []

        for row in rows[start_index:]:
            if len(row) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="Each CSV row must contain call transcript path and gemini prompt path"
                )

            call_transcript_path = row[0].strip()
            gemini_prompt_path = row[1].strip()

            with open(call_transcript_path, "r", encoding="utf-8") as f:
                transcript_text = f.read()

            with open(gemini_prompt_path, "r", encoding="utf-8") as f:
                prompt_text = f.read()

            concatenated_text = f"{transcript_text}\n\n{prompt_text}"
            analysis = analyze_transcript_with_gemini(concatenated_text, True)

            new_eval = database.Evaluation(
    filename=call_transcript_path,

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
    resolution_evidence=analysis["verbatim_evidence"]["resolution_evidence"]
)

            db.add(new_eval)
            db.commit()
            db.refresh(new_eval)

            evaluations_output.append(
                {
    "id": new_eval.id,
    "filename": new_eval.filename,

    "score": new_eval.score,
    "score_justification": new_eval.score_justification,

    "summary": new_eval.summary,

    "sentiment": new_eval.sentiment,
    "sentiment_justification": new_eval.sentiment_justification,

    "improvement_points": new_eval.improvement_points,

    "is_issue_resolved": new_eval.is_issue_resolved,
    "resolution_justification": new_eval.resolution_justification,

    "verbatim_evidence": {
        "score_evidence": new_eval.score_evidence,
        "sentiment_evidence": new_eval.sentiment_evidence,
        "resolution_evidence": new_eval.resolution_evidence
    },

    "call_transcript_path": call_transcript_path,
    "gemini_prompt_path": gemini_prompt_path
}
            )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV or referenced text file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Gemini has completed evaluations for all CSV rows",
        "count": len(evaluations_output),
        "evaluations": evaluations_output
    }

@app.get("/evaluations/")
def get_all_evaluations(db: Session = Depends(get_db)):
    evaluations = db.query(database.Evaluation).all()

    return [
        {
    "id": e.id,
    "filename": e.filename,

    "score": e.score,
    "score_justification": e.score_justification,

    "sentiment": e.sentiment,
    "sentiment_justification": e.sentiment_justification,

    "summary": e.summary,

    "improvement_points": e.improvement_points,

    "is_issue_resolved": e.is_issue_resolved,
    "resolution_justification": e.resolution_justification,

    "verbatim_evidence": {
        "score_evidence": e.score_evidence,
        "sentiment_evidence": e.sentiment_evidence,
        "resolution_evidence": e.resolution_evidence
    },

    "created_at": e.created_at
}
        for e in evaluations
    ]



@app.get("/evaluations/{evaluation_id}")
def get_evaluation_by_id(evaluation_id: int, db: Session = Depends(get_db)):
    evaluation = db.query(database.Evaluation).filter(
        database.Evaluation.id == evaluation_id
    ).first()

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return {
    "id": evaluation.id,
    "filename": evaluation.filename,

    "score": evaluation.score,
    "score_justification": evaluation.score_justification,

    "sentiment": evaluation.sentiment,
    "sentiment_justification": evaluation.sentiment_justification,

    "summary": evaluation.summary,

    "improvement_points": evaluation.improvement_points,

    "is_issue_resolved": evaluation.is_issue_resolved,
    "resolution_justification": evaluation.resolution_justification,

    "verbatim_evidence": {
        "score_evidence": evaluation.score_evidence,
        "sentiment_evidence": evaluation.sentiment_evidence,
        "resolution_evidence": evaluation.resolution_evidence
    },

    "created_at": evaluation.created_at
}
