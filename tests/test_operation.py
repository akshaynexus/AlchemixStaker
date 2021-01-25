import pytest

from brownie import Wei, accounts, Contract, config, chain
from brownie import Strategy
# reference code taken from yHegic repo
# https://github.com/Macarse/yhegic

@pytest.mark.require_network("mainnet-fork")
def test_operation(pm):
    OneInchWhale = accounts.at(
        "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8", force=True
    )  # Binance 7,Has alot of 1INCH

    rewards = accounts[2]
    gov = accounts[3]
    guardian = accounts[4]
    bob = accounts[5]
    alice = accounts[6]
    strategist = accounts[7]

    oneinch = Contract("0x111111111117dC0aa78b770fA6A738034120C302", owner=gov)
    oneinch.approve(OneInchWhale, Wei("1000000 ether"), {"from": OneInchWhale})
    oneinch.transferFrom(
        OneInchWhale, gov, Wei("888000 ether"), {"from": OneInchWhale}
    )

    Vault = pm(config["dependencies"][0]).Vault
    y1INCH = Vault.deploy({"from": gov})
    y1INCH.initialize(oneinch, gov, rewards, "", "")
    y1INCH.setDepositLimit(Wei("889000 ether"))

    strategy = guardian.deploy(Strategy,y1INCH)
    strategy.setStrategist(strategist)

    # 100% of the vault's depositLimit
    y1INCH.addStrategy(strategy, 10_000, 0, 0, {"from": gov})

    oneinch.approve(gov, Wei("1000000 ether"), {"from": gov})
    oneinch.transferFrom(gov, bob, Wei("100000 ether"), {"from": gov})
    oneinch.transferFrom(gov, alice, Wei("788000 ether"), {"from": gov})
    oneinch.approve(y1INCH, Wei("1000000 ether"), {"from": bob})
    oneinch.approve(y1INCH, Wei("1000000 ether"), {"from": alice})

    y1INCH.deposit(Wei("100000 ether"), {"from": bob})
    y1INCH.deposit(Wei("788000 ether"), {"from": alice})
    debugStratData(strategy,"Before mineup")
    #Lets mine a few blocks to build up rewards
    chain.mine(500)
    debugStratData(strategy,"Before harvest")
    #This harvest stakes the 1inch tokens gotten to vault
    strategy.harvest({"from": gov})
    assert oneinch.balanceOf(strategy) == 0

    chain.mine(500)
    debugStratData(strategy,"Before harvest2")
    #This harvest takes pending rewards now and reinvests it
    strategy.harvest({"from": gov})
    debugStratData(strategy,"After harvest2")

    chain.mine(500)
    debugStratData(strategy,"Before harvest3")
    #This harvest takes pending rewards now and reinvests it
    strategy.harvest({"from": gov})
    debugStratData(strategy,"After harvest3")

    # We should have made profit
    assert y1INCH.pricePerShare() / 1e18 > 1
    #Withdraws should not fail
    y1INCH.withdraw(Wei("788000 ether"), {"from": alice})
    y1INCH.withdraw(Wei("100000 ether"), {"from": bob})

    #Depositors after withdraw should have a profit
    assert oneinch.balanceOf(alice) > Wei("788000 ether")
    assert oneinch.balanceOf(bob)   > Wei("100000 ether")


#Used to debug strategy balance data
def debugStratData(strategy,msg):
    print(msg)
    print("1INCH Balance " + str(strategy.balanceOfWant()))
    print("Stake balance " + str(strategy.balanceOfStake()))
    print("Pending reward " + str(strategy.pendingReward()))