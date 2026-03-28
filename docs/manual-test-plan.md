# Manual Test Plan

## Goal
Verify that the staged offline pipeline listens to pump.fun new token creation and migration logs, appends normalized records to JSONL files, builds offline snapshots in `data/snapshots.jsonl`, scores them into `data/scored_snapshots.jsonl`, and filters them into `data/filtered_snapshots.jsonl`.

## Setup
1. Create a virtual environment.
2. Install the project in editable mode with `pip install -e .`.
3. Copy `.env.example` to `.env`.
4. Set `SOLANA_NODE_WSS_ENDPOINT` to a working Solana WebSocket RPC endpoint.

## Run
1. Start the collector with `python -m collector.main`.
2. Leave it running until at least one pump.fun token creation is observed.
3. Leave it running until at least one migration event is observed, if one occurs during the test window.
4. Stop it with `Ctrl+C` after one or more records have been written.

## Verify Output
1. Confirm that `data/events.jsonl` exists.
2. Confirm that each line in `data/events.jsonl` is valid JSON.
3. Confirm that a token creation record in `data/events.jsonl` includes these fields:
   - `observed_at`
   - `source`
   - `event_type`
   - `signature`
   - `slot`
   - `instruction_name`
   - `name`
   - `symbol`
   - `uri`
   - `mint`
   - `bonding_curve`
   - `user`
   - `creator`
   - `token_standard`
   - `is_mayhem_mode`
   - `raw_data_base64`
   - `raw_logs`
4. Confirm that `source` is `pumpfun.logs`.
5. Confirm that `event_type` is `token_created`.
6. Confirm that `mint` is a non-empty base58 Solana address string and can be decoded by the selected `base58` Python library. Do not require it to be exactly 44 characters.
7. Confirm that `raw_data_base64` is non-empty for parsed create events.
8. Confirm that `data/migration_events.jsonl` is created after at least one migration is observed.
9. Confirm that each line in `data/migration_events.jsonl` is valid JSON.
10. Note that some real migration events may still be missed because RPC logs can be truncated and may omit `Program data:` for a given transaction.
11. Confirm that a migration record includes these fields:
   - `observed_at`
   - `source`
   - `event_type`
   - `signature`
   - `slot`
   - `instruction_name`
   - `migration_timestamp`
   - `migration_index`
   - `creator`
   - `mint`
   - `quote_mint`
   - `base_mint_decimals`
   - `quote_mint_decimals`
   - `base_amount_in`
   - `quote_amount_in`
   - `pool_base_amount`
   - `pool_quote_amount`
   - `minimum_liquidity`
   - `initial_liquidity`
   - `lp_token_amount_out`
   - `pool_bump`
   - `pool`
   - `lp_mint`
   - `user_base_token_account`
   - `user_quote_token_account`
   - `raw_data_base64`
   - `raw_logs`
12. Confirm that `event_type` is `token_migrated`.
13. Confirm that `mint`, `pool`, and `lp_mint` are non-empty base58 strings decodable by the selected `base58` Python library.

## Decode Check Example
Use a short Python one-liner against a recorded line:

```bash
python -c "import base58, json; record=json.loads(open('data/events.jsonl', encoding='utf-8').readline()); print(len(base58.b58decode(record['mint'])))"
```

The decoded mint should produce bytes without raising an exception.

## Malformed Event Handling
1. Keep the collector running long enough to observe normal traffic.
2. Confirm the process continues running even if some logs do not parse into `TokenCreatedEvent`.
3. Confirm the process continues running even if some logs do not parse into `MigrationEvent`.
4. Confirm reconnect attempts happen after connection loss with a 5 second backoff.

## Migration Skip Behavior
1. Watch the collector logs during migration traffic.
2. Confirm transactions that contain error logs are skipped and do not produce records in `data/migration_events.jsonl`.
3. Confirm transactions that include an `already migrated` log are skipped and do not produce records in `data/migration_events.jsonl`.

## Reconnect Verification Procedure
1. Start the collector with `python -m collector.main`.
2. Wait until the startup logs show that the websocket subscription has been established.
3. Disconnect the machine from the network, disable the network adapter, or temporarily block the configured websocket endpoint.
4. Observe the collector logs and confirm the connection drops.
5. Confirm the collector does not exit after the disconnect.
6. Confirm a reconnect log appears and explicitly says it will retry in 5 seconds.
7. Restore network access or unblock the websocket endpoint.
8. Confirm the collector connects again and logs a fresh subscription confirmation.
9. Confirm both listener paths reconnect cleanly over time.
10. Leave it running until at least one new event is processed after reconnection.

