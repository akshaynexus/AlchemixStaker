import pytest

from brownie import Wei, chain


@pytest.mark.require_network("mainnet-fork")
def test_migrate(
    currency, Strategy, strategy, chain, vault, whale, gov, strategist, interface
):
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 1000, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(Wei("100 ether"), {"from": whale})
    strategy.harvest({"from": strategist})

    chain.sleep(2592000)
    chain.mine(1)

    strategy.harvest({"from": strategist})
    totalasset_beforemig = strategy.estimatedTotalAssets()
    assert totalasset_beforemig > 0

    strategy2 = strategist.deploy(Strategy, vault)
    vault.migrateStrategy(strategy, strategy2, {"from": gov})
    # Check that we got all the funds on migration
    assert strategy2.estimatedTotalAssets() == totalasset_beforemig
