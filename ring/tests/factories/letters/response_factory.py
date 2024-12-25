import factory

from ring.letters.models.response_model import Response
from ring.tests.factories.base_factory import BaseFactory, register_factory


@register_factory
class ResponseFactory(BaseFactory[Response]):
    class Meta:
        model = Response

    response_text = factory.Faker(
        "pystr_format", string_format="Response-{{random_int}}"
    )
    participant = factory.SubFactory(
        "ring.tests.factories.parties.user_factory.UserFactory"
    )
    question = factory.SubFactory(
        "ring.tests.factories.letters.question_factory.QuestionFactory"
    )
