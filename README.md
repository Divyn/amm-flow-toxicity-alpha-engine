# Flow-Toxicity Alpha System: Automated Fade Trading with Trend Detection for DEX Pools

Fade the noise, not the signal. Automated mean-reversion trading for DEX pools that bets against temporary price shocks. This algorithm is a microstructure alpha for AMMs. Automatically detects and fades temporary price impacts from large swaps, using depth-aware sizing and flow detection to avoid trending markets.


## How It Works

1. **Detects large swaps** that move price significantly (50-500 basis points)
2. **Verifies isolation** - ensures it's not part of a trend (see `flow_detector.py`)
3. **Trades in opposite direction** - fades the move
4. **Exits quickly** - uses tight stop losses (1%) and take profits (0.5%)


### Example Scenario

```
Initial: Pool has 1000 TokenA and 1000 TokenB (price = 1:1)

1. Large trader swaps 100 TokenA → TokenB
   - Price moves: 1 TokenA = 0.9 TokenB (10% move)
   
2. Strategy detects this isolated shock
   
3. We fade by buying TokenA (B→A swap)
   - Betting price will revert toward 1:1
```


## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

Copy `config_sample.py` to `config.py` and fill in your Bitquery credentials, this will be provided by their team. For docs on the streams, read more [here](https://docs.bitquery.io/docs/streams/kafka-streaming-concepts/)

```python
eth_username = "your_username"
eth_password = "your_password"
```

**Note**: Never commit `config.py` to version control. Only `config_sample.py` should be in the repository.

### 3. Adjust Strategy Parameters (Optional)

Edit `strategy_config.py` to customize:
- `MIN_IMPACT_BASIS_POINTS` (50): Minimum price move to trade (0.5%)
- `MAX_IMPACT_BASIS_POINTS` (500): Maximum price move to fade (5%)
- `STOP_LOSS_BASIS_POINTS` (100): Exit if price moves 1% against us
- `TAKE_PROFIT_BASIS_POINTS` (50): Exit if price moves 0.5% in our favor
- `MAX_POSITION_SIZE_RATIO` (0.05): Maximum position size (5% of pool liquidity)
- `WAIT_TIME_SECONDS` (2): Wait time before entering trade

## Running the Strategy

```bash
python3 strategy.py
```

The strategy will:
1. Connect to Bitquery Kafka stream
2. Monitor pool events in real-time
3. Generate fade signals when conditions are met
4. Track and monitor positions

Press `Ctrl+C` to stop gracefully and see active positions.

## Project Structure

- `strategy.py` - Main orchestration and event processing
- `signal_generator.py` - Creates trading signals when conditions are right
- `price_impact.py` - Calculates price impact from swaps
- `flow_detector.py` - Distinguishes isolated shocks from trends
- `position_sizing.py` - Calculates position sizes based on risk
- `position_manager.py` - Monitors active positions and manages exits
- `strategy_config.py` - All configurable parameters
- `bitquery.py` - Handles Bitquery Kafka stream connection. Read more on the dex pool stream [here](https://docs.bitquery.io/docs/cubes/evm-dexpool/)
- `utils.py` - Helper functions for data conversion and formatting
- `config.py` - Your credentials (not in repo, create from `config_sample.py`)

## Configuration Tips

- **Lower MIN_IMPACT**: More trades, but smaller moves (less profit per trade)
- **Higher MAX_IMPACT**: Only fade very large moves (fewer trades, higher risk)
- **Longer WAIT_TIME**: More confirmation, but might miss quick reversals
- **Larger MAX_POSITION_SIZE**: Bigger positions, more risk/reward
- **Tighter STOP_LOSS**: Exit faster, smaller losses but also smaller wins
