from __future__ import annotations

# from .task import *
# from .schedule import *
# from .user import *
# from .response import *
# from .question import *
# from .letter import *
# from .group import *
from .linked_schemas import *

GroupLinked.model_rebuild()
LetterLinked.model_rebuild()
QuestionLinked.model_rebuild()
ResponseLinked.model_rebuild()
UserLinked.model_rebuild()
ScheduleUnlinked.model_rebuild()
# TaskLinked.model_rebuild()
