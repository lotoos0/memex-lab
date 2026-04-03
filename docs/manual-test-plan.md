# Manual Test Plan

## Goal
Verify that the staged offline pipeline listens to pump.fun new token creation and migration logs, appends normalized records to JSONL files, builds offline snapshots in `data/snapshots.jsonl`, scores them into `data/scored_snapshots.jsonl`, filters them into `data/filtered_snapshots.jsonl`, supports offline review, export, and labeling through `reviewkit`, produces a count-based dataset audit report, and exposes a thin Tkinter console for running the existing offline tools.

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

## Scorer v0
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

## Scorer v1
1. Run the scorer v1 with `python -m scorer --score-version v1`.
2. Confirm `data/scored_snapshots_v1.jsonl` exists.
3. Confirm v1 output is written to a separate file and does not overwrite `data/scored_snapshots.jsonl`.
4. Confirm each v1 scored record includes the same schema as v0 and has `score_version="v1"`.
5. Confirm a create-only complete record that scored `6` in v0 now scores `5` in v1 because the lifecycle bonus is no longer awarded without a confirmed two-event lifecycle.
6. Confirm a migrated record with `created_at`, `migrated_at`, valid temporal order, and `migration_target` still scores `9` in v1.
7. Confirm a migration-only record receives the informational `migration_only` flag in v1.
8. Confirm v1 no longer emits these removed noisy flags:
   - `create_event_count_unexpected`
   - `migration_event_count_unexpected`
   - `source_count_unexpected`
   - `source_count_exceeds_event_count`
   - `missing_first_seen_at`
9. Re-run `python -m scorer --score-version v1` without changing inputs and confirm score totals, reasons, and flags stay the same across runs.

## Scorer Comparison v0 vs v1
1. Run the comparison with `python -m scorer compare`.
2. Confirm `data/reports/scorer_v0_vs_v1.json` exists.
3. Confirm the comparison report is aggregate-only and does not contain per-mint record dumps.
4. Confirm the report includes:
   - `overview`
   - `score_delta_distribution`
   - `score_band_distribution`
   - `flag_delta_summary`
5. Confirm the score delta distribution prominently shows `-1` for create-only records.
6. Confirm create-only complete records drop from `6` in v0 to `5` in v1.
7. Confirm migrated valid records remain at `9` in both versions.
8. Confirm `changed_score_band_count` is aggregate-only and uses the same screener thresholds and blocking definitions as before.
9. Re-run `python -m scorer compare` without changing inputs and confirm the count-based sections stay the same across runs, aside from the comparison timestamp.

## Scorer v2
1. Run the scorer v2 with `python -m scorer --score-version v2`.
2. Confirm `data/scored_snapshots_v2.jsonl` exists.
3. Confirm v2 output is written to a separate file and does not overwrite `data/scored_snapshots_v1.jsonl`.
4. Confirm each v2 scored record keeps the same schema as v1 and has `score_version="v2"`.
5. Confirm `has_create_event` now contributes `+1` instead of `+2`.
6. Confirm `bonding_curve_present (+1)` no longer appears in v2 `score_reasons`.
7. Confirm non-migrated records now receive the informational `no_migration_evidence` flag.
8. Confirm a complete migrated record with valid lifecycle order scores `7` in v2 and remains in the `strong` band.
9. Confirm re-running `python -m scorer --score-version v2` without changing inputs keeps score totals, reasons, and flags stable across runs.

## Scorer Comparison v1 vs v2
1. Run the comparison with `python -m scorer compare --left-version v1 --right-version v2`.
2. Confirm `data/reports/scorer_v1_vs_v2.json` exists.
3. Confirm the comparison report is aggregate-only and does not contain per-mint record dumps.
4. Confirm the report includes:
   - `overview`
   - `score_delta_distribution`
   - `score_band_distribution`
   - `flag_delta_summary`
