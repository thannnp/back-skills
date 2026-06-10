---
name: horo-summon-money
description: >-
  Force the payment status of a horoacademy payment link or payment transaction
  in a LOCAL test environment. Given a payment-link id OR a payment-transaction
  id, it sets the transaction status (successful / pending / failed / expired /
  reversed) and lets the payment link's status derive from production logic
  (only a successful payment increments usage and flips the link to "done").
  Use when the user wants to test/QA payment flows by forcing a payment to a
  chosen status — e.g. "mark this payment link as paid", "make this transaction
  successful/failed", "ทำให้ payment link จ่ายสำเร็จ", "เสกเงิน", "ปรับสถานะการ
  ชำระเงิน", "/horo-summon-money". This only touches payment state in the
  backoffice DB; it does NOT notify wpe-service or mark any task.
---

# horo-summon-money

A **local-only testing helper** that forces the payment status of a horoacademy
**payment link** or **payment transaction**. It exists so you can QA payment flows
without going through a real Omise checkout.

Scope is deliberately narrow: **it only adjusts payment state** (the
`payment_transactions` row and, derived from it, the `payment_links` row). It does
**not** notify `wpe-service` and does **not** mark any task.

> All prompts to the user MUST be written in **Thai**. This file is in English; the
> questions you ask the user are in Thai (see the exact wording below).

## Domain model (what "payment status" means here)

Two tables in the **backoffice** DB are involved:

| Table | Model | Holds |
|---|---|---|
| `payment_links` | `\App\Models\PaymentLink` | the link itself — `price`, `current_usage_count`, `max_usage_count`, `is_unlimited`, `status` (`active` / `done` / `expired`) |
| `payment_transactions` | `\App\Models\PaymentTransaction` | one actual payment — `amount`, `paid_at`, `method`, `provider_id`, `status` (`successful` / `pending` / `failed` / `expired` / `reversed`) |

A link has many transactions, joined polymorphically:
`payment_transactions.model_type = 'App\Models\PaymentLink'` and
`payment_transactions.model_id = <payment_link id>`.

**Both ids are UUIDs** and cannot be told apart by shape — that is why the skill
asks the user which type they gave (see Step 2).

How the link status derives from the transaction (mirrors production
`OmiseService::updateOmisePayment`):

- transaction → `successful`  ⇒  call `$link->incrementUsage()`, which increments
  `current_usage_count` and flips `status` to `done` once it reaches
  `max_usage_count` (unless `is_unlimited`).
- transaction → any other status  ⇒  the link is **not touched** (usage unchanged).
- Usage is **never decremented** — re-running with a non-successful status will not
  roll a `done` link back.

## Interaction flow

Ask these in order, **in Thai**, using the AskUserQuestion tool. Skip any question
the user already answered in their invocation (e.g. they typed the id, or said
"ทำให้ failed ผ่าน webhook").

### Step 1 — UUID
If the user passed a UUID with the command, use it. Otherwise ask:
> "ใส่ UUID ที่ต้องการปรับสถานะมาได้เลย (payment link id หรือ transaction id)"

### Step 2 — Type (ask every time unless already stated)
> "UUID นี้เป็น type ไหน?"
> options: `payment link` / `transaction`

Then **verify it exists** in the matching table (see Step 5). If not found, stop and
tell the user in Thai that the id was not found in that table.

### Step 3 — Mode (ask BEFORE status)
> "จะใช้ mode ไหน?"
> options:
> - `direct` — แก้ DB ตรงผ่าน tinker (เร็ว, เลือก status ได้ครบ 5 แบบ) — **default**
> - `webhook` — สร้าง Omise charge จริงแล้วยิงเข้า webhook (เหมือน production มากกว่า, รองรับแค่ successful / failed)

### Step 4 — Status (options depend on the mode chosen in Step 3)
- If mode = **direct**:
  > "จะปรับเป็นสถานะอะไร?"
  > options: `successful` / `pending` / `failed` / `expired` / `reversed`
- If mode = **webhook** (state the limitation in the question text):
  > "จะปรับเป็นสถานะอะไร? (webhook mode รองรับแค่ 2 สถานะนี้ — status อื่นต้องใช้ direct mode)"
  > options: `successful` / `failed`

If the user asks for `pending` / `expired` / `reversed` in webhook mode, tell them in
Thai that test cards cannot produce those statuses through a charge and offer to do it
in **direct** mode instead.

