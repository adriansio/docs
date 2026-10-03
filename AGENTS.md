# StoreRocket API Documentation

CODEX -> CLAUDE / CODEX / POLARIS / CURSOR: These instructions apply to every
agent working on this documentation repository.

- The published API reference is https://docs.storerocket.io. Navigation in
  docs.json defines the supported published pages; excluded starter pages are not
  evidence that an API operation exists.
- Verify contracts against the supported StoreRocket implementation in
  adriansio/storerocket. Production uses master; Phoenix features need a verified
  release before they are described as available.
- Keep supported V1 and V2 contracts distinct, including credentials, routes,
  identifiers, response shapes and update/geocoding behavior. Do not change an
  API contract to simplify the documentation.
- Use Stripe as the developer-experience benchmark: clear instructions,
  actionable errors and copyable examples. Preserve supported compatibility;
  breaking changes require a version and migration guidance.
- Retire Postman as the documentation host. An optional Postman client collection
  remains supported; examples contain placeholders, never real credentials or data.
- Use the official StoreRocket logo unchanged, normal light/dark switching and
  native Mintlify components. Check desktop and mobile in both themes.
- Run mint validate and mint broken-links, parse changed JSON/shell examples,
  and check the actual rendered and copied result. Never run write examples
  against a real customer account.
- Never push directly to main or merge a PR. Adriano merges; main publishes
  automatically. Verify deployed pages after the merge.

## Documentation Ships With Important Work (2026-10-03)

CODEX -> CLAUDE / CODEX / POLARIS / CURSOR: Adriano's standing instruction:
every important StoreRocket change includes a check of the relevant documentation.
Update it whenever the change makes existing instructions or examples incomplete
or wrong. Documentation is part of delivery, never an optional later task.

- Check the Mintlify API reference at https://docs.storerocket.io (source:
  https://github.com/adriansio/docs), affected Intercom help articles, and relevant
  in-app instructions and examples before calling customer-facing work finished.
- Update affected documentation in the same change/release. Across repositories,
  prepare and link the companion docs change; track its publication until complete.
  API changes include methods, accepted inputs, defaults, omission/clearing, errors,
  response shapes, authentication, compatibility and runnable examples as applicable.
- Describe the supported, shipped behavior. Verify against the actual implementation;
  do not document an unshipped Phoenix feature as available.
- Check links and copied examples safely, then verify the published result after
  release. A local edit, merged app PR or prepared article is not proof docs are live.
- If no documentation needs changing, record "Docs checked; no update needed" with
  the reason. Do not create unrelated documentation for ceremony.
- This applies to every agent, branch and worktree. Existing approval, publication,
  production and Adriano-only merge rules still apply.
