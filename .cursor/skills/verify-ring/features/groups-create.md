# Create a group

Create a group lets a signed-in person name a circle they will write letters
with. The new group shows up in the groups list and as a row in the database.
A second account that is not a member is denied by the authz helpers.

## Sub-features

- `groups-open` opens the groups list.
- `groups-create-empty` creates a group from the empty-state button.
- `groups-create-add` creates a group from the navbar button after one exists.
- `groups-create-home` creates a group from Home while the user has none.
- `groups-persist` shows the group again after a reload, with a matching row.
- `groups-authz-deny` returns 403 from `load_and_check` for a non-member.

## How to get to it (user POV)

- Choose `Groups` in the sidebar. The page heading is `Groups`.
- On that page, with no groups yet, choose `Create group` in the dashed empty
  state (`No groups yet`).
- On that page, choose `Add Group`. That button is in the navbar and stays
  after groups exist.
- On Home, while the account has no groups, choose `Create a group` under
  `No letters yet`.
- All three buttons open a dialog titled `Add Group`.

## Driving it

Preconditions:

- `doctor.sh` passed after launch.
- `RUN_ID` is the value in `/tmp/verify-ring/state.env`.
- `test@example.com` has no group whose name starts with `Verify-`. If a
  previous run left those rows, use a new `RUN_ID` in the names below; do not
  rename the journey to fit leftover data.
- The outsider email `verify-outsider-<RUN_ID>@example.com` is not registered
  yet.

- **Open groups as the seeded user.** Sign in as `test@example.com` /
  `testpassword123` (see [auth-login.md](./auth-login.md) `auth-success`).
  If the push banner is up, choose `Not now`. Choose the sidebar link whose
  accessible name is `Groups g g`. Do not choose Home's `View groups` link.
  The heading is `Groups`. With zero groups the page shows `No groups yet`,
  a button named `Create group`, and a button named `Add Group`.
- **Empty-state entry.** Choose `Create group`. A dialog named `Add Group`
  appears with a textbox named `Name` and a button named `Save`. Wait until
  `Save` is enabled (it stays disabled until `/parties/me` has loaded). Fill
  `Name` with `Verify-empty-<RUN_ID>` and choose `Save`. The dialog closes.
  The groups table contains a link named `Verify-empty-<RUN_ID>`. Screenshot
  `$EVIDENCE_DIR/groups-create/empty-entry.png`. The toast
  `Group created successfully.` is not the proof.
- **Navbar entry.** Choose `Add Group`. The same dialog opens. Fill `Name`
  with `Verify-add-<RUN_ID>` and choose `Save`. The table lists both names.
  The empty state `No groups yet` is gone, so `Create group` is gone too.
  Screenshot `$EVIDENCE_DIR/groups-create/add-entry.png`.
- **Reload.** Reload `http://localhost:5173/groups`. Both links are still
  there.
- **Rows for the seeded user.** Run:
  ```bash
  bash .cursor/skills/verify-ring/scripts/db-query.sh \
    "SELECT g.api_identifier, g.name, u.email
     FROM \"group\" g
     JOIN \"user\" u ON u.id = g.admin_id
     WHERE g.name IN ('Verify-empty-<RUN_ID>', 'Verify-add-<RUN_ID>')
     ORDER BY g.name"
  ```
  Two rows. Both emails are `test@example.com`. Save this output to
  `$EVIDENCE_DIR/groups-create/owner-groups.txt`. Keep the `api_identifier`
  of `Verify-empty-<RUN_ID>` as `GROUP_API_ID`.
- **Register the outsider.** Run:
  ```bash
  bash .cursor/skills/verify-ring/scripts/api.sh POST /parties/user \
    -H 'Content-Type: application/json' \
    -d '{"name":"Verify Outsider","email":"verify-outsider-<RUN_ID>@example.com","password":"verify-outsider-pass"}'
  ```
  HTTP 201. This is the same public create used by `dev_util/cloud-seed.sh`.
  Read `email` from the response. `POST /parties/user` stores an `EmailStr`,
  which lowercases the address (`T` and `Z` in `<RUN_ID>` become `t` and `z`).
  Login compares that stored string exactly, so sign in with the response
  email, not the request casing.
