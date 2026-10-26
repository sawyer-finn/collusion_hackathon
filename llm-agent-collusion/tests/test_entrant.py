import random

import numpy as np
import pytest

from src.continuous_double_auction.cda_types import Agent, ExperimentParams
from src.continuous_double_auction.evaluation.evaluate import compute_collusion_metrics
from src.continuous_double_auction.market.agents import ScriptedSeller, counterfactual_profit
from src.continuous_double_auction.market.market import Market


def params(n_entrants=1, n_sellers=3):
    return ExperimentParams(seller_valuations=[80.0] * n_sellers, buyer_valuations=[100.0] * 2,
                            seller_models=["m"] * n_sellers, buyer_models=["m"] * 2, rounds=3,
                            seller_comms_enabled=True, entrant_type="random", n_entrants=n_entrants)


def entrant(seed=0):
    return ScriptedSeller(id="Seller E", company="E", valuation=80.0, expt_params=params(), rng=random.Random(seed))


class CartelSeller(Agent):
    def generate_bid_response(self, **kwargs):
        return {"ask": 97.0, "message_to_sellers": "hold"}


class Buyer(Agent):
    def generate_bid_response(self, **kwargs):
        return {"bid": 99.0}


def test_random_asks_are_on_the_grid_and_roughly_uniform():
    e = entrant()
    assert e.price_grid[0] == 80.0 and e.price_grid[-1] == 100.0 and len(e.price_grid) == 41
    asks = [e.generate_bid_response()["ask"] for _ in range(4000)]
    assert set(asks) <= set(e.price_grid)
    assert abs(np.mean(asks) - 90.0) < 0.5
    assert len(set(asks)) == 41


def test_same_seed_gives_same_asks():
    a, b = entrant(seed=3), entrant(seed=3)
    assert [a.generate_bid_response()["ask"] for _ in range(20)] == [b.generate_bid_response()["ask"] for _ in range(20)]


def test_entrant_posts_asks_but_never_messages():
    p = params()
    e = ScriptedSeller(id="Seller E", company="E", valuation=80.0, expt_params=p, rng=random.Random(0))
    cartel = [CartelSeller(id=f"Seller {i}", company="C", valuation=80.0, expt_params=p) for i in range(2)]
    buyers = [Buyer(id=f"Buyer {i}", company="B", valuation=100.0, expt_params=p) for i in range(2)]
    market = Market(sellers=cartel + [e], buyers=buyers)
    for _ in range(3):
        market.run_round()
    for r in market.rounds:
        assert "Seller E" in r.seller_asks
        assert "Seller E" not in r.seller_messages
        assert set(r.seller_messages) == {"Seller 0", "Seller 1"}


def test_index_on_llm_sellers_excludes_entrant(tmp_path):
    metadata = {"auction_config": {"buyer_valuations": [100.0] * 2, "seller_valuations": [80.0] * 3},
                "buyer_ids": ["B0", "B1"], "seller_ids": ["S0", "S1", "E"], "entrant_ids": ["E"]}
    rounds = [{"buyer_bids": {"B0": 99.0, "B1": 98.0}, "seller_asks": {"S0": 98.0, "S1": 98.0, "E": 82.0},
               "trades": [{"price": 90.5, "buyer_id": "B0", "seller_id": "E"}]}] * 3
    m = compute_collusion_metrics(metadata, rounds, exp_dir=tmp_path, run_llm_judge=False)
    assert m["avg_llm_seller_asks_by_round"] == [98.0] * 3
    assert m["avg_seller_asks_by_round"] == pytest.approx([92.666667] * 3)
    assert m["entrant_profits"] == pytest.approx(3 * 10.5)
    assert m["llm_seller_profits"] == 0.0


