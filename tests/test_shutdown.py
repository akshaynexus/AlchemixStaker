import pytest
from brownie import Wei, accounts, chain


def test_shutdown(gov, whale, currency, vault, strategy):
    currency.approve(vault, 2 ** 256 - 1, {"from": gov})

    currency.approve(whale, 2 ** 256 - 1, {"from": whale})
    currency.transferFrom(whale, gov, Wei("40000 ether"), {"from": whale})

    vault.setDepositLimit(Wei("40000 ether"), {"from": gov})
    # Start with 100% of the debt
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    # Depositing 80k
    vault.deposit(Wei("40000 ether"), {"from": gov})
    strategy.harvest()

    vault.revokeStrategy(strategy, {"from": gov})
    strategy.harvest()
    assert vault.strategies(strategy).dict()["totalDebt"] == 0
