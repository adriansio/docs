# StoreRocket API documentation

The API reference is published at [docs.storerocket.io](https://docs.storerocket.io)
using Mintlify. This repository contains its pages, examples, branding and navigation.

## What to update

Read [AGENTS.md](AGENTS.md) before working here. Important StoreRocket changes
must include the affected documentation and examples in the same release.

- `docs.json` defines the published navigation and native API playground.
  The four GET pages use direct browser requests (`proxy: false`). Write pages
  keep `playground: 'simple'` and runnable code examples: do not enable their
  forms until explicit nulls, empty objects and omitted fields survive a native
  request test. A visible type picker alone is not proof of correct JSON.
- `api/` contains the supported V2 reference and separate legacy V1 guides.
- `api/quickstart.mdx` starts with authenticated read requests; `api/sync-locations.mdx`
  contains complete JavaScript/PHP scripts with preview mode and bounded retries.
- `scripts/check-examples.py` extracts published examples and checks their syntax
  and behavior against local HTTP fixtures, without calling the production API.
- `files/storerocket-v2.postman_collection.json` is an optional Postman client
  collection. Postman is being retired as the documentation host.
- `custom.css` contains the bounded native-layout adjustments.
- `logo/` and `favicon.png` use the official StoreRocket branding.

Verify behavior against the supported implementation in `adriansio/storerocket`.
Production uses `master`; do not document unshipped Phoenix behavior as available.
Excluded starter pages are not proof that an API operation exists.

## Preview and checks

With the Mintlify CLI available, run these commands from this repository:

```bash
mint dev --no-open
mint validate
mint broken-links
python3 scripts/check-examples.py
```

Use the local preview to check desktop and mobile, both themes, links, search,
the exact copied code, and the gap above previous/next navigation at every page's
bottom. Test **Try it** on all four GET pages with fixture interception before
clicking **Send**; check URL, bearer header, query parameters and displayed HTTP
status/body. The code tabs are authored templates, separate from the form's
live response. Parse changed JSON and shell examples without running
write requests against customer accounts. Examples use placeholder credentials.
The example checks need Python 3, Node.js 22 or later, and PHP 8.2 or later with
cURL. They cover request encoding, error exits, pagination, preview mode, explicit
clearing and retry boundaries. No test database or SDK is required.

On Adriano's Mac, the configured trusted HTTPS preview is
[https://sr-api-docs.test](https://sr-api-docs.test).

## Publishing

Open a reviewed PR against `main`. Adriano merges; never push directly to
`main` or merge on his behalf. Mintlify publishes `main` automatically.
After the merge, verify the actual pages and examples at
[docs.storerocket.io](https://docs.storerocket.io).

StoreRocket dashboard links and Intercom articles live in the application
repository. Link their companion changes when needed; an app deployment does not
publish an Intercom article.
