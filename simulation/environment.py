"""PettingZoo AEC environment for room market simulation."""

import functools
import random
from typing import Dict, List, Optional

import gymnasium
import numpy as np
from gymnasium import spaces
from pettingzoo import AECEnv
from pettingzoo.utils import agent_selector

from .agents import compute_utility, generate_agents, should_bid
from .config import SimulationConfig
from .market_state import (
    MarketState, SimAuction, SimBooking, SimRoom, SimTimeSlot,
)


class RoomMarketEnv(AECEnv):
    """PettingZoo AEC environment simulating a Dutch auction room market."""

    metadata = {"render_modes": [], "name": "room_market_v0"}

    def __init__(self, config: SimulationConfig):
        super().__init__()
        self.config = config
        self.rng = random.Random(config.seed)
        self.np_rng = np.random.RandomState(config.seed)

        self.max_auctions = config.num_rooms * config.slots_per_room_per_day
        self.state = MarketState()
        self._sim_agents = generate_agents(config, self.rng)

        # PettingZoo required attributes
        self.possible_agents = [f"agent_{i}" for i in range(config.num_agents)]
        self.agents = list(self.possible_agents)

        # Spaces
        obs_size = 4 + self.max_auctions * 4  # balance, day, high_demand, num_bookings + per-auction(price, location, time, active)
        self.observation_spaces = {
            agent: spaces.Box(low=-np.inf, high=np.inf, shape=(obs_size,), dtype=np.float32)
            for agent in self.possible_agents
        }
        self.action_spaces = {
            agent: spaces.Discrete(self.max_auctions + 1)  # 0=pass, 1..N=bid
            for agent in self.possible_agents
        }

        self._current_day = 0
        self._current_tick = 0
        self._day_auctions: List[SimAuction] = []
        self._agent_selector = None
        self.agent_selection = None

        # PettingZoo state tracking
        self.rewards = {a: 0.0 for a in self.possible_agents}
        self.terminations = {a: False for a in self.possible_agents}
        self.truncations = {a: False for a in self.possible_agents}
        self.infos = {a: {} for a in self.possible_agents}
        self._cumulative_rewards = {a: 0.0 for a in self.possible_agents}

        # Initialize market
        self._init_rooms()

    def _init_rooms(self):
        for i in range(self.config.num_rooms):
            room = SimRoom(id=i, name=f"Room_{i}", location_index=i)
            self.state.rooms.append(room)

    def _is_high_demand(self, day: int) -> bool:
        for start, end in self.config.high_demand_days:
            if start <= day <= end:
                return True
        return False

    def _allocate_tokens(self):
        for sa in self._sim_agents:
            sa.balance += self.config.token_amount

    def _create_day_auctions(self, day: int) -> List[SimAuction]:
        auctions = []
        for room in self.state.rooms:
            for t in range(self.config.slots_per_room_per_day):
                slot_id = self.state.next_slot_id()
                slot = SimTimeSlot(id=slot_id, room_id=room.id, day=day, time_index=t)
                self.state.slots[slot_id] = slot

                auction = SimAuction(
                    id=self.state.next_auction_id(),
                    slot_id=slot_id,
                    room_id=room.id,
                    day=day,
                    time_index=t,
                    location_index=room.location_index,
                    start_price=self.config.auction_start_price,
                    min_price=self.config.auction_min_price,
                    price_step=self.config.auction_price_step,
                    current_price=self.config.auction_start_price,
                )
                auctions.append(auction)
                self.state.total_slots_offered += 1

        self.state.daily_auctions[day] = auctions
        return auctions

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        return self.observation_spaces[agent]

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return self.action_spaces[agent]

    def observe(self, agent: str) -> np.ndarray:
        agent_idx = int(agent.split("_")[1])
        sa = self._sim_agents[agent_idx]

        obs = np.zeros(4 + self.max_auctions * 4, dtype=np.float32)
        obs[0] = sa.balance
        obs[1] = float(self._current_day)
        obs[2] = 1.0 if self._is_high_demand(self._current_day) else 0.0
        obs[3] = float(len(sa.bookings))

        for i, auction in enumerate(self._day_auctions):
            if i >= self.max_auctions:
                break
            base = 4 + i * 4
            obs[base] = auction.current_price if not auction.completed else 0.0
            obs[base + 1] = float(auction.location_index)
            obs[base + 2] = float(auction.time_index)
            obs[base + 3] = 0.0 if auction.completed else 1.0

        return obs

    def reset(self, seed=None, options=None):
        if seed is not None:
            self.rng = random.Random(seed)
            self.np_rng = np.random.RandomState(seed)
            self.config.seed = seed
            self._sim_agents = generate_agents(self.config, self.rng)
            self.state = MarketState()
            self._init_rooms()

        self._current_day = 0
        self._current_tick = 0
        self.agents = list(self.possible_agents)

        self.rewards = {a: 0.0 for a in self.possible_agents}
        self.terminations = {a: False for a in self.possible_agents}
        self.truncations = {a: False for a in self.possible_agents}
        self.infos = {a: {} for a in self.possible_agents}
        self._cumulative_rewards = {a: 0.0 for a in self.possible_agents}

        # Allocate initial tokens
        self._allocate_tokens()

        # Create auctions for day 0
        self._day_auctions = self._create_day_auctions(0)

        self._agent_selector = agent_selector(self.agents)
        self.agent_selection = self._agent_selector.reset()

    def step(self, action: int):
        agent = self.agent_selection
        agent_idx = int(agent.split("_")[1])
        sa = self._sim_agents[agent_idx]

        # Clear previous step's cumulative reward
        self._cumulative_rewards[agent] = 0.0

        # Handle terminated/truncated agents: remove from active list
        if self.terminations[agent] or self.truncations[agent]:
            if agent in self.agents:
                self.agents.remove(agent)
            if self.agents:
                self._agent_selector = agent_selector(self.agents)
                self.agent_selection = self._agent_selector.reset()
            return

        if action > 0 and action <= len(self._day_auctions):
            auction = self._day_auctions[action - 1]
            self.state.total_bids_attempted += 1
            if not auction.completed and sa.balance >= auction.current_price:
                # Successful bid
                sa.balance -= auction.current_price
                auction.completed = True
                auction.winner_id = sa.id
                auction.clearing_price = auction.current_price

                sa.bookings.append(auction.slot_id)
                self.state.bookings.append(SimBooking(
                    agent_id=sa.id,
                    slot_id=auction.slot_id,
                    price=auction.current_price,
                    day=self._current_day,
                ))
                self.state.total_slots_booked += 1

                if self._current_day not in self.state.daily_clearing_prices:
                    self.state.daily_clearing_prices[self._current_day] = []
                self.state.daily_clearing_prices[self._current_day].append(auction.current_price)

                self.rewards[agent] = 1.0
            else:
                self.rewards[agent] = -0.1
        else:
            # Pass action
            self.rewards[agent] = 0.0

        # Advance to next agent
        self._cumulative_rewards[agent] += self.rewards[agent]

        is_last = self._agent_selector.is_last()
        self.agent_selection = self._agent_selector.next()

        if is_last:
            self._advance_tick()

    def _advance_tick(self):
        """Advance one tick: drop prices on active auctions."""
        self._current_tick += 1

        # Drop prices on active auctions
        for auction in self._day_auctions:
            if not auction.completed:
                auction.current_price = max(
                    auction.min_price,
                    auction.current_price - auction.price_step,
                )
                auction.tick += 1

        # Check if all auctions completed or max ticks reached
        all_done = all(a.completed for a in self._day_auctions)
        max_ticks_reached = self._current_tick >= self.config.max_ticks

        if all_done or max_ticks_reached:
            self._end_day()

    def _end_day(self):
        """End the current day, compute daily metrics, advance."""
        day = self._current_day

        # Daily utilization
        day_auctions = self._day_auctions
        booked = sum(1 for a in day_auctions if a.completed)
        total = len(day_auctions)
        self.state.daily_utilization[day] = booked / total if total > 0 else 0.0

        # Unmet demand: agents who had balance and preferences but didn't book today
        is_hd = self._is_high_demand(day)
        wanted_count = 0
        for sa in self._sim_agents:
            for auction in day_auctions:
                if not auction.completed and should_bid(sa, auction, is_hd):
                    wanted_count += 1
                    break
        self.state.daily_unmet_demand[day] = wanted_count

        # Advance day
        self._current_day += 1
        self._current_tick = 0

        if self._current_day >= self.config.max_days:
            # Terminate
            for a in self.agents:
                self.terminations[a] = True
        else:
            # Token allocation check
            if self._current_day % self.config.token_frequency == 0:
                self._allocate_tokens()

            # Create new auctions
            self._day_auctions = self._create_day_auctions(self._current_day)

    def last(self):
        agent = self.agent_selection
        obs = self.observe(agent)
        return (
            obs,
            self._cumulative_rewards[agent],
            self.terminations[agent],
            self.truncations[agent],
            self.infos[agent],
        )


