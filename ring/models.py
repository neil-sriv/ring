from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    ListAttribute,
    MapAttribute,
)
from ring.fast import ring_config


class Member(MapAttribute[str, UnicodeAttribute]):
    member_id = UnicodeAttribute()
    member_name = UnicodeAttribute()


class MediaContent(MapAttribute[str, UnicodeAttribute]):
    media_id = UnicodeAttribute()
    media_type = UnicodeAttribute()
    media_url = UnicodeAttribute()


class Response(MapAttribute[str, UnicodeAttribute | MediaContent]):
    response_id = UnicodeAttribute()
    response_text = UnicodeAttribute()
    member_name = UnicodeAttribute()
    media_content = MediaContent()


class Question(MapAttribute[str, UnicodeAttribute | ListAttribute[Response]]):
    question_id = UnicodeAttribute()
    question_text = UnicodeAttribute()
    responses = ListAttribute(of=Response)


class Letter(MapAttribute[str, UnicodeAttribute | ListAttribute[Question]]):
    letter_id = UnicodeAttribute()
    issue_number = NumberAttribute()
    questions = ListAttribute(of=Question)


class GroupModel(Model):
    class Meta:  # type: ignore
        host = ring_config.dynamo_db_host
        table_name = "group"
        region = "us-west-2"

    group_id = UnicodeAttribute(hash_key=True)
    group_name = UnicodeAttribute()
    members = ListAttribute(of=Member)
    letters = ListAttribute(of=Letter)
