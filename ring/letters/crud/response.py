from __future__ import annotations

import hashlib
import random
import string as string_lib
from typing import TYPE_CHECKING, Sequence

from fastapi import UploadFile

from ring.api_identifier import util as api_identifier_crud
from ring.config import get_config
from ring.dependencies import (
    a_get_s3_client_dependencies,
)
from ring.letters.models.letter_model import Letter
from ring.letters.models.response_model import (
    ImageResponseAssociation,
    Response,
)
from ring.letters.schemas.response import Response as ResponseUpdate
from ring.s3.models.s3_model import Image, MediaType

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_response(db: Session, response_api_id: str) -> Response:
    """Retrieve a specific response by its API identifier.

    :param db: Database session
    :param response_api_id: API identifier of the response
    :return: Response object
    :rtype: Response
    :raises IDNotFoundException: If response with given API ID is not found
    """
    return api_identifier_crud.get_model(db, Response, api_id=response_api_id)


def get_responses(
    db: Session, letter: Letter, response_api_ids: list[str]
) -> list[Response]:
    """Retrieve multiple responses for a letter by their API identifiers.

    :param db: Database session
    :param letter: Letter the responses belong to
    :param response_api_ids: List of response API identifiers
    :return: List of responses
    :rtype: list[Response]
    :raises AssertionError: If any response doesn't belong to the given letter
    :raises IDNotFoundException: If any response with given API ID is not found
    """
    responses = api_identifier_crud.get_models(db, Response, response_api_ids)
    assert all(
        response.question.letter_id == letter.id for response in responses
    )
    return responses


def edit_responses(
    response_map: dict[str, Response],
    updated_responses: Sequence[ResponseUpdate],
) -> list[Response]:
    """Update multiple responses with new text content.

    :param response_map: Dictionary mapping API IDs to Response objects
    :param updated_responses: Sequence of response updates
    :return: List of updated responses
    :rtype: list[Response]
    """
    for updated_resp in updated_responses:
        db_response = response_map[updated_resp.api_identifier]
        db_response.response_text = updated_resp.response_text
    return list(response_map.values())


def add_image_to_response(
    db: Session,
    response: Response,
    image: Image,
) -> Response:
    """Associate an image with a response.

    :param db: Database session
    :param response: Response to add the image to
    :param image: Image to associate with the response
    :return: Updated response
    :rtype: Response
    """
    assoc = ImageResponseAssociation(image=image, response=response)
    response.image_associations.append(assoc)
    db.add(response)
    return response


async def a_upload_image(
    db: Session,
    response: Response,
    response_images: list[UploadFile],
) -> Response:
    """Upload images to S3 and associate them with a response.

    :param db: Database session
    :param response: Response to add the images to
    :param response_images: List of image files to upload
    :return: Updated response with associated images
    :rtype: Response
    """
    s3_file_prefix = f"{response.question.letter.group.api_identifier}/{response.question.letter.api_identifier}/{response.api_identifier}/"
    # upload image to S3
    client = await a_get_s3_client_dependencies()
    for image_file in response_images:
        random_string = "".join(random.choices(string_lib.ascii_letters, k=12))
        s3_file_path = (
            s3_file_prefix
            + hashlib.sha1(bytearray(random_string, "utf-8")).hexdigest()
        )
        content_type = MediaType.IMAGE
        if image_file.content_type and "video" in image_file.content_type:
            content_type = MediaType.VIDEO

        client.upload_fileobj(
            image_file.file,
            get_config().BUCKET_NAME,
            s3_file_path,
        )

        # Update response with _image_file S3 path
        image = Image.create(s3_url=s3_file_path, media_type=content_type)
        add_image_to_response(db, response, image)

    return response


# def upload_image(
#     db: Session,
#     response: Response,
#     response_images: list[SpooledTemporaryFile],
# ) -> Response:
#     s3_file_prefix = f"{response.question.letter.group.api_identifier}/{response.question.letter.api_identifier}/{response.api_identifier}/"
#     random_string = "".join(random.choices(string_lib.ascii_letters, k=12))
#     s3_file_path = (
#         s3_file_prefix
#         + hashlib.sha1(bytearray(random_string, "utf-8")).hexdigest()
#     )
#     # upload image to S3
#     client = get_s3_client_dependencies()
#     for image_file in response_images:
#         client.upload_fileobj(
#             image_file,
#             get_config().BUCKET_NAME,
#             s3_file_path,
#         )

#     # Update response with _image_file S3 path
#     image = Image.create(s3_url=s3_file_path)
#     add_image_to_response(db, response, image)

#     return response