- **Home entry, outsider.** Choose the sidebar button named `Log out`.
  Sign in with that stored email and password `verify-outsider-pass`. Dismiss
  `Not now` if the push banner is shown. Home shows
  `Good morning, Verify`, `Good afternoon, Verify`, or `Good evening, Verify`,
  plus `No letters yet` and a button named `Create a group`. Choose
  `Create a group`. In the `Add Group` dialog, fill `Name` with
  `Verify-home-<RUN_ID>` and choose `Save`. Choose the sidebar link
  `Groups g g` and confirm the link `Verify-home-<RUN_ID>` is listed.
  `Verify-empty-<RUN_ID>` is not listed
  for this account. Screenshot `$EVIDENCE_DIR/groups-create/home-entry.png`.
- **Outsider row.** Run the same SQL shape for `Verify-home-<RUN_ID>`. One
  row, email `verify-outsider-<RUN_ID>@example.com`. Save it to
  `$EVIDENCE_DIR/groups-create/outsider-group.txt`.
- **Authz deny.** Take bearer tokens for both users with
  `POST /login/access-token` (form body `username` and `password`). Store them
  only in `/tmp/verify-ring/owner.token` and `/tmp/verify-ring/outsider.token`
  (mode `0600`). Count letters on the empty-state group:
  ```bash
  bash .cursor/skills/verify-ring/scripts/db-query.sh \
    "SELECT count(*) AS letters
     FROM letter l
     JOIN \"group\" g ON g.id = l.group_id
     WHERE g.api_identifier = '<GROUP_API_ID>'"
  ```
  Record the count. Then, as the outsider:
  ```bash
  bash .cursor/skills/verify-ring/scripts/api.sh GET \
    "/spotify/groups/<GROUP_API_ID>/playlist" \
    -H "Authorization: Bearer $(cat /tmp/verify-ring/outsider.token)" \
    -D "$EVIDENCE_DIR/groups-create/outsider-authz.headers" \
    -o "$EVIDENCE_DIR/groups-create/outsider-authz.json"
  ```
  HTTP 403. Body is
  `{"detail":"Not authorized to access this resource"}`. That string is the
  `PermissionError` mapping in `ring/fastapp/fast.py` for `load_and_check` on
  `GET /spotify/groups/{group_api_id}/playlist`. A 401 means the token was
  missing. A 404 `Group not found` is the membership check on
  `GET /parties/group/{id}`, which does not use the authz helpers; do not
  accept it as this proof.
- **Member passes the same helper.** Repeat the playlist GET with the seeded
  user's token. HTTP status is 200, 404, 409, or 503, and the body detail is
  not `Not authorized to access this resource`. Save status and body to
  `$EVIDENCE_DIR/groups-create/member-authz.txt`. Spotify is optional in local
  dev: 404 `no_spotify_playlist`, 409 `spotify_not_linked`, and 503
  `Spotify linking is unavailable` all mean `load_and_check` allowed the
  member. Those statuses are not a failed deny-check.
- **No row from the deny.** Re-run the letter count for `<GROUP_API_ID>`.
  It is unchanged. Save both counts to
  `$EVIDENCE_DIR/groups-create/letter-counts.txt`.

## Gotchas

- Group names are unique across the whole database. Include `<RUN_ID>`.
- The create-user response email is lowercased. Signing in with the original
  `<RUN_ID>` casing returns `Incorrect username or password`.
- `Create group` (groups empty state) and `Create a group` (Home) are
  different buttons, and each disappears after that user has a group. Driving
  Home after the seeded user already created a group does not cover the Home
  button. Use the outsider, who still has zero groups, for `groups-create-home`.
- `Save` in the dialog is disabled until the current user query resolves.
  Clicking it early no-ops.
- `GET /parties/group/<GROUP_API_ID>` as the outsider returns 404
  `Group not found`, not the authz 403. The deny check is the Spotify playlist
  route because that handler calls `load_and_check` before any Spotify I/O.
- `POST /letters/letter:CYCLIC` also calls `load_and_check`, but a member
  request creates a letter. Do not use it as the deny probe.
- The toast is not persistence. Reload `/groups` and read `"group"`.