5. Confirm `changed_score_count` is very high across shared records.
6. Confirm the score delta distribution is dominated by `-2`.
7. Confirm non-migrated records shift from `partial` toward `weak`.
8. Confirm complete migrated records remain `strong` at score `7`.
9. Confirm the added-flag counts include `no_migration_evidence`.
10. Re-run `python -m scorer compare --left-version v1 --right-version v2` without changing inputs and confirm the aggregate counts stay the same across runs, aside from the comparison timestamp.

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
10. Confirm `is_complete_record=true` only when `created_at`, `creator`, `bonding_curve`, `has_migrated=true`, and `migration_target` are all present together.
11. Confirm `filter_reasons` stay concise and explicit, such as `score_total>=7`, `no_blocking_flags`, `complete_record`, `blocking_flags_present`, or `incomplete_record`.
12. Confirm the screener prints a lightweight summary with total count, weak / partial / strong counts, blocking-flag count, and output path.

## Reviewkit Report
1. Run the report with `python -m reviewkit.report`.
2. Confirm it reads `data/filtered_snapshots.jsonl` by default.
3. Confirm it prints concise counts for:
   - total records
   - `quality_band`
   - `has_migrated`
   - `has_blocking_flags`
   - labels
   - `score_total`
4. Confirm the labels section includes unlabeled count and orphan-label count.

## Reviewkit Export
1. Run an explicit export such as `python -m reviewkit.export --quality-band strong --output-path data/exports/strong.jsonl`.
2. Confirm the export file is written as JSONL and overwritten on rerun.
3. Confirm the export command fails if no explicit filter is provided.
4. Confirm exported records are filtered only by the requested explicit conditions.
5. Confirm label-based export works when labels exist, for example `python -m reviewkit.export --label interesting --output-path data/exports/interesting.jsonl`.
6. Confirm `python -m reviewkit.export --min-score 7 --output-path data/exports/min-score-7.jsonl` exports only records with `score_total >= 7`.
7. Confirm `python -m reviewkit.export --quality-band partial --limit 5 --output-path data/exports/partial-top-5.jsonl` writes at most 5 records after applying the active filters.
8. Confirm combined filters keep AND logic, for example `--quality-band strong --has-migrated true --min-score 7 --limit 3` only exports records matching all active conditions before truncation.

## Reviewkit Label
1. Pick a mint that exists in `data/filtered_snapshots.jsonl`.
2. Set a label with `python -m reviewkit.label --mint <MINT> --label interesting`.
3. Confirm `data/labels/review_labels.jsonl` is created.
4. Confirm label records are stored separately from `data/filtered_snapshots.jsonl`.
5. Confirm each label record includes:
   - `mint`
   - `label`
   - `labeled_at`
6. Confirm setting the same mint again updates that mint entry instead of creating duplicates.
7. Confirm setting a label for a mint that does not exist in the filtered snapshots input fails with a clear error.
8. Confirm `python -m reviewkit.label --list` prints stored labels without requiring filtered-snapshot mint validation.
9. Confirm `python -m reviewkit.label --remove <MINT>` removes the stored label without requiring filtered-snapshot mint validation.
10. Confirm removing a missing mint does not mutate unrelated labels.
11. Confirm `python -m reviewkit.label --mint <MINT> --label interesting --note "manual follow-up"` stores `note` in the label record.
12. Confirm omitting `--note` still stores a valid label record without requiring a note field.

## Dataset Audit
1. Run the audit with `python -m audit`.
2. Confirm `data/reports/dataset_audit.json` exists.
3. Confirm the file is overwritten on each run rather than appended.
4. Confirm the audit reads `data/filtered_snapshots.jsonl` and optionally reads `data/labels/review_labels.jsonl` when present.
5. Run the audit once with a missing labels path, for example `python -m audit --labels-path data/labels/does-not-exist.jsonl`, and confirm it still writes a valid report with empty label-derived sections.
6. Confirm the audit JSON includes these sections:
   - `overview`
   - `quality_band_distribution`
   - `has_migrated_distribution`
   - `has_blocking_flags_distribution`
   - `lifecycle_coverage`
   - `score_total_distribution`
   - `flag_distribution`
   - `label_distribution`
   - `missing_field_distribution`
7. Confirm `overview` includes:
   - `total_records`
   - `total_labeled_records`
   - `total_migrated_records`
   - `total_blocking_records`
   - `total_complete_records`
