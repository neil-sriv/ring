from __future__ import annotations
from typing import TYPE_CHECKING, Sequence

import boto3
from fastapi import HTTPException, UploadFile

from ring.config import get_config
from ring.crud import api_identifier as api_identifier_crud
from ring.dependencies import get_s3_client_dependencies
from ring.postgres_models.letter_model import Letter
from ring.postgres_models.response_model import ImageResponseAssociation, Response
from ring.postgres_models.s3_model import Image
from ring.pydantic_schemas.response import Response as ResponseUpdate

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_response(db: Session, response_api_id: str) -> Response:
    return api_identifier_crud.get_model(db, Response, api_id=response_api_id)


def get_responses(
    db: Session, letter: Letter, response_api_ids: list[str]
) -> list[Response]:
    responses = api_identifier_crud.get_models(db, Response, response_api_ids)
    assert all(response.question.letter_id == letter.id for response in responses)
    return responses


def edit_responses(
    response_map: dict[str, Response],
    updated_responses: Sequence[ResponseUpdate],
) -> list[Response]:
    for updated_resp in updated_responses:
        db_response = response_map[updated_resp.api_identifier]
        db_response.response_text = updated_resp.response_text
    return list(response_map.values())


def add_image_to_response(
    db: Session,
    response: Response,
    image: Image,
) -> Response:
    assoc = ImageResponseAssociation(image=image, response=response)
    response.image_associations.append(assoc)
    db.add(response)
    db.commit()
    return response


async def upload_image(
    db: Session,
    response: Response,
    response_images: list[UploadFile],
) -> Response:
    s3_file_path = f"{response.question.letter.group.api_identifier}/{response.question.letter.api_identifier}/{response.api_identifier}.png"
    # upload image to S3
    client = await get_s3_client_dependencies()
    for image_file in response_images:
        client.upload_fileobj(
            image_file.file,
            get_config().BUCKET_NAME,
            s3_file_path,
        )

    # Update response with _image_file S3 path
    image = Image.create(s3_url=s3_file_path)
    add_image_to_response(db, response, image)

    return response
