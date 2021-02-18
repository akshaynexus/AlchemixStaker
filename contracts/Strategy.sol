// SPDX-License-Identifier: AGPL-3.0
// Feel free to change the license, but this is what we use

// Feel free to change this version of Solidity. We support >=0.6.0 <0.7.0;
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

// These are the core Yearn libraries
import {BaseStrategy} from "@yearnvaults/contracts/BaseStrategy.sol";
import {SafeERC20, SafeMath, IERC20, Address} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/Math.sol";

// Import interfaces for many popular DeFi projects, or add your own!
import "../interfaces/I1INCHGovernance.sol";
import "../interfaces/I1INCHGovernanceRewards.sol";

contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    //Initiate 1inch interfaces
    I1INCHGovernance public stakeT = I1INCHGovernance(0xA0446D8804611944F1B527eCD37d7dcbE442caba);
    I1INCHGovernanceRewards public governanceT = I1INCHGovernanceRewards(0x0F85A912448279111694F4Ba4F85dC641c54b594);

    constructor(address _vault) public BaseStrategy(_vault) {
        //Approve staking contract to spend 1inch tokens
        want.safeApprove(address(stakeT), type(uint256).max);
    }

    function name() external view override returns (string memory) {
        return "Strategy1INCHGovernance";
    }

    // returns balance of 1INCH
    function balanceOfWant() public view returns (uint256) {
        return want.balanceOf(address(this));
    }

    //Returns staked value
    function balanceOfStake() public view returns (uint256) {
        return stakeT.balanceOf(address(this));
    }

    function pendingReward() public view returns (uint256) {
        return governanceT.earned(address(this));
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        //Add the vault tokens + staked tokens from 1inch governance contract
        return balanceOfWant().add(balanceOfStake()).add(pendingReward());
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        // We might need to return want to the vault
        if (_debtOutstanding > 0) {
            uint256 _amountFreed = 0;
            (_amountFreed, _loss) = liquidatePosition(_debtOutstanding);
            _debtPayment = Math.min(_amountFreed, _debtOutstanding);
        }

        uint256 balanceOfWantBefore = balanceOfWant();
        governanceT.getReward();

        _profit = balanceOfWant().sub(balanceOfWantBefore);
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        uint256 _wantAvailable = balanceOfWant();

        if (_debtOutstanding >= _wantAvailable) {
            return;
        }

        uint256 toInvest = _wantAvailable.sub(_debtOutstanding);

        if (toInvest > 0) {
            stakeT.stake(toInvest);
        }
    }

    function liquidatePosition(uint256 _amountNeeded) internal override returns (uint256 _liquidatedAmount, uint256 _loss) {
        // NOTE: Maintain invariant `want.balanceOf(this) >= _liquidatedAmount`
        // NOTE: Maintain invariant `_liquidatedAmount + _loss <= _amountNeeded`
        uint256 balanceWant = balanceOfWant();
        uint256 balanceStaked = balanceOfStake();
        if (_amountNeeded > balanceWant) {
            // unstake needed amount
            stakeT.unstake((Math.min(balanceStaked, _amountNeeded - balanceWant)));
        }
        // Since we might free more than needed, let's send back the min
        _liquidatedAmount = Math.min(balanceOfWant(), _amountNeeded);
    }

    function prepareMigration(address _newStrategy) internal override {
        // If we have pending rewards,take that out
        governanceT.getReward();
        stakeT.unstake(balanceOfStake());
    }

    // Override this to add all tokens/tokenized positions this contract manages
    // on a *persistent* basis (e.g. not just for swapping back to want ephemerally)
    function protectedTokens() internal view override returns (address[] memory) {
        address[] memory protected = new address[](1);
        protected[0] = address(stakeT); // Staked 1inch tokens from governance contract
        return protected;
    }
}
