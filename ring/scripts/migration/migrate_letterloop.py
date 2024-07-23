from datetime import datetime
from pathlib import Path
from pprint import pp
from sqlalchemy import select
import ring.crud.question as question_crud
import ring.crud.letter as letter_crud
from ring.postgres_models.group_model import Group
from ring.postgres_models.letter_model import Letter
from ring.letter.enums import LetterStatus
from ring.postgres_models.user_model import User
from ring.sqlalchemy_base import Session
from ring.scripts.script_base import script_di


@script_di()
def run_script(
    db: Session, group_name: str, issue_number: int, user_admin_email: str, dry_run: bool = True
) -> None:
    issue_file_path = Path(f"/src/ring/scripts/migration/{group_name}/{issue_number}.txt")
    if not issue_file_path.exists():
        raise ValueError(f"File not found: {issue_file_path}")
    user = db.scalars(select(User).where(User.email == user_admin_email)).one_or_none()
    assert user is not None, f"User not found: {user_admin_email}"
    with open(issue_file_path) as f:
        issue = f.readlines()
    try:
        _parse_issue(db, issue, user)
    except Exception as e:
        pp(e)
        db.rollback()
        raise e

    pp("Issue parsed successfully")
    if dry_run:
        pp("Dry run, rolling back")
        db.rollback()
    else:
        db.commit()


def _get_group(db: Session, name: str) -> Group:
    group = db.scalars(select(Group).where(Group.name == name)).one_or_none()
    assert group is not None, f"Group doesn't exist: {name}"
    return group


def _create_letter(
    db: Session, group: Group, sent_at: datetime | None = None
) -> Letter:
    letter = letter_crud.create_letter(
        db,
        group.api_identifier,
        send_at=sent_at,
        letter_status=LetterStatus.SENT,
    )
    if sent_at:
        letter.issue_sent = sent_at
        # letter.send_at = sent_at
    db.add(letter)
    db.flush()
    return letter


def _parse_issue(db: Session, issue_lines: list[str], user: User) -> Letter:
    group = _get_group(db, issue_lines[0].strip())
    m, d = issue_lines[2].strip().split(" ")[-2:]
    d = d[:-2]
    sent_at = datetime.strptime(f"2023 {m} {d}", "%Y %B %d")
    letter = _create_letter(db, group, sent_at)
    member_names = {m.name for m in group.members}

    current_question = None
    question_number = 0

    current_user = None
    current_answer = None
    for line in issue_lines[1:]:
        if line.startswith("QUESTION"):
            question_number += 1
            current_user = None
            author_name = None
            current_question = None
            line_segments = [s.strip() for s in line.split(":")]
            if len(line_segments) == 3:
                author_name = line_segments[1]
            question_text = line_segments[-1]

            author_user = db.scalars(
                select(User).where(User.name == author_name)
            ).one_or_none()
            current_question = letter_crud.add_question(
                db,
                letter,
                question_text,
                author_user,
            )
            print(current_question)
            db.add(current_question)
        elif ":" in line and (member_name := line.split(":")[0]) in member_names:
            if current_answer and current_user and current_question:
                response = question_crud.add_response(
                    db, current_question, current_user, current_answer
                )
                db.add(response)
                pp(str(response))
            current_answer = None
            [current_user] = [m for m in group.members if m.name == member_name]
            current_answer = line.split(":", maxsplit=1)[1].strip()
        else:
            if current_answer:
                current_answer += line.strip()
    return letter
