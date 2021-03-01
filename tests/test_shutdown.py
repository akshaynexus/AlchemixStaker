import pytest
from brownie import Wei, accounts, chain


def test_shutdown(gov, whale, currency, vault, stakingstrategy):
    currency.approve(vault, 2 ** 256 - 1, {"from": gov})

    currency.approve(whale, 2 ** 256 - 1, {"from": whale})
    currency.transferFrom(whale, gov, Wei("4000 ether"), {"from": whale})

    vault.setDepositLimit(Wei("4000 ether"), {"from": gov})
    # Start with 100% of the debt
    vault.addStrategy(stakingstrategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    # Depositing 80k
    vault.deposit(Wei("4000 ether"), {"from": gov})
    stakingstrategy.harvest()

    vault.revokeStrategy(stakingstrategy, {"from": gov})
    stakingstrategy.harvest()
    assert vault.strategies(stakingstrategy).dict()["totalDebt"] == 0
