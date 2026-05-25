"""Stub engine - restore from original if needed."""
def run_regime_transition(prices, fred, quad, structural_probs=None): return {'current_quad': quad or 'Q3', 'transitions': {}, 'summary': f'Regime: {quad or "Q3"}'}
