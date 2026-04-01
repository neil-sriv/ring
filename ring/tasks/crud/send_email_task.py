"""Utilities for constructing letter send email tasks.

This module provides functions for creating email drafts that contain letter content,
including questions and responses with optional images. The emails are formatted
in both HTML and plain text versions.
"""

from __future__ import annotations

from ring.email_util import EmailDraft, construct_email_draft


def construct_question_html(
    question: str, responses: list[tuple[str, list[str]]]
) -> str:
    """Construct HTML for a question and its responses.

    Args:
        question: The question text
        responses: List of tuples containing (response text, list of image URLs)

    Returns:
        str: HTML string containing the formatted question and responses
    """
    return """
<div style="margin-top: 24px;">
  <h2 style="margin: 0 0 8px; font-size: 18px; line-height: 1.4; color: #2d3748;">
    {question}
  </h2>
  <ul style="margin: 0; padding: 0;">
    {responses}
  </ul>
</div>
""".format(
        question=question,
        responses="".join(
            [construct_response_html(response) for response in responses]
        ),
    )


def construct_response_html(response: tuple[str, list[str]]) -> str:
    """Construct HTML for a single response with optional images.

    Args:
        response: Tuple containing (response text, list of image URLs)

    Returns:
        str: HTML string containing the formatted response and images
    """
    image_htmls = "".join(
        [
            (
                '<img src="{url}" alt="Image" '
                'style="display:block; margin:8px 0 0; width:auto; '
                'height:auto; max-width:100%; border-radius:6px;" />'
            ).format(url=url)
            for url in response[1]
        ]
    )
    return """
<li style="margin-bottom: 12px; list-style: none;">
  <div style="padding: 12px 14px; border-radius: 8px; border: 1px solid #e2e8f0; background-color: #ffffff;">
    <p style="margin: 0; font-size: 15px; line-height: 1.5; color: #1a202c;">{text}</p>
    {images}
  </div>
</li>
""".format(
        text=response[0],
        images=image_htmls,
    )


def construct_question_text(
    question: str, responses: list[tuple[str, list[str]]]
) -> str:
    """Construct plain text version of a question and its responses.

    Args:
        question: The question text
        responses: List of tuples containing (response text, list of image URLs)

    Returns:
        str: Plain text string containing the question and responses
    """
    return (
        f"{question}:\n"
        + "\n".join([response[0] for response in responses])
        + "\n\n"
    )


def construct_send_letter_email(
    recipients: list[str],
    title: str,
    letter_api_id: str,
    letter_dict: dict[str, list[tuple[str, list[str]]]],
) -> EmailDraft:
    """Construct an email draft containing a complete letter.

    Creates an email draft with all questions and responses from a letter,
    formatted in both HTML and plain text versions. The HTML version includes
    images and proper formatting, while the plain text version serves as a
    fallback for non-HTML email clients.

    Args:
        recipients: List of email addresses to send to
        letter_number: The sequential number of this letter
        group_name: Name of the group
        letter_api_id: API identifier of the letter
        letter_dict: Dictionary mapping questions to lists of responses

    Returns:
        EmailDraft: A draft email ready to be sent
    """
    question_text = "".join(
        construct_question_text(q, r) for q, r in letter_dict.items()
    )

    question_html = "".join(
        construct_question_html(q, r) for q, r in letter_dict.items()
    )

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = question_text

    # The HTML body of the email.
    BODY_HTML = """
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
  </head>
  <body style="margin:0; padding:0; background-color:#edf2f7;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%%" style="background-color:#edf2f7; padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%%" style="max-width:640px; background-color:#ffffff; border-radius:12px; border:1px solid #e2e8f0; overflow:hidden;">
            <tr>
              <td style="padding:20px 24px 12px; background-color:#2b6cb0; color:#ffffff;">
                <div style="font-size:13px; letter-spacing:0.08em; text-transform:uppercase; opacity:0.9;">Ring Newsletter</div>
                <h1 style="margin:6px 0 0; font-size:22px; line-height:1.3; font-weight:600;">{title}</h1>
              </td>
            </tr>
            <tr>
              <td style="padding:20px 24px 8px;">
                <p style="margin:0 0 12px; font-size:14px; line-height:1.5; color:#4a5568;">
                  You can also read and share this newsletter online:
                </p>
                <p style="margin:0 0 4px;">
                  <a href="http://ring.neilsriv.tech/loops/{letter_api_id}" style="color:#2b6cb0; text-decoration:underline; font-size:14px;">http://ring.neilsriv.tech/loops/{letter_api_id}</a>
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 24px 24px;">
                {question_html}
              </td>
            </tr>
            <tr>
              <td style="padding:16px 24px 20px; border-top:1px solid #e2e8f0; background-color:#f7fafc;">
                <p style="margin:0; font-size:12px; line-height:1.5; color:#a0aec0;">
                  You are receiving this email as a member of a Ring loop.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".format(
        title=title,
        letter_api_id=letter_api_id,
        question_html=question_html,
    )

    # Try to send the email.
    subject = title
    email_draft = construct_email_draft(
        recipients, subject, BODY_HTML, BODY_TEXT
    )

    return email_draft
