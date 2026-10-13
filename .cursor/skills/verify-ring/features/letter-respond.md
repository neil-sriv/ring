# Respond to a letter

Respond to a letter lets a group admin start the next loop, open it for
answers, and save a reply on a question. The reply is still there after a
reload and as a `response` row.

## Sub-features

- `letter-start` creates the next cyclic loop from the group page.
- `letter-upcoming-locked` shows questions that cannot be answered yet.
- `letter-in-progress` opens the loop so replies can be typed.
- `letter-answer` saves text on `🌤️ One Good Thing`.
- `letter-persist` shows that text after a reload and in the database.

## How to get to it (user POV)

- Open a group from `Groups` (the group name is a link to
  `/groups/<group id>/loops`).
- Choose `Start Next Loop`, set `Send at`, and choose `Save`. The dialog
  title is `Start Next Loop`.
- Open the issue card (the link whose name contains `Issue #1` when the loop
  has no title).
- Choose `Edit Loop`, switch status to `In Progress`, and choose `Save`.
- Type in the box whose placeholder is `Type your response...` under the
  question `🌤️ One Good Thing`.

## Driving it

Preconditions:

- `doctor.sh` passed.
- Signed in as `test@example.com`, the admin of a group created in this run
  (the `Verify-empty-<RUN_ID>` group from [groups-create.md](./groups-create.md)
  is the one to use).
- That group has no cyclic loop yet. `Start Next Loop` is enabled only when
  the group has no upcoming cyclic loop. If the button reads
  `Upcoming loop scheduled` and is disabled, this journey's precondition is
  unmet: report that, and do not flip a different group's letter to make the
  button appear.

- **Open the group.** From `Groups`, choose the link
  `Verify-empty-<RUN_ID>`. The heading is that group name. Tabs include
  `Loops`, `Adhoc Loops`, `Store`, and `Documents`. The Loops tab shows
  `No loops yet` and a button named `Start Next Loop`.
- **Start the loop.** Choose `Start Next Loop`. A dialog named
  `Start Next Loop` appears with a field named `Send at` (`#sendAt`,
  `datetime-local`, already filled with a future time) and a button named
  `Save`. Leave the filled time and choose `Save`. The dialog closes. An
  `Upcoming Issues` section appears with a link whose name contains
  `Issue #1`. Screenshot `$EVIDENCE_DIR/letter-respond/upcoming.png`.
- **Upcoming is locked.** Open that `Issue #1` link. The page shows the group
  name, the heading `Issue #1`, and a button named `Edit Loop`. Questions
  include `📸 Photo Wall`, `🌤️ One Good Thing`, `💭 On Your Mind`, and
  `👀 Check it Out`, plus three questions drawn from the bank. The response
  boxes are disabled and there is no `Saved` status. Do not type into them.
  Screenshot `$EVIDENCE_DIR/letter-respond/locked.png`.
- **Open for replies.** Choose `Edit Loop`. The dialog title is `Edit Loop`.
  The status control is a checkbox named `Status` (`#isInProgress`). Check it
  so the adjacent text `In Progress` is the emphasized side, then choose
  `Save`. The dialog closes. The issue page shows a line beginning with
  `Due`. Screenshot `$EVIDENCE_DIR/letter-respond/in-progress.png`.
- **Answer.** Under the heading `🌤️ One Good Thing`, fill the textbox whose
  placeholder is `Type your response...` with
  `Verify reply <RUN_ID>`. Wait until a status reads `Saved` (it appears
  after the one-second debounce, following `Saving...`). Do not navigate
  away before `Saved`. Screenshot
  `$EVIDENCE_DIR/letter-respond/saved.png`.
- **Reload.** Reload the issue URL. The same textbox still contains
  `Verify reply <RUN_ID>`. Screenshot
  `$EVIDENCE_DIR/letter-respond/reloaded.png`.
- **Row.** Run:
  ```bash
  bash .cursor/skills/verify-ring/scripts/db-query.sh \
    "SELECT r.api_identifier, r.response_text, u.email, q.question_text
     FROM response r
     JOIN \"user\" u ON u.id = r.participant_id
     JOIN question q ON q.id = r.question_id
     WHERE u.email = 'test@example.com'
       AND q.question_text = '🌤️ One Good Thing'
       AND r.response_text = 'Verify reply <RUN_ID>'"
  ```
  One row. Save the output to `$EVIDENCE_DIR/letter-respond/response-row.txt`.
- **Letter through nginx.** Read the issue id from the URL (`lttr_...`) and:
  ```bash
  bash .cursor/skills/verify-ring/scripts/api.sh GET /letters/letter/<LETTER_API_ID> \
    -H "Authorization: Bearer $(cat /tmp/verify-ring/owner.token)" \
    -o "$EVIDENCE_DIR/letter-respond/letter.json"
  ```
  HTTP 200. The JSON includes `Verify reply <RUN_ID>` on the One Good Thing
  question. Strip any token if you copy the command into notes.

## Gotchas

- Upcoming loops render the textarea `disabled`. A typed value that never
  shows `Saved` was entered on the wrong issue (often the successor upcoming
  issue created when this one moved to `In Progress`). Answer on the issue
  whose page says `Due`.
- Promoting to `In Progress` also creates the next upcoming cyclic letter.
  The group page then has both `In Progress` (`Issue #1`) and
  `Upcoming Issues` (`Issue #2`). Open the in-progress card.
- Autosave waits one second after the last keystroke, then shows `Saving...`,
  then `Saved`. The placeholder switches to `Saving...` while the request is
  in flight. Wait for the status `Saved`, not a fixed sleep.
- `Edit Loop` is only rendered for the group admin, and only when the letter
  is not `SENT`.
- The three extra questions change every new letter. Assert
  `🌤️ One Good Thing`, which is one of the four default questions.
- `Start Next Loop` calls `POST /letters/letter`, which does not use
  `load_and_check`. The authz 403 probe stays in
  [groups-create.md](./groups-create.md). Do not replace this UI journey with
  that POST.
- A `Saved` status without the reload and the `response` row is not proof.
