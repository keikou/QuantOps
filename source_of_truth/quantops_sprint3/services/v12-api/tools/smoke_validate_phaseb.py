from ai_hedge_bot.services.trading_service import TradingService

if __name__ == '__main__':
    out = TradingService().run_once()
    print({'signals': len(out['signals']), 'fills': len(out['fills']), 'evaluations': len(out['evaluations'])})