8. Confirm `lifecycle_coverage` includes:
   - `created_at_present`
   - `created_at_missing`
   - `migrated_at_present`
   - `migrated_at_missing`
   - `full_lifecycle`
   - `create_only`
   - `migration_only`
9. Confirm `flag_distribution` includes per-flag counts and a `top_flags` list for the most frequent score flags.
10. Confirm `label_distribution` includes count by label, label x quality band, and label x has_migrated cross-tabs.
11. Confirm the stdout summary stays concise and human-readable and includes a labels line.
12. Confirm missing-field counts only treat these fields as audited: `created_at`, `creator`, `token_standard`, `bonding_curve`, `migration_target`, and `snapshot_built_at`.
13. Confirm missing-field counts only treat a field as missing when it is absent, `null`, or `""`.
14. Confirm fields with `0` or `false` are not counted as missing when the field is present.
15. Re-run `python -m audit` without changing inputs and confirm all count-based sections stay the same across runs, aside from the timestamp field in the report.
16. If labels exist, confirm `overview.orphan_label_count` reflects labels whose mints are not present in the filtered snapshots input.

## Candidate Selector
1. Prepare or provide `data/filtered_snapshots_v1.jsonl` before running the selector.
2. Run the selector with `python -m selector`.
3. Confirm `data/review_candidates.jsonl` exists.
4. Confirm the file is overwritten on each run rather than appended.
5. Confirm each candidate record includes:
   - `mint`
   - `candidate_class`
   - `candidate_reasons`
   - `selection_version`
   - `quality_band`
   - `score_version`
   - `score_total`
   - `score_reasons`
   - `score_flags`
   - `filter_reasons`
   - `has_migrated`
   - `has_blocking_flags`
   - `is_complete_record`
   - `created_at`
   - `migrated_at`
   - `token_standard`
   - `creator`
   - `migration_target`
   - `label`
   - `label_labeled_at`
   - `label_note`
6. Confirm the selector fails with a clear error if `data/filtered_snapshots_v1.jsonl` is missing.
7. Confirm the selector fails with a clear error if the input file exists but is empty or contains no valid records.
8. Confirm `suspect` forces `ignore_for_now`.
9. Confirm `interesting` only promotes `review_if_time` to `review_now` and does not rescue `ignore_for_now`.
10. Confirm records with blocking flags are classified as `ignore_for_now`.
11. Confirm records with `migration_only` in `score_flags` are classified as `ignore_for_now`.
12. Confirm `quality_band=strong` with no blocking flags and no `migration_only` flag is classified as `review_now`.
13. Confirm `quality_band=partial` with no blocking flags is classified as `review_if_time` unless promoted by `interesting`.
14. Confirm the stdout summary stays concise and includes total records processed, count by candidate class, label-influenced count, and output path.

## Candidate Selector v2
1. Run selector v2 with `python -m selector --selection-version v2`.
2. Confirm `data/review_candidates_v2.jsonl` exists.
3. Confirm v2 output is written to a separate file and does not overwrite `data/review_candidates.jsonl`.
4. Confirm each v2 candidate record keeps the same schema as selector v1.
5. Confirm a non-migrated partial record defaults to `ignore_for_now`.
6. Confirm an `interesting` label rescues a non-migrated partial record only to `review_if_time`, not `review_now`.
7. Confirm a `review_later` label rescues a non-migrated partial record to `review_if_time`.
8. Confirm a migrated partial record is classified as `review_now`.
9. Confirm `suspect`, blocking flags, `migration_only`, and `missing_lifecycle_coverage` still produce explicit `ignore_for_now` outcomes in v2.
10. Re-run `python -m selector --selection-version v2` without changing inputs and confirm the class counts and candidate reasons stay the same across runs.

## Selector Comparison
1. Run the comparison with `python -m selector compare`.
2. Confirm `data/reports/selector_v1_vs_v2.json` exists.
3. Confirm the comparison report is aggregate-only and does not contain per-mint candidate dumps.
4. Confirm the report includes:
   - `overview`
   - `candidate_class_distribution`
   - `class_transition_distribution`
   - `v2_rule_impact_summary`
