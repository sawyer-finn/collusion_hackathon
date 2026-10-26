import json
import math
import random
from pathlib import Path
from typing import Any, Dict, Optional
import backoff
import openai
from pydantic import BaseModel, Field


from src.continuous_double_auction.cda_types import Agent, AgentBidResponse
from src.continuous_double_auction.util.jinja_util import render_prompt
from src.continuous_double_auction.util.json_util import extract_json
from src.continuous_double_auction.util.logging_util import ExperimentLogger
from src.resources.model_wrappers import Message, ModelWrapper

# absolute so simulations can be launched from any working directory
TEMPLATE_DIR = str(Path(__file__).resolve().parent.parent / "prompt_templates") + "/"


class MemoryManager:
    """
    Manages structured hour-by-hour memory for agents in a double auction market.
    
    This class provides a consistent memory structure where memories are stored
    by hour and formatted in a consistent way when presented to the agent.
    
    Attributes:
        memories (Dict[int, str]): Dictionary mapping hour numbers to memory strings
    """
    def __init__(self):
        self.memories: Dict[int, str] = {}
    
    def add_memory(self, hour: int, memory: str) -> None:
        """
        Adds a new memory for a specific hour.
        
        Args:
            hour (int): The hour number
            memory (str): The memory string to store
        """
        self.memories[hour] = memory
    
    def get_formatted_memory(self) -> str:
        """
        Returns all memories formatted in a consistent hour-by-hour structure.
        
        Returns:
            str: Formatted memory string
        """
        if not self.memories:
            return "No memories yet."
        
        # Format memories hour by hour in chronological order
        memory_parts = []
        for hour in sorted(self.memories.keys()):
            memory_parts.append(f"Hour {hour}: {self.memories[hour]}")
        
        return "\n".join(memory_parts)


class ZIPBuyer(Agent):
    """
    A ZIPBuyer represents an agent in a market that dynamically adjusts its bidding strategy
    based on its profit margin, learning rate, and momentum. The agent makes bids based on the
    true intrinsic value of an asset and adjusts its bidding margin over time according to
    market feedback.

    Attributes:
        id (inherited): The buyer's identifying string.
        company (inherited): The company this seller is representing.
        valuation (inherited): The price at which the agent values the asset.
        experiment_params(inherited): Various parameters required to configure agent behavior.
        profit_margin: The current profit margin used to determine the bid price.
        learning_rate: The rate at which the profit margin is adjusted in response to market feedback.
        momentum: A factor that incorporates previous adjustments to smooth the learning process.
        last_adjustment: The value of the previous adjustment applied to the profit margin.
        random_noise: A small random value added to the bid to break symmetry between identical buyers.
    """

    profit_margin: float = 0.2
    learning_rate: float = 0.25
    momentum: float = 0.1
    last_adjustment: float = 0
    random_noise: float = 0.01

    def generate_bid_response(self, **kwargs: Any) -> AgentBidResponse:
        """
        Generates a bid response for the ZIPBuyer agent.
        """
        # is_first_round = len(market_history.rounds) == 0
        # if is_first_round:
        #     last_trade_price = None
        # else:
        #     last_trade_price = market_history.rounds[-1].clearing_price

        # if not is_first_round:
        #     if last_trade_price is not None:
        #         current_bid = (1 - self.profit_margin) * self.valuation
        #         # Calculate error (normalized by valuation for scale invariance)
        #         error = (last_trade_price - current_bid) / self.valuation
        #         # Adjust profit margin: decrease margin if market price is high, and vice versa
        #         target_margin = self.profit_margin - error
        #         # Ensure margin remains between 0 and 1
        #         target_margin = max(0.0, min(1.0, target_margin))

        #         # Apply error-scaled adjustment with learning rate and momentum
        #         adjustment = (target_margin - self.profit_margin) * self.learning_rate
        #         adjustment += self.momentum * self.last_adjustment

        #     else:
        #         # No trade occurred because all buyers are bidding too low.
        #         # To become more aggressive, the buyer should lower its profit margin.
        #         # Here, we subtract a small constant (0.05) scaled by the learning rate.
        #         # This value can be tuned based on the market dynamics.
        #         target_margin = self.profit_margin - 0.05  # decrease margin by 5%
        #         target_margin = max(0.0, target_margin)
        #         adjustment = (target_margin - self.profit_margin) * self.learning_rate
        #         adjustment += self.momentum * self.last_adjustment

        #     # Update profit margin and record the adjustment
        #     self.profit_margin += adjustment
        #     self.last_adjustment = adjustment

        base_bid = (1 - self.profit_margin) * self.valuation

        # Introduce a minor randomness of to break symmetry between identical buyers.
        noise_factor = random.uniform(-self.random_noise, self.random_noise)
        return {"bid": base_bid * (1 + noise_factor)}


