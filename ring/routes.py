from fastapi import APIRouter


from ring.api import authn, user, group, letter, schedule

router = APIRouter()

router.include_router(authn.router, tags=["login"])
router.include_router(user.router, prefix="/parties", tags=["parties"])
router.include_router(group.router, prefix="/parties", tags=["parties"])
router.include_router(letter.router, prefix="/letters", tags=["letters"])
router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])


@router.get("/")
async def root():
    return {"message": "Hello World!"}


@router.get("/hello")
async def hello():
    return {"message": "Hello World!"}