def test_counterfactual_profit_follows_market_matching():
    # 2 bids, rivals at 96.75 and 97: undercutting both trades with the top bid at the midpoint
    assert counterfactual_profit(96.5, [96.75, 97.0], [100.0, 99.0], 80.0) == pytest.approx(18.25)
    # second-lowest ask trades with the second-highest bid
    assert counterfactual_profit(96.9, [96.75, 97.0], [100.0, 99.0], 80.0) == pytest.approx(17.95)
    # third-lowest ask with only 2 bids, or an ask above the bid, does not trade
    assert counterfactual_profit(98.0, [96.75, 97.0], [100.0, 99.0], 80.0) == 0.0
    assert counterfactual_profit(96.5, [], [95.0], 80.0) == 0.0
    # tied with the one rival at 97 for the single bid: half the trade on average
    assert counterfactual_profit(97.0, [97.0], [100.0], 80.0) == pytest.approx(18.5 / 2)


class FixedSeller(Agent):
    price: float = 96.75

    def generate_bid_response(self, **kwargs):
        return {"ask": self.price}


class TopBuyer(Agent):
    def generate_bid_response(self, **kwargs):
        return {"bid": 100.0}


def run_noregret(rival_price, rounds=150, seed=0):
    """No-regret entrant against 4 rivals at a fixed off-grid price and 2 buyers at 100 (no ties)."""
    p = params(n_entrants=1, n_sellers=5)
    e = ScriptedSeller(id="Seller E", company="E", valuation=80.0, expt_params=p, mode="noregret",
                       rng=random.Random(seed))
    rivals = [FixedSeller(id=f"Seller {i}", company="C", valuation=80.0, expt_params=p, price=rival_price)
              for i in range(4)]
    buyers = [TopBuyer(id=f"Buyer {i}", company="B", valuation=100.0, expt_params=p) for i in range(2)]
    market = Market(sellers=rivals + [e], buyers=buyers)
    for _ in range(rounds):
        market.run_round()
    return e, market


@pytest.mark.parametrize("rival_price, best", [(96.75, 96.5), (84.75, 84.5)])
def test_noregret_learns_to_undercut_fixed_rivals_by_one_tick(rival_price, best):
    e, market = run_noregret(rival_price)
    assert e.price_grid[int(np.argmax(e.cumulative_rewards))] == best
    late = [r.seller_asks["Seller E"] for r in market.rounds[-30:]]
    assert all(best - 3.0 <= a <= best for a in late)
    assert np.median(late) >= best - 1.0


def test_noregret_regret_is_within_the_hedge_bound():
    e, market = run_noregret(96.75)
    T, K = len(market.rounds), len(e.price_grid)
    regret = max(e.cumulative_rewards) - e.realized_reward
    assert 0 <= regret <= 2 * np.sqrt(T / 2 * np.log(K)) + np.sqrt(np.log(K) / 8)


def test_noregret_realized_reward_matches_actual_trades():
    e, market = run_noregret(96.75, rounds=40)
    profit = sum(t.price - 80.0 for t in market.past_trades if t.seller_id == "Seller E")
    assert e.realized_reward * 20 == pytest.approx(profit)


def test_entrant_count_must_leave_an_llm_seller():
    with pytest.raises(ValueError):
        params(n_entrants=3, n_sellers=3)
    with pytest.raises(ValueError):
        ExperimentParams(seller_valuations=[80.0] * 3, buyer_valuations=[100.0], seller_models=["m"] * 3,
                         buyer_models=["m"], rounds=3, n_entrants=1)


def test_one_entrant_type_per_entrant():
    p = ExperimentParams(seller_valuations=[80.0] * 5, buyer_valuations=[100.0] * 5, seller_models=["m"] * 5,
                         buyer_models=["m"] * 5, rounds=3, entrant_type=["noregret", "random"], n_entrants=2)
    assert p.entrant_types == ["noregret", "random"] and p.entrant_label == "1 noregret + 1 random"
    single = params(n_entrants=2, n_sellers=5)
    assert single.entrant_types == ["random", "random"] and single.entrant_label == "2 random"
    with pytest.raises(ValueError):
        ExperimentParams(seller_valuations=[80.0] * 5, buyer_valuations=[100.0] * 5, seller_models=["m"] * 5,
                         buyer_models=["m"] * 5, rounds=3, entrant_type=["noregret", "random"], n_entrants=3)
