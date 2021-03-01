import pytest
from brownie import Wei, accounts, chain

# reference code taken from yHegic repo and stecrv strat
# https://github.com/Macarse/yhegic
# https://github.com/Grandthrax/yearnv2_steth_crv_strat


@pytest.mark.require_network("mainnet-fork")
def test_operation(
    currency,
    stakingstrategy,
    chain,
    vault,
    whale,
    gov,
    bob,
    alice,
    strategist,
    guardian,
    interface,
):
    # Amount configs
    test_budget = Wei("8880 ether")
    approve_amount = Wei("10000 ether")
    deposit_limit = Wei("8890 ether")
    bob_deposit = Wei("1000 ether")
    alice_deposit = Wei("7880 ether")
    currency.approve(whale, approve_amount, {"from": whale})
    currency.transferFrom(whale, gov, test_budget, {"from": whale})

    vault.setDepositLimit(deposit_limit)

    # 100% of the vault's depositLimit
    vault.addStrategy(stakingstrategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})

    currency.approve(gov, approve_amount, {"from": gov})
    currency.transferFrom(gov, bob, bob_deposit, {"from": gov})
    currency.transferFrom(gov, alice, alice_deposit, {"from": gov})
    currency.approve(vault, approve_amount, {"from": bob})
    currency.approve(vault, approve_amount, {"from": alice})

    vault.deposit(bob_deposit, {"from": bob})
    vault.deposit(alice_deposit, {"from": alice})
    # Sleep and harvest 5 times
    sleepAndHarvest(5, stakingstrategy, gov)
    # We should have made profit or stayed stagnant (This happens when there is no rewards in 1INCH rewards)
    assert vault.pricePerShare() / 1e18 >= 1
    # Withdraws should not fail
    vault.withdraw(alice_deposit, {"from": alice})
    vault.withdraw(bob_deposit, {"from": bob})

    # Depositors after withdraw should have a profit or gotten the original amount
    assert currency.balanceOf(alice) >= alice_deposit
    assert currency.balanceOf(bob) >= bob_deposit

    # Make sure it isnt less than 1 after depositors withdrew
    assert vault.pricePerShare() / 1e18 >= 1


@pytest.mark.require_network("mainnet-fork")
def test_operation_lpstrat(
    currencyLP,
    strategylp,
    chain,
    vaultlp,
    whaleLP,
    gov,
    bob,
    alice,
    strategist,
    guardian,
    interface,
):
    # Amount configs
    test_budget = Wei("88 ether")
    approve_amount = Wei("100 ether")
    deposit_limit = Wei("88 ether")
    bob_deposit = Wei("10 ether")
    alice_deposit = Wei("78 ether")
    currencyLP.approve(whaleLP, approve_amount, {"from": whaleLP})
    currencyLP.transferFrom(whaleLP, gov, test_budget, {"from": whaleLP})

    vaultlp.setDepositLimit(deposit_limit)

    # 100% of the vault's depositLimit
    vaultlp.addStrategy(strategylp, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})

    currencyLP.approve(gov, approve_amount, {"from": gov})
    currencyLP.transferFrom(gov, bob, bob_deposit, {"from": gov})
    currencyLP.transferFrom(gov, alice, alice_deposit, {"from": gov})
    currencyLP.approve(vaultlp, approve_amount, {"from": bob})
    currencyLP.approve(vaultlp, approve_amount, {"from": alice})

    vaultlp.deposit(bob_deposit, {"from": bob})
    vaultlp.deposit(alice_deposit, {"from": alice})
    # Sleep and harvest 5 times
    sleepAndHarvest(5, strategylp, gov)
    # We should have made profit or stayed stagnant (This happens when there is no rewards in 1INCH rewards)
    assert vaultlp.pricePerShare() / 1e18 >= 1
    # Withdraws should not fail
    vaultlp.withdraw(alice_deposit, {"from": alice})
    vaultlp.withdraw(bob_deposit, {"from": bob})

    # Depositors after withdraw should have a profit or gotten the original amount
    assert currencyLP.balanceOf(alice) >= alice_deposit
    assert currencyLP.balanceOf(bob) >= bob_deposit

    # Make sure it isnt less than 1 after depositors withdrew
    assert vaultlp.pricePerShare() / 1e18 >= 1


def sleepAndHarvest(times, strat, gov):
    for i in range(times):
        debugStratData(strat, "Before harvest" + str(i))
        chain.sleep(2500)
        chain.mine(1)
        strat.harvest({"from": gov})
        debugStratData(strat, "After harvest" + str(i))


# Used to debug strategy balance data
def debugStratData(strategy, msg):
    print(msg)
    print("Total assets " + str(strategy.estimatedTotalAssets()))
    print("ALCX Balance " + str(strategy.balanceOfWant()))
    print("Stake balance " + str(strategy.balanceOfStake()))
    print("Pending reward " + str(strategy.pendingReward()))