def run_environment_fast(config: SimulationConfig) -> MarketState:
    """Fast-path runner that bypasses PettingZoo AEC machinery.

    Produces identical market outcomes to run_environment() but skips numpy
    observations, agent_selector, string agent IDs, and reward tracking.
    """
    rng = random.Random(config.seed)

    state = MarketState()
    sim_agents = generate_agents(config, rng)

    # Init rooms
    rooms = []
    for i in range(config.num_rooms):
        room = SimRoom(id=i, name=f"Room_{i}", location_index=i)
        rooms.append(room)
        state.rooms.append(room)

    def is_high_demand(day: int) -> bool:
        for start, end in config.high_demand_days:
            if start <= day <= end:
                return True
        return False

    def create_day_auctions(day: int) -> list:
        auctions = []
        for room in rooms:
            for t in range(config.slots_per_room_per_day):
                slot_id = state.next_slot_id()
                slot = SimTimeSlot(id=slot_id, room_id=room.id, day=day, time_index=t)
                state.slots[slot_id] = slot
                auction = SimAuction(
                    id=state.next_auction_id(),
                    slot_id=slot_id,
                    room_id=room.id,
                    day=day,
                    time_index=t,
                    location_index=room.location_index,
                    start_price=config.auction_start_price,
                    min_price=config.auction_min_price,
                    price_step=config.auction_price_step,
                    current_price=config.auction_start_price,
                )
                auctions.append(auction)
                state.total_slots_offered += 1
        state.daily_auctions[day] = auctions
        return auctions

    # Allocate initial tokens
    for sa in sim_agents:
        sa.balance += config.token_amount

    for day in range(config.max_days):
        # Token allocation (skip day 0 — already allocated above)
        if day > 0 and day % config.token_frequency == 0:
            for sa in sim_agents:
                sa.balance += config.token_amount

        day_auctions = create_day_auctions(day)
        is_hd = is_high_demand(day)

        for tick in range(config.max_ticks):
            # Shuffle agent order each tick to avoid bias
            agent_order = list(sim_agents)
            rng.shuffle(agent_order)

            for sa in agent_order:
                # Find a bid — shuffle auction indices to avoid bias
                indices = list(range(len(day_auctions)))
                rng.shuffle(indices)
                for i in indices:
                    auction = day_auctions[i]
                    if should_bid(sa, auction, is_hd):
                        # Process bid
                        state.total_bids_attempted += 1
                        if not auction.completed and sa.balance >= auction.current_price:
                            sa.balance -= auction.current_price
                            auction.completed = True
                            auction.winner_id = sa.id
                            auction.clearing_price = auction.current_price
                            sa.bookings.append(auction.slot_id)
                            wtp = compute_utility(sa, auction, is_hd)
                            state.bookings.append(SimBooking(
                                agent_id=sa.id,
                                slot_id=auction.slot_id,
                                price=auction.current_price,
                                day=day,
                                preferred_time_match=auction.time_index == sa.preferred_time,
                                preferred_location_match=auction.location_index == sa.preferred_location,
                                consumer_surplus=wtp - auction.current_price,
                            ))
                            state.total_slots_booked += 1
                            if day not in state.daily_clearing_prices:
                                state.daily_clearing_prices[day] = []
                            state.daily_clearing_prices[day].append(auction.current_price)
                        break

            # Check if all auctions are done
            if all(a.completed for a in day_auctions):
                break

            # Drop prices on active auctions
            for auction in day_auctions:
                if not auction.completed:
                    auction.current_price = max(
                        auction.min_price,
                        auction.current_price - auction.price_step,
                    )
                    auction.tick += 1

        # End-of-day metrics
        booked = sum(1 for a in day_auctions if a.completed)
        total = len(day_auctions)
        state.daily_utilization[day] = booked / total if total > 0 else 0.0

        # Unmet demand
        wanted_count = 0
        for sa in sim_agents:
            for auction in day_auctions:
                if not auction.completed and should_bid(sa, auction, is_hd):
                    wanted_count += 1
                    break
        state.daily_unmet_demand[day] = wanted_count

    return state


def run_environment(config: SimulationConfig) -> MarketState:
    """Run a full simulation using rule-based agent decisions and return the market state."""
    env = RoomMarketEnv(config)
    env.reset(seed=config.seed)

    while env.agents:
        agent = env.agent_selection
        obs, reward, termination, truncation, info = env.last()

        if termination or truncation:
            env.step(0)  # pass for terminated agents
            continue

        agent_idx = int(agent.split("_")[1])
        sa = env._sim_agents[agent_idx]
        is_hd = env._is_high_demand(env._current_day)

        # Rule-based action selection
        action = 0  # default: pass
        # Shuffle auction order to avoid bias toward lower-indexed auctions
        indices = list(range(len(env._day_auctions)))
        env.rng.shuffle(indices)
        for i in indices:
            auction = env._day_auctions[i]
            if should_bid(sa, auction, is_hd):
                action = i + 1  # 1-indexed
                break

        env.step(action)

    return env.state
