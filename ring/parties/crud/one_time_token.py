
from ring.parties.models.one_time_token_model import OneTimeToken


def _use_token(token: OneTimeToken) -> OneTimeToken:
    token.used = True
    return token