## Step 5 — Resolve the environment (always, before mutating)

1. **Find the backoffice container** (do not hardcode the name):
   ```bash
   docker ps --filter "name=backoffice-main-service" --format "{{.Names}}" | head -1
   ```
   If empty, stop and tell the user (in Thai) that the backoffice container was not
   found — is docker running?

2. **Safety guard — confirm it is local.** Run inside the container:
   ```bash
   docker exec -i <container> sh -lc 'php artisan tinker' <<< 'echo config("app.env");'
   ```
   If the env is **not** `local`, **STOP** and warn the user in Thai that the
   environment is not local so no data will be changed. Only continue if the user
   explicitly passed `--force`.

## Step 6 — Direct mode (default)

Write this script to a temp file, substituting `__TARGET_ID__`, `__ID_TYPE__`
(`link` or `txn`), and `__STATUS__`. Copy it into the container and run it via
**stdin** (`php artisan tinker < file` — passing the file as an argument does NOT
execute it).

```php
$idType   = '__ID_TYPE__';   // 'link' or 'txn'
$targetId = '__TARGET_ID__';
$status   = '__STATUS__';     // successful|pending|failed|expired|reversed

use App\Models\PaymentLink;
use App\Models\PaymentTransaction;

if ($idType === 'link') {
    $pl = PaymentLink::find($targetId);
    if (!$pl) { echo "ERR=link_not_found\n"; return; }
    $txn = PaymentTransaction::where('model_type', PaymentLink::class)
        ->where('model_id', $pl->id)->orderByDesc('created_at')->first();
} else {
    $txn = PaymentTransaction::find($targetId);
    if (!$txn) { echo "ERR=txn_not_found\n"; return; }
    $pl = $txn->model; // the linked PaymentLink
}

$prev = $txn->status ?? null;

// idempotency: link already paid and asked to pay again -> no-op
if ($status === 'successful' && $prev === 'successful') {
    echo "NOOP=already_successful TXN_ID={$txn->id}\n";
    if ($pl) echo "LINK_STATUS={$pl->status} USAGE={$pl->current_usage_count}/{$pl->max_usage_count}\n";
    return;
}

if (!$txn) {
    // link mode with no transaction yet -> create one
    $txn = PaymentTransaction::create([
        'user_id'          => $pl->user_id,
        'customer_name'    => $pl->customer_name,
        'model_type'       => PaymentLink::class,
        'model_id'         => $pl->id,
        'method'           => 'credit',
        'amount'           => $pl->price,
        'net'              => $pl->price,
        'status'           => $status,
        'paid_at'          => $status === 'successful' ? now() : null,
        'transaction_date' => now(),
        'source'           => 'backoffice',
    ]);
} else {
    // flip the existing transaction
    $txn->status  = $status;
    if ($status === 'successful' && empty($txn->paid_at)) $txn->paid_at = now();
    $txn->save();
}

// derive link: only a real transition INTO successful increments usage
if ($pl && $status === 'successful' && $prev !== 'successful') {
    $pl->incrementUsage();
    $pl->refresh();
}

echo "TXN_ID={$txn->id} TXN_STATUS={$txn->status}\n";
if ($pl) echo "LINK_ID={$pl->id} LINK_STATUS={$pl->status} USAGE={$pl->current_usage_count}/{$pl->max_usage_count}\n";
```

Run:
```bash
docker cp /tmp/summon.php <container>:/tmp/summon.php
docker exec -i <container> sh -lc 'php artisan tinker < /tmp/summon.php'
```

## Step 7 — Webhook mode (`successful` / `failed` only)

This drives the **real** Omise webhook path: create a real Omise test charge, then
POST its event to the backoffice webhook. The webhook handler re-fetches the event
from Omise, so it works locally without ngrok.

Pick the test card by the requested status:

| Status | Test card | Result |
|---|---|---|
| `successful` | `4242424242424242` | charge `successful` |
| `failed` | `4111111111140011` | charge `failed` (failure_code `insufficient_fund`) |

