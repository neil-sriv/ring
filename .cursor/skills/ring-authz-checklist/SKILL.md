---
name: ring-authz-checklist
description: Apply Ring's Casbin-based authorization helpers when adding or modifying protected FastAPI routes. Use when introducing a new endpoint that touches user-scoped resources, bulk operations on groups or letters, or any code that loads a resource by `api_identifier` and then mutates or returns it.
---

# Ring authorization checklist

Ring uses a Casbin enforcer (see [ring/authz/](../../../ring/authz/)) with
policies in `ring/authz/policy.csv` and the model in `ring/authz/model.conf`.
Routes call helpers from
[ring/authz/authz.py](../../../ring/authz/authz.py) to load a resource by its
`api_identifier` and verify the current user has permission in one step.

## Helper reference

| Helper                       | Use it when                                                      |
|------------------------------|------------------------------------------------------------------|
| `load_and_check`             | Single resource read/write; want the loaded ORM instance back    |
| `bulk_load_and_check`        | Multiple resources by `api_identifier`; want only the authorized |
| `check`                      | Resource already loaded; raise on missing permission             |
| `can`                        | Boolean check without raising                                    |
| `filter_to_authorized`       | Drop unauthorized items from a list (silent filter)              |
| `bulk_can_or_inaccessible`   | Mark unauthorized items as `InaccessibleResource` instead of dropping |

All helpers accept the SQLAlchemy `Session`, the current `User`, an `Action`
from `ring.authz.enforcer`, and the resource(s).

## Checklist for a new protected route

```
- [ ] Identify which api_identifier(s) the route touches
- [ ] Pick the right Action (READ, WRITE, etc.) from ring/authz/enforcer.py
- [ ] Use load_and_check or bulk_load_and_check at the top of the handler
- [ ] Follow the closest sibling route in the same domain for consistency
- [ ] Update ring/authz/policy.csv if a new role/action combo is needed
- [ ] Add tests for: happy path, permission denied, not-found
- [ ] Use the `admin` pytest marker if the test needs an admin client
```

## Typical pattern

```python
from ring.authz.authz import load_and_check
from ring.authz.enforcer import Action

@router.post("/letters/{letter_api_id}/publish")
def publish_letter(
    letter_api_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LetterResponse:
    letter = load_and_check(db, user, Action.WRITE, letter_api_id)
    # ... do the work with `letter`
```

For routes that take many ids at once:

```python
letters = bulk_load_and_check(db, user, Action.READ, payload.letter_api_ids)
```

For partial-success endpoints where you want to return both accessible and
inaccessible items, use `bulk_can_or_inaccessible` and surface
`InaccessibleResource` entries in the response shape.

## Testing

- Add tests under `ring/tests/unit/<domain>/` and (where it makes sense) under
  `ring/tests/unit/authz/`.
- Use existing client fixtures from `ring/tests/conftest.py`. Add the
  `@pytest.mark.admin` marker (defined in
  [ring/tests/pytest.ini](../../../ring/tests/pytest.ini)) when the route
  requires an admin user.
- Cover all three cases:
  1. Authorized user → 2xx with expected body
  2. Authenticated but unauthorized user → 403 / `PermissionError`
  3. Missing resource → 404 / `IDNotFoundException`

## Don'ts

- Don't write raw `if user.id != resource.owner_id` checks in handlers; route
  the check through `authz.py` so the policy stays in one place.
- Don't load with `db.query(Model).filter(...).one()` and then forget the
  permission check — `load_and_check` does both.
- Don't paper over a missing policy by editing the handler; add the rule to
  `ring/authz/policy.csv` and cover it with a test.
