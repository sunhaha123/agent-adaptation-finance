from src.schemas.evolution import MarketState, Order, Trade
from src.simulation.utils import clamp, stdev


def match_order_book(
    orders: list[Order],
    previous_market: MarketState,
    recent_returns: list[float] | None = None,
    max_move: float = 0.10,
) -> tuple[list[Trade], MarketState]:
    buy_orders = sorted(
        [order.model_copy() for order in orders if order.side == "buy"],
        key=lambda order: order.limit_price,
        reverse=True,
    )
    sell_orders = sorted(
        [order.model_copy() for order in orders if order.side == "sell"],
        key=lambda order: order.limit_price,
    )

    total_buy_qty = sum(order.quantity for order in buy_orders)
    total_sell_qty = sum(order.quantity for order in sell_orders)
    total_order_qty = total_buy_qty + total_sell_qty
    order_imbalance = (
        (total_buy_qty - total_sell_qty) / total_order_qty if total_order_qty > 0 else 0.0
    )

    trades: list[Trade] = []
    buy_index = 0
    sell_index = 0
    while buy_index < len(buy_orders) and sell_index < len(sell_orders):
        buy = buy_orders[buy_index]
        sell = sell_orders[sell_index]
        if buy.limit_price < sell.limit_price:
            break

        quantity = min(buy.quantity, sell.quantity)
        trade_price = (buy.limit_price + sell.limit_price) / 2.0
        trades.append(
            Trade(
                buyer_id=buy.individual_id,
                seller_id=sell.individual_id,
                quantity=quantity,
                price=trade_price,
            )
        )
        buy.quantity -= quantity
        sell.quantity -= quantity

        if buy.quantity <= 1e-8:
            buy_index += 1
        if sell.quantity <= 1e-8:
            sell_index += 1

    if trades:
        volume = sum(trade.quantity for trade in trades)
        raw_close = sum(trade.quantity * trade.price for trade in trades) / volume
        liquidity_stress = max(0.0, abs(order_imbalance) * (1.0 - volume / max(total_order_qty, volume)))
    else:
        volume = 0.0
        raw_close = previous_market.price
        liquidity_stress = abs(order_imbalance)

    min_price = previous_market.price * (1.0 - max_move)
    max_price = previous_market.price * (1.0 + max_move)
    close_price = max(clamp(raw_close, min_price, max_price), 0.01)
    return_rate = close_price / previous_market.price - 1.0
    returns_for_vol = (recent_returns or [])[-19:] + [return_rate]

    next_market = MarketState(
        round_index=previous_market.round_index + 1,
        price=close_price,
        volume=volume,
        volatility=stdev(returns_for_vol),
        return_rate=return_rate,
        order_imbalance=clamp(order_imbalance, -1.0, 1.0),
        liquidity_stress=clamp(liquidity_stress, 0.0, 1.0),
    )
    return trades, next_market
