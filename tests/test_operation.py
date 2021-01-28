import pytest

from brownie import Wei, accounts, Contract, config, chain
from brownie import Strategy
# reference code taken from yHegic repo and stecrv strat
# https://github.com/Macarse/yhegic
# https://github.com/Grandthrax/yearnv2_steth_crv_strat

# @pytest.mark.require_network("mainnet-fork")
def test_operation(currency,Strategy, strategy, chain,vault, whale,gov,strategist,guardian, interface):
    bob = accounts[5]
    alice = accounts[6]

    currency.approve(whale, Wei("1000000 ether"), {"from": whale})
    currency.transferFrom(
        whale, gov, Wei("888000 ether"), {"from": whale}
    )

    vault.setDepositLimit(Wei("889000 ether"))

    strategy = guardian.deploy(Strategy,vault)
    strategy.setStrategist(strategist)

    # 100% of the vault's depositLimit
    vault.addStrategy(strategy, 10_000, 0, 0, {"from": gov})

    currency.approve(gov, Wei("1000000 ether"), {"from": gov})
    currency.transferFrom(gov, bob, Wei("100000 ether"), {"from": gov})
    currency.transferFrom(gov, alice, Wei("788000 ether"), {"from": gov})
    currency.approve(vault, Wei("1000000 ether"), {"from": bob})
    currency.approve(vault, Wei("1000000 ether"), {"from": alice})

    vault.deposit(Wei("100000 ether"), {"from": bob})
    vault.deposit(Wei("788000 ether"), {"from": alice})
    debugStratData(strategy,"Before mineup")
    #Lets mine a few blocks to build up rewards
    chain.mine(500)
    debugStratData(strategy,"Before harvest")
    #This harvest stakes the 1inch tokens gotten to vault
    strategy.harvest({"from": gov})
    assert currency.balanceOf(strategy) == 0
    chain.sleep(2592000)
    chain.mine(1)
    debugStratData(strategy,"Before harvest2")
    #This harvest takes pending rewards now and reinvests it
    strategy.harvest({"from": gov})
    debugStratData(strategy,"After harvest2")
    # We should have made profit
    assert vault.pricePerShare() / 1e18 > 1
    #Withdraws should not fail
    vault.withdraw(Wei("788000 ether"), {"from": alice})
    vault.withdraw(Wei("100000 ether"), {"from": bob})

    #Depositors after withdraw should have a profit
    assert currency.balanceOf(alice) > Wei("788000 ether")
    assert currency.balanceOf(bob)   > Wei("100000 ether")
    #Make sure it isnt less than 1 after depositors withdrew
    assert vault.pricePerShare() / 1e18 >= 1


@pytest.mark.require_network("mainnet-fork")
def test_migrate(currency,Strategy, strategy, chain,vault, whale,gov,strategist, interface):
    rate_limit = 1_000_000_000 *1e18
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, rate_limit, 1000, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    whale_deposit  = 100 *1e18
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': strategist})

    chain.sleep(2592000)
    chain.mine(1)

    strategy.harvest({'from': strategist})

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-100*1e18)*12)/(100*1e18)))

    strategy2 = strategist.deploy(Strategy, vault)
    vault.migrateStrategy(strategy, strategy2, {'from': gov})

#Used to debug strategy balance data
def debugStratData(strategy,msg):
    print(msg)
    print("Total assets "   + str(strategy.estimatedTotalAssets()))
    print("1INCH Balance "  + str(strategy.balanceOfWant()))
    print("Stake balance "  + str(strategy.balanceOfStake()))
    print("Pending reward " + str(strategy.pendingReward()))