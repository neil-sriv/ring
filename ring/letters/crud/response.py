"""CRUD operations for response management.

This module provides functions for managing responses to questions in letters,
including text responses and image attachments using AWS S3 for storage.
"""

from __future__ import annotations

import hashlib
import random
import string as string_lib
from typing import TYPE_CHECKING, Sequence

from fastapi import UploadFile

from ring.api_identifier import util as api_identifier_crud
from ring.fastapp.config import get_config
from ring.fastapp.dependencies import (
    get_s3_client_dependencies,
)
from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import (
    ImageResponseAssociation,
    Response,
)
from ring.letters.schemas.response import Response as ResponseUpdate
from ring.s3.models.s3_model import Image, MediaType
from ring.search.crud.hybrid_search import (
    create_hybrid_search_document,
    register_search_function,
)
from ring.search.models.hybrid_search import (
    HybridSearchDocument,
    SearchableType,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from ring.parties.models.user_model import User


def get_response(db: Session, response_api_id: str) -> Response:
    """Retrieve a specific response by its API identifier.

    Args:
        db (Session): Database session
        response_api_id (str): API identifier of the response

    Returns:
        Response: Response object

    Raises:
        IDNotFoundException: If response with given API ID is not found
    """
    return api_identifier_crud.get_model(db, Response, api_id=response_api_id)


def get_responses(
    db: Session, letter: Letter, response_api_ids: list[str]
) -> list[Response]:
    """Retrieve multiple responses for a letter by their API identifiers.

    Args:
        db (Session): Database session
        letter (Letter): Letter the responses belong to
        response_api_ids (list[str]): List of response API identifiers

    Returns:
        list[Response]: List of responses

    Raises:
        AssertionError: If any response doesn't belong to the given letter
        IDNotFoundException: If any response with given API ID is not found
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

    Args:
        response_map (dict[str, Response]): Dictionary mapping API IDs to Response objects
        updated_responses (Sequence[ResponseUpdate]): Sequence of response updates

    Returns:
        list[Response]: List of updated responses
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

    Args:
        db (Session): Database session
        response (Response): Response to add the image to
        image (Image): Image to associate with the response

    Returns:
        Response: Updated response
    """
    assoc = ImageResponseAssociation(image=image, response=response)
    response.image_associations.append(assoc)
    db.add(response)
    return response


async def upload_image(
    db: Session,
    response: Response,
    response_images: list[UploadFile],
) -> Response:
    """Upload images to S3 and associate them with a response.

    Args:
        db (Session): Database session
        response (Response): Response to add the images to
        response_images (list[UploadFile]): List of image files to upload

    Returns:
        Response: Updated response with associated images
    """
    s3_file_prefix = f"{response.question.letter.group.api_identifier}/{response.question.letter.api_identifier}/{response.api_identifier}/"
    # upload image to S3
    client = await get_s3_client_dependencies()
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


def create_response(
    db: Session,
    question: Question,
    user: User,
    response_text: str,
) -> Response:
    """Create a response.

    Args:
        db (Session): Database session
        question (Question): Question to add response to
        user (User): User creating the response
        response_text (str): Text content of the response

    Returns:
        Response: Newly created response
    """
    db_response = Response.create(user, question, response_text)
    db.add(db_response)
    db.add(create_response_search_document(db, db_response))
    return db_response


@register_search_function(SearchableType.RESPONSE, Response)
def create_response_search_document(
    db: Session, response: Response
) -> HybridSearchDocument:
    """Create a search document for a response.

    Args:
        db (Session): Database session
        response (Response): Response to create a search document for

    Returns:
        HybridSearchDocument: Search document for the response
    """
    raw_text = f"{response.response_text} {response.participant.name}"
    return create_hybrid_search_document(
        db, raw_text, response.api_identifier, SearchableType.RESPONSE
    )


def delete_image_from_response(
    db: Session,
    response: Response,
    s3_url: str,
) -> Response:
    """Delete an image from a response.

    Removes the image association and deletes the Image model row.
    The S3 file is not deleted to avoid data loss.

    Args:
        db (Session): Database session
        response (Response): Response containing the image
        image_id (int): ID of the image to delete

    Returns:
        Response: Updated response without the deleted image

    Raises:
        ValueError: If image is not found in the response
    """
    # Find the image association for this specific image
    image_association = None
    for assoc in response.image_associations:
        if assoc.image.s3_url == s3_url:
            image_association = assoc
            break

    if not image_association:
        raise ValueError(f"Image with S3 URL {s3_url} not found in response")

    # Remove the association from the response
    response.image_associations.remove(image_association)

    # Delete the image model (this will cascade to remove the association)
    db.delete(image_association.image)

    return response
