"""
Service layer package
Provides modular services for blockchain analysis and credit assessment
"""

# Blockchain data fetching
from .blockchain_service import (
    fetch_all_nfts,
    fetch_token_balances,
    fetch_eth_balance,
    fetch_token_metadata_batch,
    fetch_token_metadata,
    fetch_token_price_alchemy,
    fetch_historical_prices_alchemy,
    fetch_asset_transfers,
    fetch_token_prices,
    fetch_wallet_events_etherscan
)

# Token analysis
from .token_service import (
    calculate_volatility,
    categorize_token,
    enrich_token_data,
    calculate_portfolio_concentration,
    estimate_nft_values
)

# DeFi analysis
from .defi_service import (
    check_defi_interactions,
    check_mixer_interactions,
    analyze_stablecoin_holdings
)

# Wallet metadata
from .wallet_service import (
    calculate_wallet_metadata
)

# Lending protocol analysis
from .lending_service import (
    categorize_lending_event,
    analyze_protocol_interactions,
    fetch_protocol_lending_history,
    extract_repayment_timelines,
    measure_repayment_punctuality,
    analyze_borrowing_frequency,
    detect_emergency_repayments,
    analyze_protocol_performance,
    detect_capital_looping
)

# Treasury and risk analysis
from .treasury_service import (
    calculate_treasury_nav,
    measure_liquidity_buffers,
    stress_test_treasury,
    calculate_debt_service_coverage,
    model_stress_scenarios
)

# Credit assessment
from .credit_service import (
    complete_credit_assessment,
    calculate_credit_score_comprehensive
)

__all__ = [
    # Blockchain
    'fetch_all_nfts',
    'fetch_token_balances',
    'fetch_eth_balance',
    'fetch_token_metadata_batch',
    'fetch_token_metadata',
    'fetch_token_price_alchemy',
    'fetch_historical_prices_alchemy',
    'fetch_asset_transfers',
    'fetch_token_prices',
    'fetch_wallet_events_etherscan',
    
    # Token
    'calculate_volatility',
    'categorize_token',
    'enrich_token_data',
    'calculate_portfolio_concentration',
    'estimate_nft_values',
    
    # DeFi
    'check_defi_interactions',
    'check_mixer_interactions',
    'analyze_stablecoin_holdings',
    
    # Wallet
    'calculate_wallet_metadata',
    
    # Lending
    'categorize_lending_event',
    'analyze_protocol_interactions',
    'fetch_protocol_lending_history',
    'extract_repayment_timelines',
    'measure_repayment_punctuality',
    'analyze_borrowing_frequency',
    'detect_emergency_repayments',
    'analyze_protocol_performance',
    'detect_capital_looping',
    
    # Treasury
    'calculate_treasury_nav',
    'measure_liquidity_buffers',
    'stress_test_treasury',
    'calculate_debt_service_coverage',
    'model_stress_scenarios',
    
    # Credit
    'complete_credit_assessment',
    'calculate_credit_score_comprehensive',
]