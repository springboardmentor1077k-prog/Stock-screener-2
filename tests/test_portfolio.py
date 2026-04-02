import pytest
from unittest.mock import MagicMock, patch
from backend.portfolio_logic import (
    calculate_unrealized_pnl,
    calculate_average_buy_price,
    calculate_realized_pnl,
    handle_partial_sell,
    calculate_portfolio_summary
)

def test_unrealized_pnl_profit():
    """Test 1: calculate_unrealized_pnl returns correct profit."""
    res = calculate_unrealized_pnl(buy_price=100, current_price=150, quantity=10)
    assert res["profit_or_loss"] == 500.0, f"Expected 500, got {res['profit_or_loss']}"
    assert res["percentage_change"] == 50.0
    assert res["total_invested"] == 1000.0
    assert res["current_value"] == 1500.0

def test_unrealized_pnl_loss():
    """Test 2: calculate_unrealized_pnl returns correct loss."""
    res = calculate_unrealized_pnl(buy_price=200, current_price=150, quantity=5)
    assert res["profit_or_loss"] == -250.0
    assert res["percentage_change"] == -25.0

def test_average_buy_price():
    """Test 3: calculate_average_buy_price is correct."""
    # ((10 * 100) + (5 * 130)) / 15 = (1000 + 650) / 15 = 1650 / 15 = 110.0
    res = calculate_average_buy_price(old_quantity=10, old_buy_price=100.0, new_quantity=5, new_buy_price=130.0)
    assert res == 110.0

def test_realized_pnl_profit():
    """Test 4: calculate_realized_pnl is correct for profit."""
    res = calculate_realized_pnl(buy_price=100.0, sell_price=150.0, quantity_sold=10)
    assert res == 500.0

def test_realized_pnl_loss():
    """Test 5: calculate_realized_pnl is correct for loss."""
    res = calculate_realized_pnl(buy_price=200.0, sell_price=150.0, quantity_sold=5)
    assert res == -250.0

def test_handle_partial_sell():
    """Test 6: handle_partial_sell reduces quantity correctly."""
    res = handle_partial_sell(current_quantity=10, sell_quantity=4, buy_price=100, sell_price=120)
    assert res["remaining_quantity"] == 6
    assert res["realized_pnl"] == 80.0 # (120-100)*4
    assert res["is_position_closed"] is False

def test_handle_full_sell():
    """Test 7: handle_partial_sell with full quantity closes position."""
    res = handle_partial_sell(current_quantity=10, sell_quantity=10, buy_price=100, sell_price=120)
    assert res["remaining_quantity"] == 0
    assert res["is_position_closed"] is True

def test_handle_sell_more_than_owned():
    """Test 8: handle_partial_sell rejects selling more than owned."""
    with pytest.raises(ValueError) as excinfo:
        handle_partial_sell(current_quantity=5, sell_quantity=10, buy_price=100, sell_price=120)
    assert "Cannot sell more" in str(excinfo.value)

def test_portfolio_summary_aggregation():
    """Test 9: calculate_portfolio_summary aggregates correctly."""
    holdings = [
        {"total_invested": 1000.0, "current_value": 1500.0, "profit_or_loss": 500.0},
        {"total_invested": 2000.0, "current_value": 1800.0, "profit_or_loss": -200.0},
        {"total_invested": 500.0, "current_value": 700.0, "profit_or_loss": 200.0}
    ]
    res = calculate_portfolio_summary(holdings)
    
    # total_invested: 1000+2000+500 = 3500.0
    # total_current: 1500+1800+700 = 4000.0
    # total_pnl: 4000-3500 = 500.0
    # overall_%: (500/3500)*100 = 14.29
    # total_holdings: 3
    # profitable: 1500>1000 (yes), 1800>2000 (no), 700>500 (yes) -> 2
    
    assert res["total_invested"] == 3500.0
    assert res["total_current_value"] == 4000.0
    assert res["total_pnl"] == 500.0
    assert res["total_holdings"] == 3
    assert res["profitable_holdings"] == 2
    assert res["profitable_holdings"] == 2
    assert res["overall_percentage_change"] == 14.29

def test_unrealized_pnl_zero_buy_price():
    """Edge Case 4: Portfolio with zero buy price does not cause division by zero."""
    res = calculate_unrealized_pnl(buy_price=0, current_price=100, quantity=10)
    assert res["total_invested"] == 0.0
    assert res["percentage_change"] == 0.0 # Handled gracefully

@patch('backend.portfolio_logic.yf.download')
def test_get_current_price_unknown_symbol(mock_download):
    """Edge Case 5: yfinance returns None/empty for unknown symbol returns 0.0."""
    import pandas as pd
    # Mocking an empty DataFrame which yfinance returns for invalid symbols
    mock_download.return_value = pd.DataFrame()
    from backend.portfolio_logic import get_current_price
    
    price = get_current_price("INVALID_SYM")
    assert price == 0.0
