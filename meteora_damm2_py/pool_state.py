from dataclasses import dataclass
from typing import List
from construct import Container, Struct, Int8ul, Int16ul, Int32ul, Int64ul, Array, Bytes, Padding
from construct.core import Construct
from solders.pubkey import Pubkey  # type: ignore

class Int128ul(Construct):
    def _parse(self, stream, context, path):
        data = stream.read(16)
        return int.from_bytes(data, byteorder="little")

    def _build(self, obj, stream, context, path):
        stream.write(obj.to_bytes(16, byteorder="little"))
        return obj

    def _sizeof(self, context, path):
        return 16

BASE_FEE_STRUCT_LAYOUT = Struct(
    "cliff_fee_numerator"   / Int64ul,
    "fee_scheduler_mode"    / Int8ul,
    "padding_0"             / Array(5, Int8ul),
    "number_of_period"      / Int16ul,
    "period_frequency"      / Int64ul,
    "reduction_factor"      / Int64ul,
    "padding_1"             / Int64ul,
)

DYNAMIC_FEE_STRUCT_LAYOUT = Struct(
    "initialized"                 / Int8ul,
    "padding"                     / Array(7, Int8ul),
    "max_volatility_accumulator"  / Int32ul,
    "variable_fee_control"        / Int32ul,
    "bin_step"                    / Int16ul,
    "filter_period"               / Int16ul,
    "decay_period"                / Int16ul,
    "reduction_factor"            / Int16ul,
    "last_update_timestamp"       / Int64ul,
    "bin_step_u128"               / Int128ul(),
    "sqrt_price_reference"        / Int128ul(),
    "volatility_accumulator"      / Int128ul(),
    "volatility_reference"        / Int128ul(),
)

POOL_FEES_STRUCT_LAYOUT = Struct(
    "base_fee"               / BASE_FEE_STRUCT_LAYOUT,
    "protocol_fee_percent"   / Int8ul,
    "partner_fee_percent"    / Int8ul,
    "referral_fee_percent"   / Int8ul,
    "padding_0"              / Array(5, Int8ul),
    "dynamic_fee"            / DYNAMIC_FEE_STRUCT_LAYOUT,
    "padding_1"              / Array(2, Int64ul),
)

POOL_METRICS_LAYOUT = Struct(
    "total_lp_a_fee"        / Int128ul(),
    "total_lp_b_fee"        / Int128ul(),
    "total_protocol_a_fee"  / Int64ul,
    "total_protocol_b_fee"  / Int64ul,
    "total_partner_a_fee"   / Int64ul,
    "total_partner_b_fee"   / Int64ul,
    "total_position"        / Int64ul,
    "padding"               / Int64ul,
)

REWARD_INFO_LAYOUT = Struct(
    "initialized"                                  / Int8ul,
    "reward_token_flag"                            / Int8ul,
    "_padding_0"                                   / Array(6, Int8ul),
    "_padding_1"                                   / Array(8, Int8ul),
    "mint"                                         / Bytes(32),
    "vault"                                        / Bytes(32),
    "funder"                                       / Bytes(32),
    "reward_duration"                              / Int64ul,
    "reward_duration_end"                          / Int64ul,
    "reward_rate"                                  / Int128ul(),
    "reward_per_token_stored"                      / Bytes(32),
    "last_update_time"                             / Int64ul,
    "cumulative_seconds_with_empty_liquidity_reward" / Int64ul,
)

POOL_LAYOUT = Struct(
    Padding(8),
    "pool_fees"                   / POOL_FEES_STRUCT_LAYOUT,
    "token_a_mint"                / Bytes(32),
    "token_b_mint"                / Bytes(32),
    "token_a_vault"               / Bytes(32),
    "token_b_vault"               / Bytes(32),
    "whitelisted_vault"           / Bytes(32),
    "partner"                     / Bytes(32),
    "liquidity"                   / Int128ul(),
    "_padding"                    / Int128ul(),
    "protocol_a_fee"              / Int64ul,
    "protocol_b_fee"              / Int64ul,
    "partner_a_fee"               / Int64ul,
    "partner_b_fee"               / Int64ul,
    "sqrt_min_price"              / Int128ul(),
    "sqrt_max_price"              / Int128ul(),
    "sqrt_price"                  / Int128ul(),
    "activation_point"            / Int64ul,
    "activation_type"             / Int8ul,
    "pool_status"                 / Int8ul,
    "token_a_flag"                / Int8ul,
    "token_b_flag"                / Int8ul,
    "collect_fee_mode"            / Int8ul,
    "pool_type"                   / Int8ul,
    "_padding_0"                  / Array(2, Int8ul),
    "fee_a_per_liquidity"         / Bytes(32),
    "fee_b_per_liquidity"         / Bytes(32),
    "permanent_lock_liquidity"    / Int128ul(),
    "metrics"                     / POOL_METRICS_LAYOUT,
    "creator"                     / Bytes(32),
    "_padding_1"                  / Array(6, Int64ul),
    "reward_infos"                / Array(2, REWARD_INFO_LAYOUT),
)

