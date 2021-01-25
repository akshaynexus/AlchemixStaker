// SPDX-License-Identifier: AGPL-3.0
// Feel free to change the license, but this is what we use

// Feel free to change this version of Solidity. We support >=0.6.0 <0.7.0;
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

// These are the core Yearn libraries
import {
    BaseStrategy,
    StrategyParams
} from "@yearnvaults/contracts/BaseStrategy.sol";
import {
    SafeERC20,
    SafeMath,
    IERC20,
    Address
} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/Math.sol";


// Import interfaces for many popular DeFi projects, or add your own!
import "../interfaces/I1INCHGovernance.sol";
import "../interfaces/I1INCHGovernanceRewards.sol";
interface I1nchStake is I1INCHGovernance, IERC20 {}
contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    IERC20 public OneInchToken = IERC20(0x111111111117dC0aa78b770fA6A738034120C302);
    //Initiate 1inch interfaces
    I1nchStake public stakeT = I1nchStake(0xA0446D8804611944F1B527eCD37d7dcbE442caba);
    I1INCHGovernanceRewards public governanceT = I1INCHGovernanceRewards(0x0F85A912448279111694F4Ba4F85dC641c54b594);
    // The amount of 1INCH we have earned which we are now staking in 1INCH Governance
    uint256 public staking = 0;

    constructor(address _vault) public BaseStrategy(_vault) {
        require(address(want) == address(OneInchToken),"wrong want token");
        //Approve staking contract to spend 1inch tokens
        OneInchToken.safeApprove(address(stakeT),type(uint256).max);
        // You can set these parameters on deployment to whatever you want
        // maxReportDelay = 6300;
        // profitFactor = 100;
        // debtThreshold = 0;
    }

    // ******** OVERRIDE THESE METHODS FROM BASE CONTRACT ************

    function name() external override view returns (string memory) {
        // Add your own name here, suggestion e.g. "StrategyCreamYFI"
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

    function estimatedTotalAssets() public override view returns (uint256) {
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
        //If we have pending rewards,take that out aswell
        if(governanceT.earned(address(this)) > 0) {
            governanceT.getReward();
        }
        //Stake it
        // stakeT.stake(balanceOfWant());

        // Final profit is want generated in the swap if wbtcProfit > 0
        _profit = balanceOfWant().sub(balanceOfWantBefore);
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        //emergency exit is dealt with in prepareReturn
        if (emergencyExit) {
            return;
        }
        // do not invest if we have more debt than want
        if (_debtOutstanding > balanceOfWant()) {
            return;
        }
        // Invest the rest of the want
        uint256 _wantAvailable = balanceOfWant().sub(_debtOutstanding);

        if (_wantAvailable > 0) {
            stakeT.stake(_wantAvailable);
        }
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        // NOTE: Maintain invariant `want.balanceOf(this) >= _liquidatedAmount`
        // NOTE: Maintain invariant `_liquidatedAmount + _loss <= _amountNeeded`
        uint256 balanceWant = balanceOfWant();
        if (balanceWant < _amountNeeded) {
            // unstake needed amount
            stakeT.unstake(_amountNeeded.sub(balanceWant));
        }
        // Since we might free more than needed, let's send back the min
        _liquidatedAmount = Math.min(balanceOfWant(), _amountNeeded);
    }

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function prepareMigration(address _newStrategy) internal override {
        //If we have pending rewards,take that out
        if(governanceT.earned(address(this)) > 0) {
            governanceT.getReward();
        }
        //Unstake from governance
        stakeT.unstake(stakeT.balanceOf(address(this)));
    }

    // Override this to add all tokens/tokenized positions this contract manages
    // on a *persistent* basis (e.g. not just for swapping back to want ephemerally)
    function protectedTokens() internal override view returns (address[] memory) {
        address[] memory protected = new address[](1);
        protected[0] = address(stakeT); // Staked 1inch tokens from governance contract
        return protected;
    }
}
