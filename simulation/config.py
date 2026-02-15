"""Configuration dataclasses for PettingZoo market simulation."""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class SimulationConfig:
    """Configuration for a single simulation run."""
    num_agents: int = 30
    num_rooms: int = 5
    slots_per_room_per_day: int = 3  # morning, afternoon, evening
    max_days: int = 14

    # Token allocation
    token_amount: float = 100.0
    token_frequency: int = 7  # allocate every N days

    # Dutch auction params
    auction_start_price: float = 100.0
    auction_min_price: float = 10.0
    auction_price_step: float = 5.0
    max_ticks: int = 20  # max ticks per auction before expiry

    # High-demand periods (exam days)
    high_demand_days: List[Tuple[int, int]] = field(default_factory=lambda: [(10, 14)])

    # Agent generation
    location_weights: List[float] = field(default_factory=lambda: [0.3, 0.25, 0.2, 0.15, 0.1])
    time_weights: List[float] = field(default_factory=lambda: [0.4, 0.35, 0.25])  # morning, afternoon, evening

    # Random seed
    seed: int = 42


@dataclass
class GridSearchConfig:
    """Configuration for grid search over allocation parameters."""
    base_config: SimulationConfig = field(default_factory=SimulationConfig)

    token_amounts: List[float] = field(default_factory=lambda: [50.0, 75.0, 100.0, 125.0, 150.0, 200.0])
    token_frequencies: List[int] = field(default_factory=lambda: [3, 5, 7, 10, 14])

    num_seeds: int = 3  # runs per combo for averaging
    base_seed: int = 42