ENTRANT_TYPES = ("random", "noregret")
ENTRANT_TICK = 0.5  # entrant asks lie on a grid from its cost up to the highest buyer value


def counterfactual_profit(ask: float, other_asks: list[float], bids: list[float], cost: float) -> float:
    """
    Expected profit of posting `ask` against fixed other asks and bids, under the market's
    matching rule (market.resolve_trades_if_any): the k-th lowest ask trades with the k-th
    highest bid while ask <= bid, at the midpoint of the two. Ties with other asks at the same
    price are split evenly over the tied positions.
    """
    bids_desc = sorted(bids, reverse=True)
    below = sum(1 for a in other_asks if a < ask)
    tied = sum(1 for a in other_asks if a == ask)
    total = 0.0
    for rank in range(below, below + tied + 1):
        if rank < len(bids_desc) and ask <= bids_desc[rank]:
            total += (ask + bids_desc[rank]) / 2 - cost
    return total / (tied + 1)


class ScriptedSeller(Agent):
    """
    A rule-based seller that replaces an LLM seller (sprint project 1.5: market entrants).
    It never sends messages, so it is outside the seller chat and the overseer's view, and
    other sellers only see it through its asks.

    Attributes:
        mode: "random" draws each ask uniformly from the price grid, ignoring the market.
            "noregret" is full-information Hedge over the grid: after each round it scores every
            grid price against that round's other asks and bids (counterfactual_profit), and
            asks with probability proportional to exp(eta_t * cumulative score), with
            eta_t = sqrt(8 ln K / t).
        rng: The entrant's own random stream, kept apart from the global one so adding an
            entrant leaves agent names and initial orders unchanged for a given seed.
        cumulative_rewards: Per grid price, the summed counterfactual profit scaled to [0, 1].
        realized_reward: The same score summed over the asks actually posted.
    """
    mode: str = "random"
    rng: random.Random = Field(default_factory=random.Random)
    cumulative_rewards: list[float] = Field(default_factory=list)
    realized_reward: float = 0.0
    rounds_observed: int = 0
    last_ask: Optional[float] = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def price_grid(self) -> list[float]:
        top = max(self.expt_params.buyer_valuations)
        n = int(round((top - self.valuation) / ENTRANT_TICK))
        return [round(self.valuation + ENTRANT_TICK * i, 2) for i in range(n + 1)]

    def hedge_weights(self) -> list[float]:
        grid = self.price_grid
        if not self.cumulative_rewards:
            return [1.0 / len(grid)] * len(grid)
        eta = math.sqrt(8 * math.log(len(grid)) / (self.rounds_observed + 1))
        top = max(self.cumulative_rewards)
        w = [math.exp(eta * (s - top)) for s in self.cumulative_rewards]
        return [x / sum(w) for x in w]

    def generate_bid_response(self, **kwargs: Any) -> AgentBidResponse:
        if self.mode == "random":
            ask = self.rng.choice(self.price_grid)
        elif self.mode == "noregret":
            ask = self.rng.choices(self.price_grid, weights=self.hedge_weights())[0]
        else:
            raise ValueError(f"Unknown entrant mode: {self.mode}")
        self.last_ask = ask
        return {"ask": ask}

    def observe_round(self, seller_asks: list[tuple[float, str]], buyer_bids: list[tuple[float, str]]) -> None:
        """Full-information feedback: the order book as it stood just before this round's matching."""
        if self.mode != "noregret":
            return
        others = [a for a, sid in seller_asks if sid != self.id]
        bids = [b for b, _ in buyer_bids]
        scale = max(self.expt_params.buyer_valuations) - self.valuation
        scores = [counterfactual_profit(p, others, bids, self.valuation) / scale for p in self.price_grid]
        if not self.cumulative_rewards:
            self.cumulative_rewards = [0.0] * len(scores)
        self.cumulative_rewards = [s + r for s, r in zip(self.cumulative_rewards, scores)]
        if self.last_ask is not None:
            self.realized_reward += counterfactual_profit(self.last_ask, others, bids, self.valuation) / scale
        self.rounds_observed += 1


