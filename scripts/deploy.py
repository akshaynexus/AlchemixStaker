from pathlib import Path

from brownie import Strategy, interface, accounts, config, network, project, web3
from brownie.network.gas.strategies import GasNowStrategy
from brownie.network import gas_price
from eth_utils import is_checksum_address


API_VERSION = config["dependencies"][0].split("@")[-1]
Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault
IVaultRegistry = interface.IVaultRegistry
ISharer = interface.ISharer
# Config data
WANT_TOKEN = "0x111111111117dC0aa78b770fA6A738034120C302"
STRATEGIST_ADDR = "0x7495B77b15fCb52fbb7BCB7380335d819ce4c04B"

VAULT_REGISTRY = "0xE15461B18EE31b7379019Dc523231C57d1Cbc18c"
SHARER = "0x2C641e14AfEcb16b4Aa6601A40EE60c3cc792f7D"
STRATEGIST_MULTISIG = "0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7"
TREASURY = "0x93A62dA5a14C80f265DAbC077fCEE437B1a0Efde"
KEEP3R_MANAGER = "0x13dAda6157Fee283723c0254F43FF1FdADe4EEd6"
DEV_MS = "0x846e211e8ba920B353FB717631C015cf04061Cc9"
BRS_MS = "0xcF02A27199b4d2c842B442B08b55bBe27ca6Cb7C"
# Deployer as governance
GOVERNANCE = STRATEGIST_ADDR
# Rewards to deployer,we can change it to yearn governance after approval
REWARDS = STRATEGIST_ADDR
# Set this to true if we are using a experimental deploy flow
EXPERIMENTAL_DEPLOY = True
BASE_GASLIMIT = 400000
# Set gas price as fast
gas_price(200 * 1e9)


def get_address(msg: str) -> str:
    while True:
        val = input(msg)
        if is_checksum_address(val):
            return val
        else:
            addr = web3.ens.address(val)
            if addr:
                print(f"Found ENS '{val}' [{addr}]")
                return addr
        print(f"I'm sorry, but '{val}' is not a checksummed address or ENS")


def main():
    print(f"You are using the '{network.show_active()}' network")
    dev = accounts.load("stratdev")
    print(f"You are using: 'dev' [{dev.address}]")
    if input("Is there a Vault for this strategy already? y/[N]: ").lower() == "y":
        vault = Vault.at(get_address("Deployed Vault: "))
        assert vault.apiVersion() == API_VERSION
    elif EXPERIMENTAL_DEPLOY:
        vaultRegistry = IVaultRegistry(VAULT_REGISTRY)
        # Deploy and get Vault deployment address
        expVaultTx = vaultRegistry.newExperimentalVault(
            WANT_TOKEN,
            STRATEGIST_ADDR,
            STRATEGIST_MULTISIG,
            TREASURY,
            "",
            "",
            {"from": dev},
        )
        vault = Vault.at(expVaultTx.return_value)
    else:
        # Deploy vault
        vault = Vault.deploy({"from": dev})
        vault.initialize(
            WANT_TOKEN,  # OneInch token as want token
            GOVERNANCE,  # governance
            REWARDS,  # rewards
            "",  # nameoverride
            "",  # symboloverride
            {"from": dev},
        )
        print(API_VERSION)
        assert vault.apiVersion() == API_VERSION

    print(
        f"""
    Strategy Parameters

       api: {API_VERSION}
     token: {vault.token()}
      name: '{vault.name()}'
    symbol: '{vault.symbol()}'
    """
    )
    if input("Deploy Strategy? [y]/n: ").lower() == "n":
        strategy = Strategy.at(get_address("Deployed Strategy: "))
    else:
        strategy = Strategy.deploy(vault, {"from": dev}, publish_source=True)
    # add strat to vault
    vault.addStrategy(strategy, 9800, 0, 2 ** 256 - 1, 1000, {"from": dev})
    # Set deposit limit to 1008 1INCH tokens,Approx 50K
    vault.setDepositLimit(1008 * 1e18, {"from": dev})
    # Set keeper
    strategy.setKeeper(KEEP3R_MANAGER, {"from": dev})
    # Set reward
    strategy.setRewards(SHARER, {"from": dev})
    if EXPERIMENTAL_DEPLOY:
        vault.setGovernance(BRS_MS, {"from": dev})
        vault.setManagementFee(0, {"from": dev})
        # Setup rewards
        contributors = [dev.address]
        _numOfShares = [660]
        sharer = ISharer(SHARER)
        sharer.setContributors(
            strategy, contributors, _numOfShares, {"from": dev},
        )