1. **Create a pending transaction + Omise charge** (substitute the link id; in txn
   mode reuse the given transaction id as `payment_transaction_id`). Run via stdin:

   ```php
   use App\Models\PaymentLink;
   use App\Models\PaymentTransaction;

   $pl   = PaymentLink::find('__LINK_ID__');
   $card = '__TEST_CARD__'; // 4242424242424242 (successful) | 4111111111140011 (failed)
   if (!$pl) { echo "ERR=link_not_found\n"; return; }

   $txn = PaymentTransaction::create([
       'user_id' => $pl->user_id, 'customer_name' => $pl->customer_name,
       'model_type' => PaymentLink::class, 'model_id' => $pl->id,
       'method' => 'credit', 'amount' => $pl->price, 'net' => $pl->price,
       'status' => 'pending', 'transaction_date' => now(), 'source' => 'backoffice',
   ]);

   $token = \OmiseToken::create(['card' => [
       'name' => 'Test', 'number' => $card,
       'expiration_month' => 12, 'expiration_year' => 2030, 'security_code' => '123',
   ]]);
   $charge = \OmiseCharge::create([
       'amount' => intval($pl->price) * 100, 'currency' => 'thb', 'card' => $token['id'],
       'metadata' => [
           'model_type' => PaymentLink::class, 'model_id' => $pl->id,
           'payment_transaction_id' => $txn->id, 'is_subscription' => false, 'point' => 0,
       ],
   ]);
   echo "TXN_ID={$txn->id}\nCHARGE_ID={$charge['id']}\nCHARGE_STATUS={$charge['status']}\n";
   ```

2. **Find the Omise event id** for that charge (poll a few times — events are async):

   ```php
   $chargeId = '__CHARGE_ID__'; $found = null;
   for ($i = 0; $i < 5; $i++) {
       foreach (\OmiseEvent::retrieve()['data'] as $e) {
           if (($e['data']['object'] ?? null) === 'charge' && ($e['data']['id'] ?? null) === $chargeId) {
               if (($e['key'] ?? '') === 'charge.complete') { $found = $e; break 2; }
               if (!$found) $found = $e;
           }
       }
       if ($found) break; sleep(2);
   }
   echo $found ? "EVENT_ID={$found['id']}\n" : "EVENT_NOT_FOUND\n";
   ```

3. **POST the event to the backoffice webhook.** Discover the published host port for
   container port 80, then POST:

   ```bash
   PORT=$(docker port <container> 80/tcp | head -1 | sed 's/.*://')
   curl -s -w "\nHTTP=%{http_code}\n" -X POST "http://localhost:${PORT}/api/webhook/omise" \
     -H 'Content-Type: application/json' \
     -d '{"object":"event","id":"__EVENT_ID__"}'
   ```

   To instead exercise an external ngrok delivery, POST to the ngrok URL — but the
   ngrok tunnel must forward to the **backoffice** port (the one above), not to
   wpe-service. (Omise's webhook lives on the backoffice; wpe-service only has
   `/api/webhook/payment`.)

### Known local caveat (state still lands correctly)
On a `successful` charge the webhook returns **HTTP 400** locally because
`updateOmisePayment` calls `PointService`, which needs a `reward` DB connection that
local does not have:
```
database "reward" does not exist (Connection: reward, ... point_profiles ...)
```
The important writes (transaction → successful, `incrementUsage()` → link `done`)
commit **before** that exception, so the result is still correct. A `failed` charge
does not reach `PointService`, so it usually returns 200. Tell the user this in Thai
if a 400 appears — it is expected, not a failure of the skill.

## Step 8 — Verify and report

After either mode, read back the final state and report it to the user **in Thai**
(a small before → after summary): the transaction status, the link status, and
`current_usage_count / max_usage_count`. You can confirm directly from the DB:

```bash
docker exec <pg_container> psql -U sail -d horoacademy-backoffice -c \
  "SELECT status, current_usage_count, max_usage_count FROM payment_links WHERE id='<link id>';"
```
(`<pg_container>` = the backoffice postgres container, e.g. discovered via
`docker ps --filter name=backoffice-pgsql`.)

## Webhook mode prerequisites (reference)

- Omise **test** keys configured in the backoffice `.env`
  (`OMISE_PUBLIC_KEY=pkey_test_…`, `OMISE_SECRET_KEY=skey_test_…`).
- Posting locally to `http://localhost:<backoffice-port>/api/webhook/omise` needs
  nothing else — the handler re-fetches the event from Omise.
- For real Omise dashboard delivery: run `ngrok http <backoffice-port>` and register
  that URL under Omise Dashboard → Webhooks. (Common mistake: pointing ngrok at the
  wpe-service port instead of the backoffice port.)
- A 200 response additionally requires a working `reward` DB connection in local;
  without it you get the 400 described above (data still lands).
