import pytest
import brownie
from brownie import Wei

deposit_amount = Wei("40000 ether")
second_deposit_amount = Wei("160000 ether")
final_amount = Wei("80000 ether")


def test_increasing_debt_limit(gov, whale, currency, vault, strategy):
    currency.approve(vault, 2 ** 256 - 1, {"from": gov})
    # Fund gov with enough tokens
    currency.approve(whale, deposit_amount + second_deposit_amount, {"from": whale})
    currency.transferFrom(
        whale, gov, deposit_amount + second_deposit_amount, {"from": whale}
    )

    # Start with a 40k deposit limit
    vault.setDepositLimit(deposit_amount, {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})

    # deposit 40k in total to test
    vault.deposit(deposit_amount, {"from": gov})
    strategy.harvest()
    assert strategy.estimatedTotalAssets() >= deposit_amount

    # User shouldn't be able to deposit 40k more
    with brownie.reverts():
        vault.deposit(deposit_amount, {"from": gov})

    vault.setDepositLimit(second_deposit_amount, {"from": gov})
    vault.deposit(deposit_amount, {"from": gov})
    strategy.harvest()
    assert (
        strategy.estimatedTotalAssets() >= final_amount
    )  # Check that assets is >= 80k


def test_decrease_debt_limit(gov, whale, currency, vault, strategy):
    currency.approve(vault, 2 ** 256 - 1, {"from": gov})
    # Fund gov with enough tokens
    currency.approve(whale, deposit_amount + second_deposit_amount, {"from": whale})
    currency.transferFrom(
        whale, gov, deposit_amount + second_deposit_amount, {"from": whale}
    )

    vault.setDepositLimit(second_deposit_amount, {"from": gov})
    # Start with 100% of the debt
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    print(vault.availableDepositLimit())
    # Depositing 80k
    vault.deposit(second_deposit_amount, {"from": gov})
    strategy.harvest()
    assert strategy.estimatedTotalAssets() >= second_deposit_amount

    # let's lower the debtLimit so the strategy adjust it's position
    vault.updateStrategyDebtRatio(strategy, 5_000)
    strategy.harvest()
    assert strategy.estimatedTotalAssets() >= final_amount
    assert vault.debtOutstanding(strategy) == 0
