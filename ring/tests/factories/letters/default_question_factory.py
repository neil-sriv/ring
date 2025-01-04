import factory

from ring.letters.models.default_question_model import DefaultQuestion
from ring.tests.factories.base_factory import BaseFactory, register_factory


@register_factory
class DefaultQuestionFactory(BaseFactory[DefaultQuestion]):
    class Meta:
        model = DefaultQuestion

    question_text = factory.Faker(
        "pystr_format", string_format="DefaultQuestion-{{random_int}}"
    )
    group = factory.SubFactory(
        "ring.tests.factories.parties.group_factory.GroupFactory"
    )
