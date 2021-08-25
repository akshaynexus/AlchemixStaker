from pathlib import Path
from brownie import (
    AlchemixStakingStrategy,
    accounts,
    config,
    project,
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
    newStrat.setLoss(pendReward)
    # set surplus profit as pendreward to mint perf fees
    newStrat.setSurplusProfit(pendReward)
    # harvest and check it works,harvest twice so that locked profit is recorded
    newStrat.harvest()
    newStrat.harvest()
    # Assert we made enough
    assert vault.totalAssets() <= newStrat.estimatedTotalAssets()
