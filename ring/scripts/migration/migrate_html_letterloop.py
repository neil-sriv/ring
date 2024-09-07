from datetime import datetime
from pathlib import Path
from pprint import pp
import re
import tempfile
import requests
from sqlalchemy import select
import ring.letters.crud.question as question_crud
import ring.letters.crud.letter as letter_crud
from ring.letters.crud.response import upload_image
from ring.parties.models.group_model import Group
from ring.letters.models.letter_model import Letter
from ring.letters.constants import LetterStatus
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.parties.models.user_model import User
from ring.sqlalchemy_base import Session
from ring.scripts.script_base import script_di
from bs4 import BeautifulSoup, PageElement, Tag


@script_di()
def run_script(
    db: Session,
    group_name: str,
    issue_numbers: list[int],
    user_admin_email: str,
    dry_run: bool = True,
) -> None:
    for issue_number in issue_numbers:
        issue_file_path = Path(
            f"/src/ring/scripts/migration/{group_name}/{issue_number}.html"
        )
        if not issue_file_path.exists():
            raise ValueError(f"File not found: {issue_file_path}")
        user = db.scalars(
            select(User).where(User.email == user_admin_email)
        ).one_or_none()
        assert user is not None, f"User not found: {user_admin_email}"
        with open(issue_file_path) as f:
            soup = BeautifulSoup(f, "html.parser")
        try:
            _parse_issue(db, soup, user)
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
    db: Session,
    group: Group,
    sent_at: datetime,
    number: int,
) -> Letter:
    letter = letter_crud.create_letter(
        db,
        group.api_identifier,
        send_at=sent_at,
        letter_status=LetterStatus.SENT,
        number=number,
    )
    db.add(letter)
    db.flush()
    return letter


def _parse_issue(db: Session, soup: BeautifulSoup, user: User) -> Letter:
    texts = soup.find_all(class_=re.compile("chakra-text.*"))
    group = _get_group(db, texts[2].string)
    number_text, date_text = texts[3].string.split(" · ")
    issue_number = int(number_text.split("Issue No.")[-1])
    m, d = date_text.split(" ")[-2:]
    d = d[:-2]
    sent_at = datetime.strptime(f"2023 {m} {d}", "%Y %B %d")
    letter = _create_letter(db, group, sent_at, number=issue_number)
    member_names = {m.name for m in group.members}

    content_stack = soup.find_all("div", class_=re.compile("chakra-stack"))[5]
    question_stacks = []
    start = False
    for stack in content_stack.contents:
        if start:
            question_stacks.append(stack)
        if "chakra-divider" in stack.attrs["class"]:
            start = True

    current_question = None

    current_user = None
    current_answer = None

    print(group.name, issue_number, sent_at)
    for question_stack in question_stacks:
        actual_stack = [question_stack]
        if question_stack.contents[0].string == "✨ Questions":
            actual_stack = question_stack.contents[1]
        for q_stack in actual_stack:
            q = _parse_question(db, letter, q_stack)
    return letter


def _parse_question(db: Session, letter: Letter, question_stack: Tag) -> Question:
    if not question_stack.contents:
        return
    author_name = None
    if not question_stack.contents[0].string:
        author_name, question_text = _parse_asked_question_text(
            question_stack.contents[0]
        )
    else:
        question_text: str = question_stack.contents[0].string
    print(author_name, question_text)

    author_user = (
        None
        if not author_name
        else db.scalars(select(User).where(User.name == author_name)).one_or_none()
    )
    current_question = letter_crud.add_question(
        db,
        letter,
        question_text,
        author_user,
    )
    db.add(current_question)

    # parse responses from question_stack.contents[1:]
    if len(question_stack.contents) == 2:
        response_stack = question_stack.contents[1]
    else:
        response_stack = question_stack.contents[1:]

    for stack in response_stack:
        url = None
        if question_text == "📸 Photo Wall":
            assert stack.contents[0].name == "img"
            url = stack.contents[0].get("src")
            second_content_text = stack.contents[1].text.split(": ")
            author = second_content_text[0]
            response_text = "\n".join(second_content_text[1:])
        elif len(stack.contents) > 1:
            # first content is the user and response
            first_content = stack.contents[0]
            author = first_content.contents[0].string
            response_text = ""
            idx = 2
            while first_content.contents[idx].name != "button":
                if (
                    not first_content.contents[idx].string
                    and not first_content.contents[idx].contents
                ):
                    break
                curr_str = (
                    first_content.contents[idx].string
                    or first_content.contents[idx].contents[0].string
                )
                if curr_str and response_text:
                    response_text += f"\n{curr_str}"
                elif curr_str:
                    response_text += curr_str
                idx += 1
            # second content is the image
            if stack.contents[1].name == "img":
                url = stack.contents[1].get("src")
        else:
            first_content = stack.contents[0]
            author = first_content.contents[0].string
            response_text = ""
            idx = 2
            while first_content.contents[idx].name != "button":
                if (
                    not first_content.contents[idx].string
                    and not first_content.contents[idx].contents
                ):
                    break
                curr_str = (
                    first_content.contents[idx].string
                    or first_content.contents[idx].contents[0].string
                )
                if curr_str and response_text:
                    response_text += f"\n{curr_str}"
                elif curr_str:
                    response_text += curr_str
                idx += 1
        print([author])
        # print([m.name for m in letter.group.members])
        [current_user] = [m for m in letter.group.members if m.name == author.strip()]
        response = question_crud.add_response(
            db, current_question, current_user, response_text
        )
        db.add(response)
        if url:
            with tempfile.SpooledTemporaryFile() as f:
                f.write(requests.get(url).content)
                f.seek(0)
                upload_result = upload_image(db, response, [f])

    return current_question


def _parse_asked_question_text(question: PageElement) -> tuple[str | None, str]:
    author_name = None
    parts = question.contents[0].contents
    if len(parts) > 1:
        if not parts[0].string:
            author_name = question.contents[0].text.split(" asked:")[0]
        else:
            author_name = parts[0].string.split(" asked:")[0]
    return author_name, parts[-1].string


async def upload(db: Session, response: Response, url: str):
    upload_result = await upload_image(db, response, url)
    print(upload_result)
