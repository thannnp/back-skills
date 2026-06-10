<?php
// summon_direct.php — force a payment transaction to a chosen status by editing the
// backoffice DB directly through tinker. Reads its inputs from environment variables
// (passed via `docker exec -e ...`) so this file never needs editing per-run.
//
//   SUMMON_ID_TYPE   'link' | 'txn'
//   SUMMON_TARGET_ID the payment_link id (link mode) or payment_transaction id (txn mode)
//   SUMMON_STATUS    successful | pending | failed | expired | reversed
//
// Run with:
//   docker cp scripts/summon_direct.php <container>:/tmp/summon_direct.php
//   docker exec -e SUMMON_ID_TYPE=link -e SUMMON_TARGET_ID=<uuid> -e SUMMON_STATUS=successful \
//     -i <container> sh -lc 'php artisan tinker < /tmp/summon_direct.php'

use App\Models\PaymentLink;
use App\Models\PaymentTransaction;

$idType   = getenv('SUMMON_ID_TYPE');
$targetId = getenv('SUMMON_TARGET_ID');
$status   = getenv('SUMMON_STATUS');

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
    $txn->status = $status;
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
