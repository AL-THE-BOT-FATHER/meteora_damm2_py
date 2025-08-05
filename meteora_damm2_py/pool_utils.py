from typing import Optional
from solana.rpc.api import Client
from solders.pubkey import Pubkey  # type: ignore

from solana.rpc.commitment import Processed
from solana.rpc.types import MemcmpOpts

from constants import METEORA_DAMM2_PROGRAM
from pool_state import POOL_LAYOUT, parse_pool


def fetch_pool_state(client: Client, pool_str: str):
    pool_pubkey = Pubkey.from_string(pool_str)
    info = client.get_account_info_json_parsed(pool_pubkey)
    raw_data = info.value.data
    decoded = POOL_LAYOUT.parse(raw_data)
    return parse_pool(pool_pubkey, decoded)


def fetch_pool_from_rpc(
    client: Client,
    base_mint: str,
    quote_mint: str = "So11111111111111111111111111111111111111112",
) -> Optional[str]:
    try:
        f_base = MemcmpOpts(offset=168, bytes=base_mint)
        f_quote = MemcmpOpts(offset=200, bytes=quote_mint)

        resp = client.get_program_accounts(
            METEORA_DAMM2_PROGRAM,
            commitment=Processed,
            filters=[f_base, f_quote],
        )

        best: Optional[str] = None
        max_liq = -1
        for acct in resp.value:
            pk = acct.pubkey
            state = fetch_pool_state(client, str(pk))
            if state.liquidity > max_liq:
                max_liq = state.liquidity
                best = str(pk)
        return best
    except:
        return None
