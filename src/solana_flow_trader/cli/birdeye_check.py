"""Perform a small read-only Birdeye connectivity check."""

from __future__ import annotations

import os
import sys

from solana_flow_trader.providers.birdeye import (
    BirdeyeClient,
    BirdeyeClientError,
    BirdeyeProvider,
)


def main() -> int:
    api_key = os.environ.get("BIRDEYE_API_KEY", "").strip()

    if not api_key:
        print(
            "BIRDEYE_API_KEY is not configured.",
            file=sys.stderr,
        )
        return 2

    try:
        with BirdeyeClient(api_key=api_key) as client:
            provider = BirdeyeProvider(client=client)

            candidates = provider.discover_tokens(limit=5)

            print("Birdeye connection: OK")
            print(f"Candidates returned: {len(candidates)}")
            print()

            for index, candidate in enumerate(candidates, start=1):
                print(
                    f"{index}. "
                    f"{candidate.symbol or 'UNKNOWN'} "
                    f"{candidate.token_mint}"
                )
                print(
                    f"   market_cap={candidate.market_cap_usd} "
                    f"liquidity={candidate.liquidity_usd} "
                    f"volume_24h={candidate.volume_24h_usd}"
                )

            if not candidates:
                print("No candidates were returned.")
                return 0

            selected = candidates[0]

            print()
            print(
                "Requesting overview for "
                f"{selected.symbol or selected.token_mint}..."
            )

            snapshot = provider.get_snapshot(
                selected.token_mint
            )

            print()
            print("Snapshot:")
            print(f"  token       = {snapshot.token_mint}")
            print(f"  symbol      = {snapshot.symbol}")
            print(f"  timestamp   = {snapshot.timestamp_utc.isoformat()}")
            print(f"  price       = {snapshot.price_usd}")
            print(f"  market cap  = {snapshot.market_cap_usd}")
            print(f"  liquidity   = {snapshot.liquidity_usd}")
            print(f"  volume      = {snapshot.volume_usd}")
            print(f"  buy volume  = {snapshot.buy_volume_usd}")
            print(f"  sell volume = {snapshot.sell_volume_usd}")
            print(f"  buys        = {snapshot.buys}")
            print(f"  sells       = {snapshot.sells}")
            print(f"  txs         = {snapshot.transactions}")
            print(f"  source      = {snapshot.source}")

    except BirdeyeClientError as exc:
        print(
            f"Birdeye connectivity check failed: {exc}",
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        print(
            f"Birdeye data could not be normalized: {exc}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
