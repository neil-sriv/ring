# Sign in

Sign in lets a person with an account open Ring, land on Home, and sign back
out. A wrong password stays on the login page and shows the API's error.

## Sub-features

- `auth-open` shows the login form at `/login`.
- `auth-success` accepts the seeded user and opens Home.
- `auth-reject` keeps a wrong password on the login page.
- `auth-logout` returns to the login page.
- `auth-api` issues a bearer token through nginx.

## How to get to it (user POV)

- Open `http://localhost:5173/login`.
- Choose `Ring` in the sidebar and follow a redirect to `/login` after logging out.
- Submit the login form. The API equivalent is `POST /login/access-token`.

## Driving it

Preconditions:

- `=== verify-ring ready ===` has been printed for this run.
- `doctor.sh` passed.
- The seeded user is `test@example.com` / `testpassword123`, display name
  `Test User`.

- **Open login.** Open `http://localhost:5173/login`. The heading reads
  `Welcome back`. A textbox named `Email` (`#username`), a textbox named
  `Password` (`#password`), and a button named `Sign In` are visible. The
  wordmark link reads `Ring`.
- **Reject bad password.** Fill `Email` with `test@example.com` and `Password`
  with `not-the-password`, then choose `Sign In`. The URL stays on `/login`.
  The page shows `Incorrect username or password` (the API detail string, not
  the word "email"). Screenshot
  `$EVIDENCE_DIR/auth-login/rejected.png`.
- **Sign in.** Fill `Email` with `test@example.com` and `Password` with
  `testpassword123`, then choose `Sign In`. The app navigates to `/`. The
  heading matches `Good morning, Test`, `Good afternoon, Test`, or
  `Good evening, Test`. The sidebar shows `test@example.com`. Sidebar links
  expose their shortcuts in the accessible name: `Home g h`, `Groups g g`,
  `Search g s`, `Settings g p`. A fresh user also sees `No letters yet`. If a
  banner offers `Enable notifications` and `Not now`, choose `Not now`.
  Screenshot `$EVIDENCE_DIR/auth-login/home.png`.
- **Confirm the account row.** Run:
  ```bash
  bash .cursor/skills/verify-ring/scripts/db-query.sh \
    "SELECT api_identifier, email, name FROM \"user\" WHERE email = 'test@example.com'"
  ```
  One row, email `test@example.com`, name `Test User`. Do not select
  `hashed_password`.
- **Token through nginx.** Run:
  ```bash
  bash .cursor/skills/verify-ring/scripts/api.sh POST /login/access-token \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d 'username=test@example.com&password=testpassword123' \
    -o /tmp/verify-ring/owner-login.json
  chmod 600 /tmp/verify-ring/owner-login.json
  ```
  HTTP 200. JSON has `token_type` `bearer` and a non-empty `access_token`.
  Record the status in `$EVIDENCE_DIR/auth-login/token.txt`. Do not copy the
  token into evidence. Then:
  ```bash
  token="$(python3 -c 'import json; print(json.load(open("/tmp/verify-ring/owner-login.json"))["access_token"])')"
  bash .cursor/skills/verify-ring/scripts/api.sh GET /parties/me \
    -H "Authorization: Bearer ${token}" \
    -o "$EVIDENCE_DIR/auth-login/me.json"
  ```
  HTTP 200. `email` is `test@example.com`.
- **Log out.** Choose the button named `Log out` (the sidebar control whose
  visible icon is a logout glyph; the accessible name is `Log out`). The URL
  is `/login` and the heading is `Welcome back`. Screenshot
  `$EVIDENCE_DIR/auth-login/logged-out.png`.

## Gotchas

- The password field's eye icon has no accessible name. Do not click it;
  clicking it flips the input type and can drop a filled value.
- Sidebar link accessible names include the shortcut (`Groups g g`, not
  `Groups`). A substring match on `Groups` also hits Home's `View groups`
  link.
- Home may show a push banner (`Enable notifications` / `Not now`) from
  `PushOfferBanner`. Dismiss it with `Not now`. It is not part of sign-in.
- The API says `Incorrect username or password` even though the label is
  `Email`. Assert that string.
- An already-authenticated visit to `/login` redirects to `/`. Log out before
  proving `auth-reject`.
- `https://localhost/login` is nginx's static `react/dist`, not the Vite app.
  Use `http://localhost:5173/login`.
- A 200 from `/login/access-token` is not proof of a session until `/parties/me`
  returns the same email and Home shows that address.
