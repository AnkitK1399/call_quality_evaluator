from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from ai_transcript_analyst import analyze_transcript_with_gemini
import database 

app = FastAPI()

# Create the database tables on startup
@app.on_event("startup")
def startup_event():
    database.init_db()

# This helps us get a database connection for each request
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

        analysis = analyze_transcript_with_gemini(transcript_text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # 3. Store Gemini's judgment in SQLite
    new_eval = database.Evaluation(
    filename=file.filename,
    score=analysis["score"],
    summary=analysis["summary"],
    sentiment=analysis["sentiment"],
    improvement_points=analysis["improvement_points"],
    is_issue_resolved=analysis["is_issue_resolved"]
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
        "summary": new_eval.summary,
        "sentiment": new_eval.sentiment,
        "improvement_points": new_eval.improvement_points,
        "is_issue_resolved": new_eval.is_issue_resolved
    }
}

@app.get("/evaluations/")
def get_all_evaluations(db: Session = Depends(get_db)):
    evaluations = db.query(database.Evaluation).all()

    return [
        {
            "id": e.id,
            "filename": e.filename,
            "score": e.score,
            "sentiment": e.sentiment,
            "summary": e.summary,
            "improvement_points": e.improvement_points,
            "is_issue_resolved": e.is_issue_resolved,
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
        "sentiment": evaluation.sentiment,
        "summary": evaluation.summary,
        "improvement_points": evaluation.improvement_points,
        "is_issue_resolved": evaluation.is_issue_resolved,
        "created_at": evaluation.created_at
    }