5. Confirm the transition distribution shows non-migrated partial records moving from `review_if_time` or `review_now` in v1 toward `ignore_for_now` or `review_if_time` in v2.
6. Confirm `v2_rule_impact_summary` counts:
   - non-migrated partial default ignores
   - interesting rescues to `review_if_time`
   - `review_later` rescues to `review_if_time`
   - migrated partial records promoted to `review_now`
7. Confirm re-running `python -m selector compare` without changing inputs keeps the aggregate counts stable across runs, aside from the comparison timestamp.

## Selector Alignment
1. Run the alignment report with `python -m selector alignment`.
2. Confirm `data/reports/selector_scorer_alignment_v2.json` exists.
3. Confirm the alignment report is aggregate-only and does not contain per-mint dumps.
4. Confirm the report includes:
   - `overview`
   - `shared_scorer_band_from_scores_distribution`
   - `shared_selector_candidate_class_distribution`
   - `shared_scorer_band_from_scores_by_selector_candidate_class`
   - `shared_selector_candidate_class_by_scorer_band_from_scores`
   - `selector_v2_reason_distribution`
5. Confirm the field names make the data source explicit:
   - `scorer_band_from_scores` is derived locally from scorer output by mirroring screener band logic
   - `selector_candidate_class` comes from selector output
6. Confirm the shared-record counts in `overview` reflect only the overlap between scored v2 input and selector v2 input.
7. Confirm the current alignment finding is visible in the aggregate report:
   - `shared_scorer_band_from_scores_distribution.weak` is high on current data
   - weak scorer-v2 band records map mostly or entirely to `ignore_for_now` in `shared_scorer_band_from_scores_by_selector_candidate_class`
   - the `partial` scorer-v2 row in `shared_scorer_band_from_scores_by_selector_candidate_class` is zero or near-zero on current data
8. Confirm `selector_v2_reason_distribution` aggregates selector v2 `candidate_reasons` strings without listing raw mints.
9. Confirm the cross-tabs remain aggregate-only and do not include raw mint lists.
10. Rename or remove either alignment input file and confirm `python -m selector alignment` exits with a clear missing-file error instead of writing an empty report.
11. Re-run `python -m selector alignment` without changing inputs and confirm the aggregate counts stay the same across runs, aside from the report timestamp.

## Candidate Audit
1. Run candidateaudit with `python -m candidateaudit`.
2. Confirm `data/reports/candidate_audit.json` exists.
3. Confirm `data/review_queue_now.jsonl` exists.
4. Confirm `data/review_queue_if_time.jsonl` exists.
5. Confirm the report file and both queue files are overwritten on rerun.
6. Confirm `candidateaudit` exits with a clear error if `data/review_candidates.jsonl` is missing.
7. Confirm `candidateaudit` exits with a clear error if the input file exists but is empty or contains no valid records.
8. Confirm queue records are strict pass-through subsets of candidate records and are not reclassified or mutated.
9. Confirm `review_queue_now.jsonl` contains only records where `candidate_class = review_now`.
10. Confirm `review_queue_if_time.jsonl` contains only records where `candidate_class = review_if_time`.
11. Confirm the candidate audit JSON includes:
   - `candidate_totals`
   - `candidate_class_distribution`
   - `class_label_alignment`
   - `class_quality_context`
   - `queue_sizes`
   - `queue_usefulness_notes`
12. Confirm `candidate_totals` includes:
   - `total_records`
   - `total_review_now`
   - `total_review_if_time`
   - `total_ignore_for_now`
   - `total_labeled_records`
13. Confirm `candidate_class_distribution` includes count and percentage by candidate class.
14. Confirm `class_label_alignment` uses the embedded `label` field from `data/review_candidates.jsonl`.
15. Confirm `class_label_alignment` includes:
   - labels within each candidate class
   - `interesting` in `review_now`
   - `suspect` in `ignore_for_now`
   - unlabeled records in `review_now`
16. Confirm `class_quality_context` includes:
   - candidate_class x quality_band
   - candidate_class x has_blocking_flags
   - candidate_class x has_migrated
17. Confirm the stdout summary stays concise and includes total records, class counts, label-alignment highlights, queue sizes, and report path.
18. Confirm the code comments or docs clearly note that if labels change, `selector` must be re-run before `candidateaudit`.

