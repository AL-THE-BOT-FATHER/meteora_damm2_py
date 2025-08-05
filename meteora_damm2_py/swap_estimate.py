from enum import Enum
from decimal import Decimal, getcontext
from typing import NamedTuple, Optional

getcontext().prec = 50

BASIS_POINT_MAX                    = 10_000      # e.g. 10000 bps = 100%
FEE_DENOMINATOR                    = 1_000_000_000  # if your fees are out of 1e9
MAX_FEE_NUMERATOR                  = 500_000_000  # or whatever your protocol max is
SCALE_OFFSET                       = 64          # Q64.64 fixed-point

class FeeSchedulerMode(Enum):
    Constant    = 0
    Linear      = 1
    Exponential = 2

class Rounding(Enum):
    Down = 0
    Up   = 1

class FeeMode(NamedTuple):
    fee_on_input: bool
    fees_on_token_a: bool

class SwapResult(NamedTuple):
    amount_out: int
    total_fee: int
    next_sqrt_price: int

def mul_div(numer: int, mul: int, denom: int, rounding: Rounding) -> int:
    prod = numer * mul
    if rounding == Rounding.Up:
        return (prod + denom - 1) // denom
    else:
        return prod // denom

def get_next_sqrt_price(amount: int, sqrt_price: int, liquidity: int, a_to_b: bool) -> int:
    if a_to_b:
        product     = amount * sqrt_price
        denominator = liquidity + product
        numerator   = liquidity * sqrt_price
        return (numerator + (denominator - 1)) // denominator
    else:
        quotient = (amount << (SCALE_OFFSET * 2)) // liquidity
        return sqrt_price + quotient

def get_amount_a_from_liquidity_delta(
    liquidity: int, cur_sp: int, max_sp: int, rounding: Rounding
) -> int:
    product     = liquidity * (max_sp - cur_sp)
    denominator = cur_sp * max_sp
    if rounding == Rounding.Up:
        return (product + (denominator - 1)) // denominator
    return product // denominator

def get_amount_b_from_liquidity_delta(
    liquidity: int, cur_sp: int, min_sp: int, rounding: Rounding
) -> int:
    one         = 1 << (SCALE_OFFSET * 2)
    delta_price = cur_sp - min_sp
    result      = liquidity * delta_price
    if rounding == Rounding.Up:
        return (result + (one - 1)) // one
    return result >> (SCALE_OFFSET * 2)

def get_next_sqrt_price_from_output(
    sqrt_price: int, liquidity: int, out_amount: int, is_b: bool
) -> int:
    if sqrt_price == 0:
        raise ValueError("sqrt price must be > 0")
    if is_b:
        # √P' = √P - Δy / L  (rounding up)
        quotient = ((out_amount << (SCALE_OFFSET * 2)) + liquidity - 1) // liquidity
        res = sqrt_price - quotient
        if res < 0:
            raise ValueError("sqrt price negative")
        return res
    else:
        # √P' = (L * √P) / (L - Δx * √P)  (rounding down)
        if out_amount == 0:
            return sqrt_price
        prod       = out_amount * sqrt_price
        denom      = liquidity - prod
        if denom <= 0:
            raise ValueError("invalid denom in √P calc")
        num        = liquidity * sqrt_price
        return num // denom

def get_base_fee_numerator(
    mode: FeeSchedulerMode,
    cliff: int,
    period: int,
    reduction: int
) -> int:
    if mode == FeeSchedulerMode.Linear:
        return max(0, cliff - period * reduction)
    else:
        # exponential: cliff * (1 - reduction/BASIS_POINT_MAX)^period
        bps = Decimal(1) - Decimal(reduction) / BASIS_POINT_MAX
        factor = bps ** period
        return int((Decimal(cliff) * factor).to_integral_value(rounding="ROUND_FLOOR"))

def get_dynamic_fee_numerator(
    volatility_acc: int,
    bin_step: int,
    variable_fee_ctrl: int
) -> int:
    if variable_fee_ctrl == 0:
        return 0
    square = volatility_acc * bin_step
    square = square * square
    vfee   = variable_fee_ctrl * square
    # match: (vfee + 1e11 - 1) / 1e11
    return (vfee + 100_000_000_000 - 1) // 100_000_000_000

def get_fee_numerator(
    current_point: int,
    activation_point: int,
    number_of_period: int,
    period_freq: int,
    mode: FeeSchedulerMode,
    cliff_fee: int,
    reduction: int,
    dynamic_params: Optional[dict] = None
) -> int:
    if period_freq == 0 or current_point < activation_point:
        return cliff_fee
    period = min(
        number_of_period,
        (current_point - activation_point) // period_freq
    )
    fee_num = get_base_fee_numerator(mode, cliff_fee, period, reduction)
    if dynamic_params:
        df = get_dynamic_fee_numerator(
            dynamic_params["volatility_accumulator"],
            dynamic_params["bin_step"],
            dynamic_params["variable_fee_control"],
        )
        fee_num += df
    return min(fee_num, MAX_FEE_NUMERATOR)

def get_fee_mode(collect_fee_mode: int, b_to_a: bool) -> FeeMode:
    fee_on_input   = b_to_a and collect_fee_mode == 1  # e.g. OnlyB==1
    fees_on_token_a = b_to_a and collect_fee_mode == 0 # e.g. BothToken==0
    return FeeMode(fee_on_input, fees_on_token_a)

def get_total_fee_on_amount(amount: int, fee_num: int) -> int:
    return mul_div(amount, fee_num, FEE_DENOMINATOR, Rounding.Up)

def get_swap_amount(
    in_amount: int,
    sqrt_price: int,
    liquidity: int,
    trade_fee_numerator: int,
    a_to_b: bool,
    collect_fee_mode: int
) -> SwapResult:
    fee_mode    = get_fee_mode(collect_fee_mode, not a_to_b)
    actual_in   = in_amount
    total_fee   = 0

    # fee on input?
    if fee_mode.fee_on_input:
        total_fee   = get_total_fee_on_amount(in_amount, trade_fee_numerator)
        actual_in   = in_amount - total_fee

    next_sp     = get_next_sqrt_price(actual_in, sqrt_price, liquidity, a_to_b)

    # compute raw out before fees
    if a_to_b:
        out_amount = get_amount_b_from_liquidity_delta(liquidity, sqrt_price, next_sp, Rounding.Down)
    else:
        out_amount = get_amount_a_from_liquidity_delta(liquidity, sqrt_price, next_sp, Rounding.Down)

    # fee on output?
    if not fee_mode.fee_on_input:
        total_fee  = get_total_fee_on_amount(out_amount, trade_fee_numerator)
        out_amount = out_amount - total_fee

    return SwapResult(
        amount_out      = out_amount,
        total_fee       = total_fee,
        next_sqrt_price = next_sp,
    )

