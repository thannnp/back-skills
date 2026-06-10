# Webhook mode — reference

Read this when the user picked **webhook** mode (Step 3). It drives the **real** Omise
webhook path instead of editing the DB directly, so it's closer to production. It only
supports `successful` / `failed` — see the limitation note in SKILL.md Step 4.

## How it works

1. `scripts/summon_webhook.php` creates a pending transaction, creates a real Omise
   **test** charge with the right test card, then polls Omise for the charge's event id.
   The webhook handler re-fetches the event from Omise by id, so this works locally
   **without ngrok**.
2. You POST the event `{"object":"event","id":<EVENT_ID>}` to the backoffice webhook,
   which runs the same `OmiseService::updateOmisePayment` production code path.

## Test cards

| Status | Test card | Result |
|---|---|---|
| `successful` | `4242424242424242` | charge `successful` |
| `failed` | `4111111111140011` | charge `failed` (failure_code `insufficient_fund`) |

## POST the event to the webhook

Discover the published host port for container port 80, then POST:

```bash
PORT=$(docker port <container> 80/tcp | head -1 | sed 's/.*://')
curl -s -w "\nHTTP=%{http_code}\n" -X POST "http://localhost:${PORT}/api/webhook/omise" \
  -H 'Content-Type: application/json' \
  -d '{"object":"event","id":"<EVENT_ID>"}'
```

To instead exercise an external ngrok delivery, POST to the ngrok URL — but the ngrok
tunnel must forward to the **backoffice** port (the one above), not to wpe-service.
(Omise's webhook lives on the backoffice; wpe-service only has `/api/webhook/payment`.)

## Known local caveat (state still lands correctly)

On a `successful` charge the webhook returns **HTTP 400** locally because
`updateOmisePayment` calls `PointService`, which needs a `reward` DB connection that
local does not have:

```
database "reward" does not exist (Connection: reward, ... point_profiles ...)
```

The important writes (transaction → successful, `incrementUsage()` → link `done`) commit
**before** that exception, so the result is still correct. A `failed` charge does not
reach `PointService`, so it usually returns 200. Tell the user this in Thai if a 400
appears — it is expected, not a failure of the skill.

## Prerequisites

- Omise **test** keys configured in the backoffice `.env`
  (`OMISE_PUBLIC_KEY=pkey_test_…`, `OMISE_SECRET_KEY=skey_test_…`).
- Posting locally to `http://localhost:<backoffice-port>/api/webhook/omise` needs nothing
  else — the handler re-fetches the event from Omise.
- For real Omise dashboard delivery: run `ngrok http <backoffice-port>` and register that
  URL under Omise Dashboard → Webhooks. (Common mistake: pointing ngrok at the wpe-service
  port instead of the backoffice port.)
- A 200 response additionally requires a working `reward` DB connection in local; without
  it you get the 400 described above (data still lands).