## Review Feedback
1. Record a review outcome with `python -m reviewfeedback.record --mint <MINT> --outcome useful`.
2. Confirm `data/review_outcomes.jsonl` is created.
3. Confirm each outcome record includes:
   - `mint`
   - `candidate_class`
   - `outcome`
   - `reviewed_at`
4. Confirm the stored outcome record includes `note` only when `--note` is provided with a non-empty value.
5. Confirm recording the same mint again updates the existing outcome record instead of creating duplicates.
6. Confirm `python -m reviewfeedback.record --mint <MINT> --outcome noise --note "not worth the time"` stores the optional note.
7. Confirm the outcome recorder fails with a clear error if `data/review_candidates.jsonl` is missing.
8. Confirm the outcome recorder fails with a clear error if the mint does not exist in the candidate input.
9. Run the feedback report with `python -m reviewfeedback.report`.
10. Confirm `data/reports/review_feedback_report.json` exists.
11. Confirm the report is overwritten on rerun rather than appended.
12. Confirm the report includes:
   - `totals`
   - `candidate_class_by_outcome`
   - `label_by_outcome`
   - `effectiveness_indicators`
13. Confirm `totals` includes:
   - `total_reviewed_records`
   - `total_useful`
   - `total_noise`
   - `total_needs_more_context`
14. Confirm `candidate_class_by_outcome` includes rows for:
   - `review_now`
   - `review_if_time`
   - `ignore_for_now`
15. Confirm `effectiveness_indicators` includes:
   - `useful_rate_in_review_now`
   - `noise_rate_in_review_if_time`
   - `unlabeled_reviewed_count`
16. Remove or rename `data/review_outcomes.jsonl`, run `python -m reviewfeedback.report`, and confirm it still writes a valid zero-state report.
17. In the zero-state report, confirm:
   - `total_reviewed_records = 0`
   - all outcome counts are `0`
   - `candidate_class_by_outcome` contains only zero counts
   - `label_by_outcome` is empty
   - rate fields are `null`
18. Rename or remove `data/review_candidates.jsonl`, run `python -m reviewfeedback.report`, and confirm it still runs cleanly using an empty candidate map.
19. Confirm the stdout summary stays concise and still runs cleanly in the zero-state case.

## Review Export
1. Run `python -m reviewexport --source queue-now`.
2. Confirm it reads `data/review_queue_now_v2.jsonl`.
3. Confirm it writes a compact JSONL export to `data/exports/review_queue_now.jsonl`.
4. Confirm the export file is overwritten on rerun rather than appended.
5. Confirm exported records are sorted by `mint`.
6. Confirm each exported record uses a stable compact schema and includes:
   - `review_source`
   - `mint`
   - `candidate_class`
   - `quality_band`
   - `score_version`
   - `score_total`
   - `has_migrated`
   - `has_blocking_flags`
   - `token_standard`
   - `creator`
   - `migration_target`
   - `created_at`
   - `migrated_at`
   - `label`
   - `label_note`
   - `candidate_reasons`
   - `score_flags`
7. Run `python -m reviewexport --source queue-if-time --format csv`.
8. Confirm it writes `data/exports/review_queue_if_time.csv`.
9. Confirm CSV list fields are serialized as pipe-joined strings rather than Python list reprs.
10. Confirm empty list fields become empty strings in CSV output.
11. Run `python -m reviewexport --source candidates --candidate-class review_now`.
12. Confirm it reads `data/review_candidates_v2.jsonl`.
13. Confirm it exports only candidate records where `candidate_class=review_now`.
14. Confirm `--candidate-class` fails with a clear error when used with `--source queue-now` or `--source queue-if-time`.
15. Rename or remove one source file and confirm `python -m reviewexport --source ...` exits with a clear missing-file error instead of writing empty output.
16. Re-run the same export without changing inputs and confirm the output order remains deterministic.

## Review Loop Metrics
1. Run `python -m reviewloopmetrics`.
2. Confirm it reads `data/review_candidates_v2.jsonl` as the primary source.
3. Confirm it writes `data/reports/review_loop_metrics.json`.
4. Confirm the report file is overwritten on rerun rather than appended.
5. Confirm the report is aggregate-only and does not contain per-mint dumps.
6. Confirm the report includes:
   - `candidate_funnel`
   - `review_coverage`
   - `outcome_distribution`
   - `outcome_by_candidate_class`
   - `label_interaction_summary`
   - `sample_size_note`
