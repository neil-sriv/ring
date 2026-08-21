"""Shared warm-paper HTML shell for Ring emails.

Email clients cannot read the frontend's CSS variables, so the design tokens
from react/src/app.css are mirrored here as hex values. Keep the two in sync
when the palette changes (see docs/design-system.md, "Email" section).

All helpers return HTML strings with inline styles and table layout so they
render consistently across email clients. Interpolated user content must be
escaped by the caller unless a helper documents otherwise.
"""

from __future__ import annotations

import html

# Warm-paper palette (mirrors react/src/app.css @theme tokens)
PAPER_BG = "#fbfaf7"  # --color-background
CARD_BG = "#ffffff"  # --color-card
INK = "#3a3631"  # --color-foreground
MUTED_INK = "#746d64"  # --color-muted-foreground
BORDER = "#e5e2dc"  # --color-border
PRIMARY = "#ba512c"  # --color-primary (terracotta)
PRIMARY_FG = "#fdfcf9"  # --color-primary-foreground

SERIF = "Georgia, 'Times New Roman', serif"
SANS = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, "
    "sans-serif"
)


def render_link(url: str, label: str | None = None) -> str:
    """Render a terracotta inline link. Escapes the URL and label."""
    escaped_url = html.escape(url, quote=True)
    text = html.escape(label) if label else escaped_url
    return (
        f'<a href="{escaped_url}" '
        f'style="color:{PRIMARY};text-decoration:underline;">{text}</a>'
    )


def render_button(label: str, url: str) -> str:
    """Render a bulletproof terracotta button. Escapes the URL and label."""
    return f"""
<table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:24px 0 4px;">
  <tr>
    <td style="border-radius:6px; background-color:{PRIMARY};">
      <a href="{html.escape(url, quote=True)}" style="display:inline-block; padding:10px 22px; font-family:{SANS}; font-size:14px; font-weight:600; color:{PRIMARY_FG}; text-decoration:none; border-radius:6px;">{html.escape(label)}</a>
    </td>
  </tr>
</table>
"""


def render_paragraph(inner_html: str) -> str:
    """Render a body paragraph. Caller escapes any user content."""
    return (
        f'<p style="margin:16px 0 0; font-family:{SANS}; font-size:14px; '
        f'line-height:1.6; color:{INK};">{inner_html}</p>'
    )


def render_muted_line(inner_html: str) -> str:
    """Render a small muted line (fallback URLs, fine print)."""
    return (
        f'<p style="margin:12px 0 0; font-family:{SANS}; font-size:12px; '
        f'line-height:1.6; color:{MUTED_INK};">{inner_html}</p>'
    )


def render_email_shell(
    *,
    title: str,
    content_html: str,
    eyebrow: str | None = None,
    preheader: str | None = None,
    footer_note: str = "You are receiving this email because you have a Ring account.",
) -> str:
    """Wrap content in the standard Ring email frame.

    Warm paper canvas, centered serif "Ring" wordmark, a white card with a
    serif title, and a muted footer. `title`, `eyebrow`, `preheader`, and
    `footer_note` are treated as plain text and escaped here; `content_html`
    is trusted HTML from the render helpers.
    """
    escaped_title = html.escape(title)
    preheader_html = (
        (
            '<span style="display:none; max-height:0; overflow:hidden; '
            f'mso-hide:all;">{html.escape(preheader)}</span>'
        )
        if preheader
        else ""
    )
    eyebrow_html = (
        (
            f'<div style="margin:0 0 8px; font-family:{SANS}; font-size:12px; '
            "font-weight:600; letter-spacing:0.08em; text-transform:uppercase; "
            f'color:{MUTED_INK};">{html.escape(eyebrow)}</div>'
        )
        if eyebrow
        else ""
    )
    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{escaped_title}</title>
  </head>
  <body style="margin:0; padding:0; background-color:{PAPER_BG};">
    {preheader_html}
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:{PAPER_BG};">
      <tr>
        <td align="center" style="padding:32px 16px;">
          <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width:600px;">
            <tr>
              <td align="center" style="padding:0 0 20px;">
                <span style="font-family:{SERIF}; font-size:26px; font-weight:600; letter-spacing:-0.02em; color:{INK};">Ring</span>
              </td>
            </tr>
            <tr>
              <td style="background-color:{CARD_BG}; border:1px solid {BORDER}; border-radius:12px; padding:28px;">
                {eyebrow_html}
                <h1 style="margin:0; font-family:{SERIF}; font-size:24px; line-height:1.3; font-weight:600; letter-spacing:-0.01em; color:{INK};">{escaped_title}</h1>
                {content_html}
              </td>
            </tr>
            <tr>
              <td align="center" style="padding:20px 8px 0;">
                <p style="margin:0; font-family:{SANS}; font-size:12px; line-height:1.6; color:{MUTED_INK};">{html.escape(footer_note)}</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""
