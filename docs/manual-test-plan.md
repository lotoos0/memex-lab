# Manual Test Plan

## Goal
Verify that the M1 collector listens to pump.fun new token creation logs and appends normalized records to `data/events.jsonl`.

## Setup
1. Create a virtual environment.
2. Install the project in editable mode with `pip install -e .`.
3. Copy `.env.example` to `.env`.
4. Set `SOLANA_NODE_WSS_ENDPOINT` to a working Solana WebSocket RPC endpoint.

## Run
1. Start the collector with `python -m collector.main`.
2. Leave it running until at least one pump.fun token creation is observed.
3. Stop it with `Ctrl+C` after one or more records have been written.

## Verify Output
1. Confirm that `data/events.jsonl` exists.
2. Confirm that each line is valid JSON.
3. Confirm that a token creation record includes these fields:
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
7. Confirm that `raw_data_base64` is non-empty for parsed events.

## Decode Check Example
Use a short Python one-liner against a recorded line:

```bash
python -c "import base58, json; record=json.loads(open('data/events.jsonl', encoding='utf-8').readline()); print(len(base58.b58decode(record['mint'])))"
```

The decoded mint should produce bytes without raising an exception.

## Malformed Event Handling
1. Keep the collector running long enough to observe normal traffic.
2. Confirm the process continues running even if some logs do not parse into `TokenCreatedEvent`.
3. Confirm reconnect attempts happen after connection loss with a 5 second backoff.

## Reconnect Verification Procedure
1. Start the collector with `python -m collector.main`.
2. Wait until the startup logs show that the websocket subscription has been established.
3. Disconnect the machine from the network, disable the network adapter, or temporarily block the configured websocket endpoint.
4. Observe the collector logs and confirm the connection drops.
5. Confirm the collector does not exit after the disconnect.
6. Confirm a reconnect log appears and explicitly says it will retry in 5 seconds.
7. Restore network access or unblock the websocket endpoint.
8. Confirm the collector connects again and logs a fresh subscription confirmation.
9. Leave it running until at least one new event is processed after reconnection.

## Expected Result
At least one real pump.fun create event is appended to `data/events.jsonl` in normalized JSONL form without introducing scoring or execution behavior.