7. Confirm `candidate_funnel` includes:
   - `total_candidate_records`
   - `total_review_now`
   - `total_review_if_time`
   - `total_ignore_for_now`
8. Confirm `review_coverage` includes:
   - `total_reviewed_records`
   - `reviewed_share_of_all_candidates`
   - `reviewed_share_of_review_now_candidates`
   - `reviewed_share_of_review_if_time_candidates`
9. Confirm `outcome_distribution` includes:
   - `useful_count`
   - `noise_count`
   - `needs_more_context_count`
   - `useful_rate`
   - `noise_rate`
10. Confirm `label_interaction_summary` includes:
   - `reviewed_labeled_count`
   - `reviewed_unlabeled_count`
   - `reviewed_outcomes_by_label`
11. Rename or remove `data/review_outcomes.jsonl`, run `python -m reviewloopmetrics`, and confirm it still writes a valid sparse report instead of crashing.
12. In that sparse case, confirm all reviewed counts are `0`, all outcome counts are `0`, and all rate fields remain `null`.
13. Confirm `sample_size_note` is a simple rule-based value:
   - `low` for very small reviewed counts
   - `moderate` for mid-sized reviewed counts
   - `sufficient` for larger reviewed counts
14. Confirm the stdout summary stays concise and includes top-line candidate counts, reviewed count, outcome counts, useful rate, and sample size note.
15. Re-run `python -m reviewloopmetrics` without changing inputs and confirm the aggregate counts remain stable across runs.

## Operator Snapshot
1. Run `python -m operatorsnapshot`.
2. Confirm it writes `data/reports/operator_snapshot.json`.
3. Confirm the snapshot is aggregate-only and does not duplicate full nested source report sections.
4. Confirm `candidate_state` comes from `data/reports/candidate_audit_v2.json`.
5. Confirm `review_loop_state` comes from `data/reports/review_loop_metrics.json`.
6. Confirm `alignment_state` comes from `data/reports/selector_scorer_alignment_v2.json`.
7. Confirm `feedback_state` comes from `data/reports/review_feedback_report.json`.
8. Confirm the snapshot includes `snapshot_completeness` with presence flags for all four source reports.
9. Rename or remove one source report and confirm `python -m operatorsnapshot` still writes a valid sparse snapshot instead of crashing.
10. In that sparse case, confirm the affected section becomes null/sparse while other available sections remain populated.
11. Confirm the stdout summary stays concise and includes logical content groups for:
   - candidate state
   - review loop state
   - alignment state
   - source report completeness
12. Re-run `python -m operatorsnapshot` without changing inputs and confirm all snapshot values except `generated_at` remain stable across runs.

## Pipeline Health
1. Run `python -m pipelinehealth`.
2. Confirm it writes `data/reports/pipeline_health.json`.
3. Confirm the report includes:
   - `overall_status`
   - `artifact_status`
   - `ordering_checks`
   - `missing_artifacts`
   - `warnings`
4. Confirm `artifact_status` includes the fixed tracked artifact set only and each entry includes:
   - `path`
   - `present`
   - `modified_at`
   - `age_seconds`
5. Confirm missing artifact metadata stays `null` rather than using fake zero values.
6. Confirm optional artifacts are non-blocking when missing.
7. Confirm ordering checks are skipped when one or more required artifacts for that check are missing.
8. Confirm ordering checks use strict `>` comparisons rather than `>=`.
9. Change one artifact mtime using any equivalent local method and confirm an ordering warning appears when a downstream artifact becomes older than its upstream dependency.
10. Confirm readiness rules stay simple and explicit:
   - `not_ready` when one or more core artifacts are missing
   - `degraded` when all core artifacts are present but warnings exist
   - `ready` when all core artifacts are present and no warnings exist
11. Confirm warning messages stay short and operator-facing.
12. Re-run `python -m pipelinehealth` without changing inputs and confirm:
   - `generated_at` changes
   - `artifact_status[*].age_seconds` changes
   - all other values remain stable across runs.
