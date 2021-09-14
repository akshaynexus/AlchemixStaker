from pathlib import Path
from brownie import (
    AlchemixStakingStrategy,
    accounts,
    config,
    project,
    chain
)

Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault


def test_migration():
    oldStrat = AlchemixStakingStrategy.at("0x9a631F009eA64eeD2306c1FD34A7e728880a67aF")
    vault = Vault.at(oldStrat.vault())
    gov = accounts.at(vault.governance(), force=True)
    newStrat = AlchemixStakingStrategy.deploy(vault, {"from": gov})
    pendReward = oldStrat.pendingReward()
    newStrat.setSurplusProfit(oldStrat.surplusProfit())
    # migrate the strat
    vault.migrateStrategy(oldStrat, newStrat, {"from": gov})
    # Record surplus profit
    newStrat.harvest()
    # Set manual loss
    newStrat.setLoss(pendReward, {"from": gov})
    # set surplus profit as pendreward to mint perf fees
    newStrat.setSurplusProfit(pendReward, {"from": gov})
    # harvest and check it works,harvest twice so that locked profit is recorded
    newStrat.harvest()
    newStrat.harvest()
    chain.sleep(24*60*60)
    assetDifference = vault.totalAssets() - newStrat.balanceOfStake() 
    #This might be negative,so if its negative set manual loss and harvest
    if assetDifference > 0:
        print(assetDifference / 1e18)
        newLoss = abs(assetDifference)
        newStrat.setLoss(newLoss, {"from": gov})
        newStrat.harvest()
        chain.sleep(24*60*60)
    assetDifference = vault.totalAssets() - newStrat.balanceOfStake()
    #allow small difference difference
    if assetDifference > 0:
        print(assetDifference / 1e18)
    else:
        # Assert we made enough
        assert vault.totalAssets() <= newStrat.balanceOfStake()
