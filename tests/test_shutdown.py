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


def test_emergency_shutdown(chain, gov, whale, currency, vault, stakingstrategy):
    currency.approve(vault, 2 ** 256 - 1, {"from": gov})
    currency.transfer(gov, Wei("4000 ether"), {"from": whale})

    vault.setDepositLimit(Wei("4000 ether"), {"from": gov})
    vault.addStrategy(stakingstrategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    vault.deposit(Wei("4000 ether"), {"from": gov})
    stakingstrategy.harvest()

    vault.setEmergencyShutdown(True, {"from": gov})
    stakingstrategy.harvest()

    assert vault.strategies(stakingstrategy).dict()["totalDebt"] == 0


def test_shutdown_lpstrat(gov, whaleLP, currencyLP, vaultlp, strategylp):
    currencyLP.approve(vaultlp, 2 ** 256 - 1, {"from": gov})

    currencyLP.approve(whaleLP, 2 ** 256 - 1, {"from": whaleLP})
    currencyLP.transferFrom(whaleLP, gov, Wei("400 ether"), {"from": whaleLP})

    vaultlp.setDepositLimit(Wei("400 ether"), {"from": gov})
    # Start with 100% of the debt
    vaultlp.addStrategy(strategylp, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    # Depositing 80k
    vaultlp.deposit(Wei("400 ether"), {"from": gov})
    strategylp.harvest()

    vaultlp.revokeStrategy(strategylp, {"from": gov})
    strategylp.harvest()
    assert vaultlp.strategies(strategylp).dict()["totalDebt"] == 0