13. Confirm stdout stays concise and includes readiness state, missing required artifact count, warning count, and the top issue when present.

## Ops Console
1. Run the console with `python -m console`.
2. Confirm a single Tkinter window opens and remains responsive while idle.
3. Confirm the window includes:
   - fixed command buttons for offline pipeline tools
   - workflow buttons inside the Commands section
   - a file status section
   - a label form
   - a review outcome form
   - a command log
4. Confirm the file status section does not auto-refresh continuously.
5. Click `Refresh status` and confirm the file status table updates manually.
6. Run a short command such as `Build snapshots` or `Review report` and confirm the UI stays responsive while the command runs.
7. Confirm the file status section refreshes after a command completes.
8. Confirm the command log shows:
   - the invoked `python -m ...` command
   - the exit code
   - captured stdout
   - captured stderr when present
9. Use the label form to set a label and confirm it succeeds through `reviewkit.label`.
10. Use the label form to list labels and confirm the output appears in the command log.
11. Use the label form to remove a label and confirm it succeeds through `reviewkit.label`.
12. Use the review outcome form to store an outcome and confirm it succeeds through `reviewfeedback.record`.
13. Confirm the label form keeps the current `reviewkit.label` default input-path behavior and does not expose path-selection controls in v0.
14. Confirm the Commands frame includes a `Workflows` section with exactly these buttons:
   - `full_v2_review_flow`
   - `refresh_candidates_only`
   - `feedback_report_only`
15. Click `feedback_report_only` and confirm the console launches `python -m orchestrator --workflow feedback_report_only` through the existing command runner.
16. Confirm workflow stdout and stderr appear in the existing command log panel rather than in a separate output area.
17. Confirm file status refreshes after a workflow completes, just like the existing command buttons.
18. Confirm only one command can run at a time and the console rejects overlapping starts with a clear message for workflow buttons as well as the existing buttons and forms.
19. Confirm the window includes a read-only `Review queue` section inside the existing main console window.
20. Confirm the queue section reads from:
   - `data/review_queue_now_v2.jsonl`
   - `data/review_queue_if_time_v2.jsonl`
21. Confirm queue records appear in a simple selectable list that includes queue source, mint, `candidate_class`, `quality_band`, score, and label.
22. Confirm the list may truncate mint display for readability, while the full mint remains available in the detail preview and form fields.
23. Select a queue record and confirm the detail preview shows the full mint and a read-only JSON preview of the selected record.
24. Confirm the read-only JSON preview does not include the console-injected `_queue_name` field.
25. Confirm selecting a queue record autofills the existing label mint field and the existing review outcome mint field with the full mint value.
26. Refresh status or complete a command while the selected queue record still exists and confirm the selection stays on that same record instead of jumping back to item 0.
27. Click `Next item` and confirm queue navigation advances only when explicitly requested.
28. Confirm storing a label or review outcome does not auto-advance to the next queue record.
29. Rename or remove one v2 queue file and confirm the queue detail area shows a clear missing-file message instead of crashing.
30. Click `Refresh queues` after restoring the file and confirm the list and detail preview reload cleanly.

## Pipeline Orchestrator
1. Change into the project root directory before running the orchestrator.
2. Run `python -m orchestrator --list`.
3. Confirm the output lists exactly these three workflows:
   - `full_v2_review_flow`
   - `refresh_candidates_only`
   - `feedback_report_only`
4. Confirm the list output includes a short purpose and step count for each workflow.
5. Run `python -m orchestrator --workflow feedback_report_only`.
6. Confirm it runs exactly one step:
   - `python -m reviewfeedback.report`
7. Confirm the final summary includes:
   - `workflow=feedback_report_only`
   - total step count
   - passed step count
   - `failed_step=none`
   - `status=success`
8. Run `python -m orchestrator --workflow refresh_candidates_only`.
9. Confirm it runs exactly these steps in order:
   - `python -m selector --selection-version v2`
   - `python -m candidateaudit --input-path data/review_candidates_v2.jsonl --report-output-path data/reports/candidate_audit_v2.json --queue-now-output-path data/review_queue_now_v2.jsonl --queue-if-time-output-path data/review_queue_if_time_v2.jsonl`
