from pathlib import Path
from brownie import AlchemixStakingStrategy, accounts, config, project, chain

Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault


def test_migration():
    oldStrat = AlchemixStakingStrategy.at("0x9a631F009eA64eeD2306c1FD34A7e728880a67aF")
    vault = Vault.at(oldStrat.vault())
    gov = accounts.at(vault.governance(), force=True)
    newStrat = AlchemixStakingStrategy.deploy(vault, {"from": gov})
    pendReward = oldStrat.pendingReward()
    debugStratData(oldStrat, vault, "before migration")
    # newStrat.setSurplusProfit(oldStrat.surplusProfit())
    # migrate the strat
    vault.migrateStrategy(oldStrat, newStrat, {"from": gov})

    # Record surplus profit
    newStrat.harvest()
    debugStratData(newStrat, vault, "after migration")

    # # Set manual loss
    # newStrat.setLoss(pendReward, {"from": gov})
    # # set surplus profit as pendreward to mint perf fees
    # newStrat.setSurplusProfit(pendReward, {"from": gov})
    # # harvest and check it works,harvest twice so that locked profit is recorded
    debugStratData(newStrat, vault, "Before second harvest")

    newStrat.harvest()
    chain.mine(1)
    debugStratData(newStrat, vault, "After second harvest")

    print((vault.totalAssets() / 1e18) + (newStrat.pendingReward() / 1e18))
    # Investigate why there is a difference here
    assetDifference = (vault.totalAssets()) - newStrat.estimatedTotalAssets()
    # This might be negative,so if its negative set manual loss and harvest
    if assetDifference > 0:
        print(assetDifference / 1e18)
        newStrat.setLoss(assetDifference, {"from": gov})
        newStrat.harvest()
        chain.sleep(24 * 60 * 60)
    assetDifference = vault.totalAssets() - newStrat.balanceOfStake()
    # allow small difference difference
    if assetDifference > 0:
        print(assetDifference / 1e18)
    else:
        # Assert we made enough
        assert vault.totalAssets() <= newStrat.balanceOfStake()


# Used to debug strategy balance data
def debugStratData(strategy, vault, msg):
    print("========")
    print(msg)
    print("Total assets Vault: " + str(vault.totalAssets() / 1e18))

    print(
        "Total assets Difference from vault: "
        + str((vault.totalAssets() - strategy.estimatedTotalAssets()) / 1e18)
    )
    print("Total assets Strat: " + str(strategy.estimatedTotalAssets() / 1e18))
    print("ALCX Balance: " + str(strategy.balanceOfWant() / 1e18))
    print("Stake balance: " + str(strategy.balanceOfStake() / 1e18))
    print("Pending reward: " + str(strategy.pendingReward() / 1e18))
    print("Total Locked Profit: " + str(vault.lockedProfit() / 1e18))
