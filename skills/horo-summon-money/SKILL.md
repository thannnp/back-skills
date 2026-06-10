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
**payment link** or **payment transaction**, so you can QA payment flows without going
through a real Omise checkout.

Scope is deliberately narrow: **it only adjusts payment state** (the
`payment_transactions` row and, derived from it, the `payment_links` row). It does
**not** notify `wpe-service` and does **not** mark any task.

> All prompts to the user MUST be written in **Thai**. This file is in English; the
> questions you ask the user are in Thai (see the exact wording below).

## Response style (important)

- **Keep every reply short.** Ask only what the flow needs, report only the result.
- The **single purpose** of this skill is to **update the payment status to what the user
  wants** — stay on that. Do not volunteer explanations, background, or extra options the
  user didn't ask for.
- If the user asks something **unrelated** to updating the payment status, do not answer
  the unrelated part — gently steer back to the task (in Thai).

## Domain model (what "payment status" means here)

Two tables in the **backoffice** DB are involved:

| Table | Model | Holds |
|---|---|---|
| `payment_links` | `\App\Models\PaymentLink` | the link — `price`, `current_usage_count`, `max_usage_count`, `is_unlimited`, `status` (`active` / `done` / `expired`) |
| `payment_transactions` | `\App\Models\PaymentTransaction` | one payment — `amount`, `paid_at`, `method`, `status` (`successful` / `pending` / `failed` / `expired` / `reversed`) |

A link has many transactions, joined polymorphically:
`payment_transactions.model_type = 'App\Models\PaymentLink'` and
`payment_transactions.model_id = <payment_link id>`.

**Both ids are UUIDs** and cannot be told apart by shape — that is why Step 2 asks the
user which type they gave.

How the link status derives from the transaction (mirrors production
`OmiseService::updateOmisePayment`):

- transaction → `successful`  ⇒  call `$link->incrementUsage()`, which increments
  `current_usage_count` and flips `status` to `done` once it reaches `max_usage_count`
  (unless `is_unlimited`).
- transaction → any other status  ⇒  the link is **not touched** (usage unchanged).
- Usage is **never decremented** — re-running with a non-successful status will not roll
  a `done` link back.

The bundled scripts already encode this derivation; you don't need to reimplement it.

## Interaction flow

### Step 1 — UUID (ALWAYS ask first, before anything else)
The **moment this skill is invoked**, ignore everything else and ask the user for the
UUID first. Do **not** resolve the environment, look for containers, or run any other
step until you have the UUID. Even if the user already typed a UUID in their invocation,
ask them to confirm it:
> "ใส่ UUID ที่ต้องการปรับสถานะมาได้เลย (payment link id หรือ transaction id)"

Once you have the UUID, continue with the remaining steps below, **in Thai**, using the
AskUserQuestion tool. Skip any later question the user already answered in their
invocation (e.g. they said "ทำให้ failed ผ่าน webhook").

### Step 2 — Type (ask every time unless already stated)
> "UUID นี้เป็น type ไหน?"
> options: `payment link` / `transaction`

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

If the user asks for `pending` / `expired` / `reversed` in webhook mode, tell them in Thai
that test cards cannot produce those statuses through a charge, and offer **direct** mode
instead.

## Step 5 — Summary & confirm (always, before touching anything)

Before resolving the environment or mutating any data, show the user a **short Thai
summary** of everything collected and ask them to **confirm**. Do this with the
AskUserQuestion tool. Do **not** proceed to Step 6 until the user picks `ยืนยัน`.

Summary format (fill in the collected values):
> "สรุปก่อนทำนะครับ:
> • UUID: `<uuid>`
> • type: `<payment link | transaction>`
> • mode: `<direct | webhook>`
> • status: `<status>`
> จะดำเนินการเลยไหม?"
> options: `ยืนยัน` / `ยกเลิก`

- If the user picks `ยกเลิก`, stop and do nothing (no DB change).
- If they want to change a value, go back to the relevant step, then re-summarise.

## Step 6 — Resolve the environment (always, before mutating)

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
   If the env is **not** `local`, **STOP** and warn the user in Thai that the environment
   is not local so no data will be changed. Only continue if the user explicitly passed
   `--force`.

## Step 7 — Run the chosen mode

The scripts read their inputs from **environment variables** passed via `docker exec -e`,
so you never edit the script files — just set the vars. Copy the script into the container
once, then run it through tinker over **stdin** (`php artisan tinker < file` — passing the
file as an argument does NOT execute it).

### Direct mode (default)

Uses `scripts/summon_direct.php`. In **link** mode it flips the link's latest transaction
(creating one if none exists); in **txn** mode it flips that exact transaction and derives
its link.

```bash
docker cp scripts/summon_direct.php <container>:/tmp/summon_direct.php
docker exec \
  -e SUMMON_ID_TYPE=<link|txn> \
  -e SUMMON_TARGET_ID=<uuid> \
  -e SUMMON_STATUS=<successful|pending|failed|expired|reversed> \
  -i <container> sh -lc 'php artisan tinker < /tmp/summon_direct.php'
```

The script prints `TXN_ID=… TXN_STATUS=…` and `LINK_ID=… LINK_STATUS=… USAGE=n/m`
(or `NOOP=already_successful` / `ERR=…`). Use that for the Step 8 report.

### Webhook mode (`successful` / `failed` only)

This drives the real Omise webhook path. **Read `references/webhook.md`** for the test
cards, the curl POST to `/api/webhook/omise`, the ngrok notes, and the expected local
HTTP 400 caveat — then:

```bash
docker cp scripts/summon_webhook.php <container>:/tmp/summon_webhook.php
docker exec \
  -e SUMMON_LINK_ID=<uuid> \
  -e SUMMON_STATUS=<successful|failed> \
  -i <container> sh -lc 'php artisan tinker < /tmp/summon_webhook.php'
# (txn mode: also pass -e SUMMON_TXN_ID=<uuid> to reuse an existing pending transaction)
```

The script prints `TXN_ID`, `CHARGE_ID`, `CHARGE_STATUS`, and `EVENT_ID`. POST that
`EVENT_ID` to the webhook as described in `references/webhook.md`.

## Step 8 — Verify and report

After either mode, read back the final state and report it to the user **in Thai** (a small
before → after summary): the transaction status, the link status, and
`current_usage_count / max_usage_count`. You can confirm directly from the DB:

```bash
docker exec <pg_container> psql -U sail -d horoacademy-backoffice -c \
  "SELECT status, current_usage_count, max_usage_count FROM payment_links WHERE id='<link id>';"
```
(`<pg_container>` = the backoffice postgres container, e.g. discovered via
`docker ps --filter name=backoffice-pgsql`.)
