from fastapi import APIRouter


from ring.auth.api import authn
from ring.letters.api import letter, question, response
from ring.parties.api import group, user, invite
from ring.tasks.api import schedule

router = APIRouter()

router.include_router(authn.router, tags=["login"])
router.include_router(user.router, prefix="/parties", tags=["parties"])
router.include_router(group.router, prefix="/parties", tags=["parties"])
router.include_router(letter.router, prefix="/letters", tags=["letters"])
router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
router.include_router(question.router, prefix="/questions", tags=["questions"])
router.include_router(response.router, prefix="/responses", tags=["responses"])
router.include_router(invite.router, prefix="/invites", tags=["invites"])


@router.get("/")
async def root():
    return {"message": "Hello World!"}


@router.get("/hello")
async def hello():
    return {"message": "Hello World!"}