@dataclass
class BaseFeeStruct:
    cliff_fee_numerator: int
    fee_scheduler_mode: int
    padding_0: List[int]
    number_of_period: int
    period_frequency: int
    reduction_factor: int
    padding_1: int

@dataclass
class DynamicFeeStruct:
    initialized: int
    padding: List[int]
    max_volatility_accumulator: int
    variable_fee_control: int
    bin_step: int
    filter_period: int
    decay_period: int
    reduction_factor: int
    last_update_timestamp: int
    bin_step_u128: int
    sqrt_price_reference: int
    volatility_accumulator: int
    volatility_reference: int

@dataclass
class PoolFeesStruct:
    base_fee: BaseFeeStruct
    protocol_fee_percent: int
    partner_fee_percent: int
    referral_fee_percent: int
    padding_0: List[int]
    dynamic_fee: DynamicFeeStruct
    padding_1: List[int]

@dataclass
class PoolMetrics:
    total_lp_a_fee: int
    total_lp_b_fee: int
    total_protocol_a_fee: int
    total_protocol_b_fee: int
    total_partner_a_fee: int
    total_partner_b_fee: int
    total_position: int
    padding: int

@dataclass
class RewardInfo:
    initialized: int
    reward_token_flag: int
    _padding_0: List[int]
    _padding_1: List[int]
    mint: Pubkey
    vault: Pubkey
    funder: Pubkey
    reward_duration: int
    reward_duration_end: int
    reward_rate: int
    reward_per_token_stored: bytes
    last_update_time: int
    cumulative_seconds_with_empty_liquidity_reward: int

@dataclass
class Pool:
    pool: Pubkey
    pool_fees: PoolFeesStruct
    token_a_mint: Pubkey
    token_b_mint: Pubkey
    token_a_vault: Pubkey
    token_b_vault: Pubkey
    whitelisted_vault: Pubkey
    partner: Pubkey
    liquidity: int
    _padding: int
    protocol_a_fee: int
    protocol_b_fee: int
    partner_a_fee: int
    partner_b_fee: int
    sqrt_min_price: int
    sqrt_max_price: int
    sqrt_price: int
    activation_point: int
    activation_type: int
    pool_status: int
    token_a_flag: int
    token_b_flag: int
    collect_fee_mode: int
    pool_type: int
    _padding_0: List[int]
    fee_a_per_liquidity: bytes
    fee_b_per_liquidity: bytes
    permanent_lock_liquidity: int
    metrics: PoolMetrics
    creator: Pubkey
    _padding_1: List[int]
    reward_infos: List[RewardInfo]

