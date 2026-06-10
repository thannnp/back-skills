<?php
// summon_webhook.php — drive the REAL Omise webhook path: create a real Omise test
// charge, then find its event so the caller can POST it to the backoffice webhook.
// Reads inputs from environment variables so this file never needs editing per-run.
//
//   SUMMON_LINK_ID   the payment_link id to charge
//   SUMMON_STATUS    successful | failed  (selects the test card)
//   SUMMON_TXN_ID    OPTIONAL — reuse this existing transaction id instead of creating one
//
// Test cards:
//   successful -> 4242424242424242        (charge successful)
//   failed     -> 4111111111140011        (charge failed, insufficient_fund)
//
// Outputs (one KEY=VALUE per line): TXN_ID, CHARGE_ID, CHARGE_STATUS, EVENT_ID.
// The caller then POSTs {"object":"event","id":<EVENT_ID>} to the backoffice webhook.
//
// Run with:
//   docker cp scripts/summon_webhook.php <container>:/tmp/summon_webhook.php
//   docker exec -e SUMMON_LINK_ID=<uuid> -e SUMMON_STATUS=successful \
//     -i <container> sh -lc 'php artisan tinker < /tmp/summon_webhook.php'

use App\Models\PaymentLink;
use App\Models\PaymentTransaction;

$linkId = getenv('SUMMON_LINK_ID');
$status = getenv('SUMMON_STATUS');                 // successful | failed
$txnId  = getenv('SUMMON_TXN_ID') ?: null;
$card   = $status === 'failed' ? '4111111111140011' : '4242424242424242';

$pl = PaymentLink::find($linkId);
if (!$pl) { echo "ERR=link_not_found\n"; return; }

// reuse an existing pending transaction (txn mode) or create a fresh one
$txn = $txnId ? PaymentTransaction::find($txnId) : null;
if ($txnId && !$txn) { echo "ERR=txn_not_found\n"; return; }
if (!$txn) {
    $txn = PaymentTransaction::create([
        'user_id' => $pl->user_id, 'customer_name' => $pl->customer_name,
        'model_type' => PaymentLink::class, 'model_id' => $pl->id,
        'method' => 'credit', 'amount' => $pl->price, 'net' => $pl->price,
        'status' => 'pending', 'transaction_date' => now(), 'source' => 'backoffice',
    ]);
}

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

// find the Omise event for that charge (events are async — poll a few times)
$found = null;
for ($i = 0; $i < 5; $i++) {
    foreach (\OmiseEvent::retrieve()['data'] as $e) {
        if (($e['data']['object'] ?? null) === 'charge' && ($e['data']['id'] ?? null) === $charge['id']) {
            if (($e['key'] ?? '') === 'charge.complete') { $found = $e; break 2; }
            if (!$found) $found = $e;
        }
    }
    if ($found) break;
    sleep(2);
}
echo $found ? "EVENT_ID={$found['id']}\n" : "EVENT_NOT_FOUND\n";
