from pprint import pprint
from ai_hedge_bot.services.trading_service import TradingService

if __name__ == '__main__':
    pprint(TradingService().run_once())
