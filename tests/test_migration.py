import pytest

from brownie import Wei, chain


@pytest.mark.require_network("mainnet-fork")
def test_migrate(
    currency,
    AlchemixStakingStrategy,
    stakingstrategy,
    chain,
    vault,
    whale,
    gov,
    strategist,
    interface,
):
    debt_ratio = 10_000
    vault.addStrategy(
        stakingstrategy, debt_ratio, 0, 2 ** 256 - 1, 1_000, {"from": gov}
    )

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(Wei("100 ether"), {"from": whale})
    stakingstrategy.harvest({"from": strategist})

    chain.sleep(2592000)
    chain.mine(1)

    stakingstrategy.harvest({"from": strategist})
    totalasset_beforemig = stakingstrategy.estimatedTotalAssets()
    assert totalasset_beforemig > 0

    strategy2 = strategist.deploy(AlchemixStakingStrategy, vault)
    vault.migrateStrategy(stakingstrategy, strategy2, {"from": gov})
    # Check that we got all the funds on migration
    assert strategy2.estimatedTotalAssets() >= totalasset_beforemig
