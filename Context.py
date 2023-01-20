from __future__ import annotations

import Strategy


class Context:

    def __init__(self) -> None:
        self._strategies = []

    def append_strategy(self, strategy: Strategy) -> None:
        self._strategies.append(strategy)

    def run_strategies(self) -> None:
        print('Running strategies:', self._strategies)
        for strategy in self._strategies:
            strategy.do_algorithm()
