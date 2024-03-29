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
import "../interfaces/IStakingPools.sol";

contract AlchemixStakingStrategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    uint256 _poolId = 1;
    uint256 public surplusProfit = 0;
    uint256 public manualLoss = 0;

    //Initiate staking gov interface
    IStakingPools public pool = IStakingPools(0xAB8e74017a8Cc7c15FFcCd726603790d26d7DeCa);

    constructor(address _vault) public BaseStrategy(_vault) {
        //Approve staking contract to spend ALCX tokens
        want.safeApprove(address(pool), type(uint256).max);
    }

    function name() external view override returns (string memory) {
        return "StrategyAlchemixStaking";
    }

    // returns balance of ALCX
    function balanceOfWant() public view returns (uint256) {
        return want.balanceOf(address(this));
    }

    //Returns staked ALCX value
    function balanceOfStake() public view returns (uint256) {
        return pool.getStakeTotalDeposited(address(this), _poolId);
    }

    function pendingReward() public view virtual returns (uint256) {
        return pool.getStakeTotalUnclaimed(address(this), _poolId);
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        //Add the vault tokens + staked tokens from alcx governance contract
        return balanceOfWant().add(balanceOfStake()).add(pendingReward());
    }

    function _deposit(uint256 _depositAmount) internal {
        pool.deposit(_poolId, _depositAmount);
    }

    function _withdraw(uint256 _withdrawAmount) internal {
        pool.withdraw(_poolId, _withdrawAmount);
    }

    function getReward() internal virtual {
        pool.claim(_poolId);
    }

    function setSurplusProfit(uint256 newSurplus) external onlyGovernance {
        surplusProfit = newSurplus;
    }

    function setLoss(uint256 _loss) external onlyGovernance {
        manualLoss = _loss;
    }

    function pendingProfit() public view returns (uint256) {
        uint256 debt = vault.strategies(address(this)).totalDebt;
        uint256 assets = estimatedTotalAssets();
        if (debt < assets) {
            //This will add to profit
            return assets.sub(debt);
        }
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
        getReward();
        uint256 balanceAfter = balanceOfWant();

        _profit = pendingProfit();
        if (surplusProfit > 0) {
            _profit += surplusProfit;
            surplusProfit = 0;
        }
        if (manualLoss > 0) {
            //Set manual loss amount
            _loss += manualLoss;
            manualLoss = 0;
        }

        uint256 requiredWantBal = _profit + _debtPayment;
        if (balanceAfter < requiredWantBal) {
            //Withdraw enough to satisfy profit check
            _withdraw(requiredWantBal.sub(balanceAfter));
        }
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        uint256 _wantAvailable = balanceOfWant();

        if (_debtOutstanding >= _wantAvailable) {
            return;
        }

        uint256 toInvest = _wantAvailable.sub(_debtOutstanding);

        if (toInvest > 0) {
            _deposit(toInvest);
        }
    }

    function liquidatePosition(uint256 _amountNeeded) internal override returns (uint256 _liquidatedAmount, uint256 _loss) {
        // NOTE: Maintain invariant `want.balanceOf(this) >= _liquidatedAmount`
        // NOTE: Maintain invariant `_liquidatedAmount + _loss <= _amountNeeded`
        uint256 balanceWant = balanceOfWant();
        uint256 balanceStaked = balanceOfStake();
        uint256 toWithdraw;
        if (_amountNeeded > balanceWant) {
            toWithdraw = (Math.min(balanceStaked, _amountNeeded - balanceWant));
            // unstake needed amount
            _withdraw(toWithdraw);
        }
        // Since we might free more than needed, let's send back the min
        _liquidatedAmount = Math.min(balanceOfWant(), _amountNeeded);
        _loss = _liquidatedAmount < _amountNeeded ? _amountNeeded.sub(_liquidatedAmount) : 0;
    }

    function prepareMigration(address _newStrategy) internal virtual override {
        //This claims rewards and withdraws deposited ALCX
        pool.exit(_poolId);
    }

    // Override this to add all tokens/tokenized positions this contract manages
    // on a *persistent* basis (e.g. not just for swapping back to want ephemerally)
    function protectedTokens() internal view override returns (address[] memory) {}
}
