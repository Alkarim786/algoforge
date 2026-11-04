"""RQ job. Runs in the worker container: rq worker --url $REDIS_URL submissions"""
import logging

from sqlalchemy import select

from app import drivers
from app.db import SessionLocal
from app.evaluation import ACCEPTED, FINISHED, PENDING, RUNNING, RUNTIME_ERROR, SYSTEM_ERROR
from app.judge import case_verdict, custom_case_verdict, overall_verdict
from app.models import Problem, Submission, SubmissionResult, TestCase
from app.sandbox import SandboxError, SandboxKilled, run_code

logger = logging.getLogger(__name__)

MAX_STORED_OUTPUT = 10_000


def clean_output(text: str) -> str:
    # Postgres text columns reject NUL bytes, and user programs can print anything.
    return text.replace("\x00", "�")[:MAX_STORED_OUTPUT]


def judge_submission(submission_id: int) -> None:
    with SessionLocal() as db:
        submission = db.get(Submission, submission_id)
        if submission is None or submission.status != PENDING:
            return
        submission.status = RUNNING
        db.commit()

        entry = db.get(Problem, submission.problem_id).entry
        query = select(TestCase).where(TestCase.problem_id == submission.problem_id).order_by(TestCase.id)
        if submission.kind == "run":
            query = query.where(TestCase.is_hidden.is_(False))
        stored_cases = list(db.scalars(query))

        # A custom input identical to a visible case can still be compared against its expected output.
        # Only visible cases are in this lookup, so custom inputs can't be used to probe hidden ones.
        if submission.custom_inputs is None:
            inputs = [case.input for case in stored_cases]
            cases = stored_cases
        else:
            by_input = {case.input.strip(): case for case in stored_cases}
            inputs = submission.custom_inputs
            cases = [by_input.get(text.strip()) for text in inputs]

        try:
            runs = run_code(submission.language, drivers.wrap(entry, submission.code), inputs)
        except SandboxKilled:
            submission.status = RUNTIME_ERROR
            db.commit()
            return
        except Exception:
            logger.exception("Sandbox failed for submission %s", submission_id)
            submission.status = SYSTEM_ERROR
            db.commit()
            return

        verdicts = []
        for case, text, run in zip(cases, inputs, runs):
            debug, answer = drivers.split_output(entry, run.stdout)
            if case is None:
                verdict = custom_case_verdict(run.outcome)
            else:
                verdict = case_verdict(run.outcome, answer, case.expected_output)
            verdicts.append(verdict)
            db.add(
                SubmissionResult(
                    submission_id=submission.id,
                    test_case_id=case.id if case else None,
                    custom_input=None if case else clean_output(text),
                    passed=verdict in (ACCEPTED, FINISHED),
                    verdict=verdict,
                    actual_output=clean_output(answer),
                    stdout=clean_output(debug),
                    stderr=clean_output(run.stderr),
                    runtime_ms=run.runtime_ms,
                    memory_kb=run.memory_kb,
                )
            )
        submission.status = overall_verdict(verdicts)
        db.commit()