## Snapshot Builder
1. After collecting at least one create event, run `python -m collector.snapshots`.
2. Confirm `data/snapshots.jsonl` exists.
3. Confirm the file is overwritten on each run rather than appended.
4. Confirm each line is valid JSON.
5. Confirm a snapshot record includes these fields:
   - `mint`
   - `snapshot_built_at`
   - `first_seen_at`
   - `created_at`
   - `migrated_at`
   - `has_migrated`
   - `token_standard`
   - `creator`
   - `bonding_curve`
   - `migration_target`
   - `source_count`
   - `event_count`
6. Confirm that a token with only a create event has `has_migrated=false`.
7. Confirm that a token with both create and migration records has `has_migrated=true` and `migration_target` populated from the migration record.
8. Re-run `python -m collector.snapshots` without changing the inputs and confirm the number of lines in `data/snapshots.jsonl` does not grow.

## Scorer
1. Run the scorer with `python -m scorer`.
2. Confirm `data/scored_snapshots.jsonl` exists.
3. Confirm the file is overwritten on each run rather than appended.
4. Confirm each line is valid JSON.
5. Confirm each scored record includes all snapshot fields plus:
   - `score_version`
   - `score_total`
   - `score_reasons`
   - `score_flags`
   - `scored_at`
6. Confirm scoring remains offline and deterministic for the same snapshot inputs apart from the run timestamp in `scored_at`.
7. Confirm a normal token snapshot with `created_at`, `creator`, `token_standard`, and `bonding_curve`, but no migration, scores `6`.
   - Expected rule breakdown:
   - `has_create_event (+2)`
   - `creator_present (+1)`
   - `token_standard_known (+1)`
   - `bonding_curve_present (+1)`
   - `lifecycle_order_valid (+1)`
8. Confirm a migrated token with valid lifecycle order and `migration_target` scores `9`.
   - Expected rule breakdown:
   - `has_create_event (+2)`
   - `creator_present (+1)`
   - `token_standard_known (+1)`
   - `bonding_curve_present (+1)`
   - `has_migration_event (+2)`
   - `migration_target_present (+1)`
   - `lifecycle_order_valid (+1)`
9. Confirm a snapshot missing `creator` receives the `missing_creator` flag.
10. Confirm a snapshot with `migrated_at` earlier than `created_at` receives the `lifecycle_order_invalid` flag and does not receive the lifecycle bonus.
11. Re-run `python -m scorer` without changing inputs and confirm score totals, reasons, and flags stay the same across runs.

## Screener
1. Run the screener with `python -m screener`.
2. Confirm `data/filtered_snapshots.jsonl` exists.
3. Confirm the file is overwritten on each run rather than appended.
4. Confirm each line is valid JSON.
5. Confirm each filtered record includes all scored fields plus:
   - `quality_band`
   - `is_complete_record`
   - `has_blocking_flags`
   - `filter_version`
   - `filter_reasons`
6. Confirm a create-only snapshot with `score_total=6` and no blocking flags is classified as `partial`, not `strong`.
7. Confirm a record is only classified as `strong` when `score_total >= 7` and `has_blocking_flags=false`.
8. Confirm a migrated record with complete lifecycle data, no blocking flags, and high score can be classified as `strong`.
9. Confirm a record with `lifecycle_order_invalid` is not classified as `strong`.
10. Confirm `is_complete_record=true` only when create-side and migration-side essentials are both present together.
11. Confirm `filter_reasons` stay concise and explicit, such as `score_total>=7`, `no_blocking_flags`, `complete_record`, `blocking_flags_present`, or `incomplete_record`.
12. Confirm the screener prints a lightweight summary with total count, weak / partial / strong counts, blocking-flag count, and output path.

## Expected Result
At least one real pump.fun create event remains appended to `data/events.jsonl`, migration events are appended to `data/migration_events.jsonl` when observed, `python -m collector.snapshots` overwrites `data/snapshots.jsonl` with scorer-ready but non-scoring feature snapshots, `python -m scorer` overwrites `data/scored_snapshots.jsonl` with explainable scored records, and `python -m screener` overwrites `data/filtered_snapshots.jsonl` with explainable filtered records.