class LMBuyer(Agent):
    """
    A simple LLM Buyer agent.

    Attributes:
        id (inherited): The buyer's identifying string.
        company (inherited): The company this seller is representing.
        valuation (inherited): The price at which the agent values the asset.
        experiment_params(inherited): Various parameters required to configure agent behavior.
        client (ModelWrapper): The model wrapper for the LLM client.
        logger (Optional[ExperimentLogger]): An optional logger for logging agent actions.
        memory_manager (MemoryManager): Manages the agent's hour-by-hour memories.
        scratch_pad (str): The agent's private strategic notes.
    """
    client: ModelWrapper
    logger: Optional[ExperimentLogger] = None
    memory_manager: MemoryManager = None
    scratch_pad: str = ""

    class Config:
        arbitrary_types_allowed = True
        
    def __init__(self, **data):
        super().__init__(**data)
        self.memory_manager = MemoryManager()
        self.scratch_pad = ""

    @backoff.on_exception(
        backoff.expo,
        (
            openai._exceptions.RateLimitError,
            json.decoder.JSONDecodeError,
            AssertionError,
        ),
        max_tries=4,
    )
    def generate_bid_response(self, **kwargs: Any) -> AgentBidResponse:
        round_num = kwargs.get("round_num", 1)
        prompt = render_prompt(
            template_dir=TEMPLATE_DIR,
            prompt_template=self.expt_params.buyer_prompt_template,
            buyer_id=self.id,
            company=self.company,
            valuation=self.valuation,
            round_number=round_num,
            num_rounds=self.expt_params.rounds,
            hide_num_rounds=self.expt_params.hide_num_rounds,
            memory=self.memory_manager.get_formatted_memory(),
            buyer_comms_enabled=self.expt_params.buyer_comms_enabled,
            buyer_messages=kwargs.get("buyer_messages", {}),
            bid_queue=kwargs.get("bid_queue", []),
            ask_queue=kwargs.get("ask_queue", []),
            past_bids_and_asks=kwargs.get("past_bids_and_asks", []),
            past_trades=kwargs.get("past_trades", []),
            agent_successful_trades=kwargs.get("agent_successful_trades", "You have not made any successful trades yet."),
            scratch_pad=self.scratch_pad,
            initial_condition=self.expt_params.initial_condition,
            max_message_length=self.expt_params.max_message_length,
        )
        messages = [Message(role="user", content=prompt)]
        response = self.client.generate(messages=messages)
        assert response is not None
        response_dict = extract_json(response)
        if self.logger:
            self.logger.log_agent_round(
                round_num=round_num,
                agent_id=self.id,
                prompt=prompt,
                response_dict=response_dict,
                )
        # Update memory with the response
        new_memory = response_dict.get("new_memory")
        if new_memory:
            self.memory_manager.add_memory(round_num, new_memory)
            
        # Update scratch pad if provided
        scratch_pad_update = response_dict.get("scratch_pad_update")
        if scratch_pad_update:
            self.scratch_pad = scratch_pad_update
            
        return response_dict


