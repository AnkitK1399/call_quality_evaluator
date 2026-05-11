from typing import Any, Dict

from sqlalchemy.orm import Session

from ai_transcript_analyst import generate_followup_response_with_gemini
import database


def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file_obj:
        return file_obj.read()


def _evaluation_to_response_dict(evaluation: database.Evaluation) -> Dict[str, Any]:
    return {
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
            "resolution_evidence": evaluation.resolution_evidence,
        },
    }


def build_followup_context(
    evaluation_id: int,
    follow_up_question: str,
    db: Session,
) -> database.FollowUp:
    """
    Build follow-up context, call Gemini, persist FollowUp, and return saved row.

    Inputs:
    - evaluation_id: ID of the stored evaluation row.
    - follow_up_question: User's follow-up message for Gemini.
    - db: SQLAlchemy session.
    """
    evaluation = (
        db.query(database.Evaluation)
        .filter(database.Evaluation.id == evaluation_id)
        .first()
    )
    if not evaluation:
        raise ValueError(f"Evaluation not found for id={evaluation_id}")

    db_transcript_path = evaluation.filename
    db_prompt_path = evaluation.promptname
    if not db_prompt_path:
        raise ValueError(
            "No prompt path found in DB row. Set promptname for this evaluation."
        )

    transcript_content = _read_text_file(db_transcript_path)
    gemini_prompt_content = _read_text_file(db_prompt_path)

    previous_gemini_response = _evaluation_to_response_dict(evaluation)

    # Ready-to-send combined text for the next Gemini turn.
    combined_context = (
        f"Call Transcript:\n{transcript_content}\n\n"
        f"Gemini Prompt:\n{gemini_prompt_content}\n\n"
        f"Previous Gemini Response:\n{previous_gemini_response}\n\n"
        f"Follow-up Question:\n{follow_up_question}"
    )

    followup_response = generate_followup_response_with_gemini(
        combined_context
    )

    saved_followup = database.FollowUp(
        evaluation_id=evaluation_id,
        question=follow_up_question,
        response=followup_response,
    )
    db.add(saved_followup)
    db.commit()
    db.refresh(saved_followup)
    return saved_followup