def parse_pool(pool_pubkey: Pubkey, c: Container) -> Pool:
    return Pool(
        pool=pool_pubkey,
        pool_fees=PoolFeesStruct(
            base_fee=BaseFeeStruct(
                cliff_fee_numerator=c.pool_fees.base_fee.cliff_fee_numerator,
                fee_scheduler_mode=c.pool_fees.base_fee.fee_scheduler_mode,
                padding_0=list(c.pool_fees.base_fee.padding_0),
                number_of_period=c.pool_fees.base_fee.number_of_period,
                period_frequency=c.pool_fees.base_fee.period_frequency,
                reduction_factor=c.pool_fees.base_fee.reduction_factor,
                padding_1=c.pool_fees.base_fee.padding_1,
            ),
            protocol_fee_percent=c.pool_fees.protocol_fee_percent,
            partner_fee_percent=c.pool_fees.partner_fee_percent,
            referral_fee_percent=c.pool_fees.referral_fee_percent,
            padding_0=list(c.pool_fees.padding_0),
            dynamic_fee=DynamicFeeStruct(
                initialized=c.pool_fees.dynamic_fee.initialized,
                padding=list(c.pool_fees.dynamic_fee.padding),
                max_volatility_accumulator=c.pool_fees.dynamic_fee.max_volatility_accumulator,
                variable_fee_control=c.pool_fees.dynamic_fee.variable_fee_control,
                bin_step=c.pool_fees.dynamic_fee.bin_step,
                filter_period=c.pool_fees.dynamic_fee.filter_period,
                decay_period=c.pool_fees.dynamic_fee.decay_period,
                reduction_factor=c.pool_fees.dynamic_fee.reduction_factor,
                last_update_timestamp=c.pool_fees.dynamic_fee.last_update_timestamp,
                bin_step_u128=c.pool_fees.dynamic_fee.bin_step_u128,
                sqrt_price_reference=c.pool_fees.dynamic_fee.sqrt_price_reference,
                volatility_accumulator=c.pool_fees.dynamic_fee.volatility_accumulator,
                volatility_reference=c.pool_fees.dynamic_fee.volatility_reference,
            ),
            padding_1=list(c.pool_fees.padding_1),
        ),
        token_a_mint=Pubkey.from_bytes(c.token_a_mint),
        token_b_mint=Pubkey.from_bytes(c.token_b_mint),
        token_a_vault=Pubkey.from_bytes(c.token_a_vault),
        token_b_vault=Pubkey.from_bytes(c.token_b_vault),
        whitelisted_vault=Pubkey.from_bytes(c.whitelisted_vault),
        partner=Pubkey.from_bytes(c.partner),
        liquidity=c.liquidity,
        _padding=c._padding,
        protocol_a_fee=c.protocol_a_fee,
        protocol_b_fee=c.protocol_b_fee,
        partner_a_fee=c.partner_a_fee,
        partner_b_fee=c.partner_b_fee,
        sqrt_min_price=c.sqrt_min_price,
        sqrt_max_price=c.sqrt_max_price,
        sqrt_price=c.sqrt_price,
        activation_point=c.activation_point,
        activation_type=c.activation_type,
        pool_status=c.pool_status,
        token_a_flag=c.token_a_flag,
        token_b_flag=c.token_b_flag,
        collect_fee_mode=c.collect_fee_mode,
        pool_type=c.pool_type,
        _padding_0=list(c._padding_0),
        fee_a_per_liquidity=c.fee_a_per_liquidity,
        fee_b_per_liquidity=c.fee_b_per_liquidity,
        permanent_lock_liquidity=c.permanent_lock_liquidity,
        metrics=PoolMetrics(
            total_lp_a_fee=c.metrics.total_lp_a_fee,
            total_lp_b_fee=c.metrics.total_lp_b_fee,
            total_protocol_a_fee=c.metrics.total_protocol_a_fee,
            total_protocol_b_fee=c.metrics.total_protocol_b_fee,
            total_partner_a_fee=c.metrics.total_partner_a_fee,
            total_partner_b_fee=c.metrics.total_partner_b_fee,
            total_position=c.metrics.total_position,
            padding=c.metrics.padding,
        ),
        creator=Pubkey.from_bytes(c.creator),
        _padding_1=list(c._padding_1),
        reward_infos=[
            RewardInfo(
                initialized=ri.initialized,
                reward_token_flag=ri.reward_token_flag,
                _padding_0=list(ri._padding_0),
                _padding_1=list(ri._padding_1),
                mint=Pubkey.from_bytes(ri.mint),
                vault=Pubkey.from_bytes(ri.vault),
                funder=Pubkey.from_bytes(ri.funder),
                reward_duration=ri.reward_duration,
                reward_duration_end=ri.reward_duration_end,
                reward_rate=ri.reward_rate,
                reward_per_token_stored=ri.reward_per_token_stored,
                last_update_time=ri.last_update_time,
                cumulative_seconds_with_empty_liquidity_reward=ri.cumulative_seconds_with_empty_liquidity_reward,
            )
            for ri in c.reward_infos
        ],
    )