class LMSeller(Agent):
    """
    A simple LLM Seller agent.

    Attributes:
        id (inherited): The seller's identifying string.
        company (inherited): The company this seller is representing.
        valuation (inherited): The price at which the agent values the asset.
        experiment_params(inherited): Various parameters required to configure agent behavior.
        client (ModelWrapper): The model wrapper for the LLM client.
        logger (Optional[ExperimentLogger]): An optional logger for logging agent actions.
        memory_manager (MemoryManager): Manages the agent's hour-by-hour memories.
        scratch_pad (str): The agent's private strategic notes.
    """
    client: ModelWrapper
    logger: Optional[ExperimentLogger] = None
    memory_manager: Optional[MemoryManager] = None
    scratch_pad: str = ""

    class Config:
        arbitrary_types_allowed = True
        
    def __init__(self, **data):
        super().__init__(**data)
        self.memory_manager = MemoryManager()
        self.scratch_pad = ""

    @backoff.on_exception(
        wait_gen=backoff.expo,
        exception=(
            openai._exceptions.RateLimitError,
            json.decoder.JSONDecodeError,
            AssertionError,
        ),
        max_value=2,
        max_tries=4,
    )
    def generate_bid_response(self, **kwargs: Any) -> AgentBidResponse:
        round_num = kwargs.get("round_num", 1)
        
        # Get seller demonym if available in experiment parameters
        demonym = None
        if self.expt_params.seller_demonyms and self.id in self.expt_params.seller_demonyms:
            demonym = self.expt_params.seller_demonyms[self.id]
        
        prompt = render_prompt(
            template_dir=TEMPLATE_DIR,
            prompt_template=self.expt_params.seller_prompt_template,
            seller_id=self.id,
            company=self.company,
            valuation=self.valuation,
            round_number=round_num,
            num_rounds=self.expt_params.rounds,
            hide_num_rounds=self.expt_params.hide_num_rounds,
            memory=self.memory_manager.get_formatted_memory(),
            seller_comms_enabled=self.expt_params.seller_comms_enabled,
            seller_messages=kwargs.get("seller_messages", {}),
            bid_queue=kwargs.get("bid_queue", []),
            ask_queue=kwargs.get("ask_queue", []),
            past_bids_and_asks=kwargs.get("past_bids_and_asks", []),
            past_trades=kwargs.get("past_trades", []),
            agent_successful_trades=kwargs.get("agent_successful_trades", "You have not made any successful trades yet."),
            scratch_pad=self.scratch_pad,
            demonym=demonym,  # Pass the demonym to the template
            is_gagged=kwargs.get("is_gag_order_active", False),
            boss_pressure=self.expt_params.boss_pressure,
            initial_condition=self.expt_params.initial_condition,
            oversight_enabled=self.expt_params.oversight_enabled,
            max_message_length=self.expt_params.max_message_length,
        )
        messages = [Message(role="user", content=prompt)]
        response = self.client.generate(messages=messages)
        assert response is not None
        response_dict = extract_json(response)
        if self.logger:
            self.logger.log_agent_round(
                round_num=round_num,
                agent_id=self.id,
                prompt=prompt,
                response_dict=response_dict,
                )
        # Update memory with the response
        new_memory = response_dict.get("new_memory")
        if new_memory:
            self.memory_manager.add_memory(round_num, new_memory)
            
        # Update scratch pad if provided
        scratch_pad_update = response_dict.get("scratch_pad_update")
        if scratch_pad_update:
            self.scratch_pad = scratch_pad_update
            
        return response_dict

class MessageOverseer(BaseModel):
    """
    Checks the messages exchanged between sellers for collusion.
    """
    client: ModelWrapper
    logger: Optional[ExperimentLogger] = None

    class Config:
        arbitrary_types_allowed = True

    def run_overseer_prompt(self, round_num: int, seller_messages_this_round: dict[str, str]):
        prompt = render_prompt(
            template_dir=TEMPLATE_DIR,
            prompt_template="message_overseer_prompt.jinja2",
            seller_messages_this_round=seller_messages_this_round,
        )
        messages = [Message(role="user", content=prompt)]
        response = self.client.generate(messages=messages)
        assert response is not None
        response_dict = extract_json(response)
        if self.logger:
            self.logger.log_agent_round(
                round_num=round_num,
                agent_id="Overseer",
                prompt=prompt,
                response_dict=response_dict,
                )
        return response_dict