10. Confirm it stops immediately if the selector step fails and does not run candidateaudit afterward.
11. Confirm a failure summary includes the exact failing command and exit status.
12. Run `python -m orchestrator --workflow full_v2_review_flow`.
13. Confirm it runs exactly these steps in order:
   - `python -m scorer --score-version v2`
   - `python -m selector --selection-version v2`
   - `python -m candidateaudit --input-path data/review_candidates_v2.jsonl --report-output-path data/reports/candidate_audit_v2.json --queue-now-output-path data/review_queue_now_v2.jsonl --queue-if-time-output-path data/review_queue_if_time_v2.jsonl`
   - `python -m reviewfeedback.report`
14. Confirm the final success summary includes the expected v2 output paths:
   - `data/scored_snapshots_v2.jsonl`
   - `data/review_candidates_v2.jsonl`
   - `data/reports/candidate_audit_v2.json`
   - `data/review_queue_now_v2.jsonl`
   - `data/review_queue_if_time_v2.jsonl`
   - `data/reports/review_feedback_report.json`
15. Change into a non-project directory and run `python -m orchestrator --workflow feedback_report_only`.
16. Confirm the command exits with a clear project-root working-directory error instead of trying to run with hidden cwd correction.

## Expected Result
At least one real pump.fun create event remains appended to `data/events.jsonl`, migration events are appended to `data/migration_events.jsonl` when observed, `python -m collector.snapshots` overwrites `data/snapshots.jsonl` with scorer-ready but non-scoring feature snapshots, `python -m scorer` overwrites `data/scored_snapshots.jsonl` with explainable v0 scored records, `python -m scorer --score-version v1` overwrites `data/scored_snapshots_v1.jsonl` with explainable v1 scored records, `python -m scorer --score-version v2` overwrites `data/scored_snapshots_v2.jsonl` with explainable v2 scored records, `python -m scorer compare` preserves the v0 vs v1 aggregate report in `data/reports/scorer_v0_vs_v1.json`, `python -m scorer compare --left-version v1 --right-version v2` overwrites `data/reports/scorer_v1_vs_v2.json` with an aggregate comparison report, `python -m screener` overwrites `data/filtered_snapshots.jsonl` with explainable filtered records, `reviewkit` provides separate offline report, export, and label flows without mutating upstream pipeline outputs, `python -m audit` overwrites `data/reports/dataset_audit.json` with a concise count-based audit report, `python -m selector` preserves the existing candidate output in `data/review_candidates.jsonl`, `python -m selector --selection-version v2` writes precision-first selector v2 output to `data/review_candidates_v2.jsonl`, `python -m selector compare` overwrites `data/reports/selector_v1_vs_v2.json` with an aggregate comparison report, `python -m selector alignment` overwrites `data/reports/selector_scorer_alignment_v2.json` with an aggregate selector/scorer alignment report, `python -m candidateaudit` overwrites `data/reports/candidate_audit.json`, `data/review_queue_now.jsonl`, and `data/review_queue_if_time.jsonl` with deterministic candidate-audit outputs, `python -m reviewfeedback.report` overwrites `data/reports/review_feedback_report.json` with a deterministic manual-review feedback report while `python -m reviewfeedback.record` updates `data/review_outcomes.jsonl` by mint, `python -m reviewexport --source <queue-now|queue-if-time|candidates>` exports deterministic compact review-ready JSONL or CSV records from the existing v2 review sources, `python -m reviewloopmetrics` overwrites `data/reports/review_loop_metrics.json` with an aggregate review-loop funnel and coverage report, `python -m operatorsnapshot` overwrites `data/reports/operator_snapshot.json` with a compact aggregate snapshot over the existing source reports, `python -m pipelinehealth` overwrites `data/reports/pipeline_health.json` with a compact readiness and freshness report over a fixed artifact set, `python -m console` opens a single-window Tkinter wrapper that runs the existing offline CLI tools without duplicating their business logic and includes a read-only review queue preview for the v2 queue files, and `python -m orchestrator --workflow <name>` runs one of three explicit offline workflows from the project root while stopping on the first failed step and printing a concise operational summary.
