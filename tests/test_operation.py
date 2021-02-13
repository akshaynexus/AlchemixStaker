import pytest

from brownie import Wei, accounts, chain

# reference code taken from yHegic repo and stecrv strat
# https://github.com/Macarse/yhegic
# https://github.com/Grandthrax/yearnv2_steth_crv_strat


@pytest.mark.require_network("mainnet-fork")
def test_operation(
    currency,
    strategy,
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

    currency.approve(whale, Wei("1000000 ether"), {"from": whale})
    currency.transferFrom(whale, gov, Wei("888000 ether"), {"from": whale})

    vault.setDepositLimit(Wei("889000 ether"))

    # 100% of the vault's depositLimit
    vault.addStrategy(strategy, 10_000, 0, 0, {"from": gov})

    currency.approve(gov, Wei("1000000 ether"), {"from": gov})
    currency.transferFrom(gov, bob, Wei("100000 ether"), {"from": gov})
    currency.transferFrom(gov, alice, Wei("788000 ether"), {"from": gov})
    currency.approve(vault, Wei("1000000 ether"), {"from": bob})
    currency.approve(vault, Wei("1000000 ether"), {"from": alice})

    vault.deposit(Wei("100000 ether"), {"from": bob})
    vault.deposit(Wei("788000 ether"), {"from": alice})
    #Sleep and harvest 5 times
    sleepAndHarvest(5,strategy,gov)
    # We should have made profit
    assert vault.pricePerShare() / 1e18 > 1
    # Withdraws should not fail
    vault.withdraw(Wei("788000 ether"), {"from": alice})
    vault.withdraw(Wei("100000 ether"), {"from": bob})

    # Depositors after withdraw should have a profit
    assert currency.balanceOf(alice) > Wei("788000 ether")
    assert currency.balanceOf(bob) > Wei("100000 ether")

    # Make sure it isnt less than 1 after depositors withdrew
    assert vault.pricePerShare() / 1e18 >= 1

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
    print("1INCH Balance " + str(strategy.balanceOfWant()))
    print("Stake balance " + str(strategy.balanceOfStake()))
    print("Pending reward " + str(strategy.pendingReward()))
