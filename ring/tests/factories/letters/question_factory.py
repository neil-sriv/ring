import factory

from ring.letters.models.question_model import Question
from ring.tests.factories.base_factory import BaseFactory, register_factory


@register_factory
class QuestionFactory(BaseFactory[Question]):
    class Meta:
        model = Question

    question_text = factory.Faker(
        "pystr_format", string_format="Question-{{random_int}}"
    )
    letter = factory.SubFactory(
        "ring.tests.factories.letters.letter_factory.LetterFactory"
    )
    author = None
