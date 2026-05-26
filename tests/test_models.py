import pytest

def test_instrument_model():
    from backend.app.data.models import Instrument
    assert hasattr(Instrument, 'symbol')
    assert hasattr(Instrument, 'name')

def test_daily_bar_model():
    from backend.app.data.models import DailyBar
    assert hasattr(DailyBar, 'trade_date')
    assert hasattr(DailyBar, 'close')
