from pathlib import Path

from brownie import Strategy, accounts, config, network, project, web3
from brownie.network.gas.strategies import GasNowStrategy
from brownie.network import gas_price
from eth_utils import is_checksum_address


API_VERSION = config["dependencies"][0].split("@")[-1]
Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault

#1INCH token
WANT_TOKEN = "0x111111111117dC0aa78b770fA6A738034120C302"
STRATEGIST_ADDR = "0xAa9E20bAb58d013220D632874e9Fe44F8F971e4d"
#Deployer as governance
GOVERNANCE = STRATEGIST_ADDR
#Rewards to deployer,we can change it to yearn governance after approval
REWARDS    = STRATEGIST_ADDR
#Set gas price as fast
gas_price(62 * 1e9)

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
    dev = accounts.load("dev")
    print(f"You are using: 'dev' [{dev.address}]")

    if input("Is there a Vault for this strategy already? y/[N]: ").lower() == "y":
        vault = Vault.at(get_address("Deployed Vault: "))
        assert vault.apiVersion() == API_VERSION
    else:
        #Deploy vault
        vault = Vault.deploy({"from": dev})
        vault.initialize(
            WANT_TOKEN,#OneInch token as want token
            GOVERNANCE,#governance
            REWARDS,#rewards
            "",#nameoverride
            "",#symboloverride
            {"from": dev}
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
    #add strat to vault
    vault.addStrategy(strategy, 10_000, 0, 0, {"from": dev})
    #Set deposit limit to 5000 1INCH tokens
    vault.setDepositLimit(5000 * 1e18)

