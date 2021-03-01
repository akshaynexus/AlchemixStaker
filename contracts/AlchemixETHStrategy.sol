pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;
import "./AlchemixStakingStrategy.sol";
import "../interfaces/IUniswapPair.sol";
import "../interfaces/IUniswapRouter.sol";

contract AlchemixETHStrategy is AlchemixStakingStrategy {
    //Asset addresses
    address ALCX = 0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF;
    address WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    //Strat reference addresses
    address token0;
    address token1;
    address reward = ALCX;

    IUniswapRouter sushiRouter = IUniswapRouter(0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F);
    IERC20 iALCX = IERC20(ALCX);
    IERC20 iWETH = IERC20(WETH);

    constructor(address _vault) public AlchemixStakingStrategy(_vault) {
        _poolId = 2;
        token0 = IUniswapPair(address(want)).token0();
        token1 = IUniswapPair(address(want)).token1();
        iALCX.safeApprove(address(sushiRouter), type(uint256).max);
        iWETH.safeApprove(address(sushiRouter), type(uint256).max);
    }

    function pendingReward() public view override returns (uint256) {
        return reward_to_want(super.pendingReward());
    }

    function quote(
        address token_in,
        address token_out,
        uint256 amount_in
    ) internal view returns (uint256) {
        bool is_weth = token_in == WETH || token_out == WETH;
        address[] memory path = new address[](is_weth ? 2 : 3);
        path[0] = token_in;
        if (is_weth) {
            path[1] = token_out;
        } else {
            path[1] = WETH;
            path[2] = token_out;
        }
        uint256[] memory amounts = sushiRouter.getAmountsOut(amount_in, path);
        return amounts[amounts.length - 1];
    }

    function reward_to_want(uint256 _earned) internal view returns (uint256) {
        if (_earned / 2 == 0) return 0;
        uint256 _amount0 = quote(reward, token0, _earned / 2);
        uint256 _amount1 = quote(reward, token1, _earned / 2);
        (uint112 _reserve0, uint112 _reserve1, ) = IUniswapPair(address(want)).getReserves();
        uint256 _supply = IERC20(want).totalSupply();
        return Math.min(_amount0.mul(_supply).div(_reserve0), _amount1.mul(_supply).div(_reserve1));
    }

    function compoundRewardsToLP(uint256 amount) internal {
        //Sell half to eth
        _sell(amount / 2);
        //Add liq to pair
        _addLiq();
    }

    function _sell(uint256 amount) internal {
        address[] memory sellPath = new address[](2);
        sellPath[0] = ALCX;
        sellPath[1] = WETH;
        //Sell via Token->WETH
        sushiRouter.swapExactTokensForTokens(amount, 0, sellPath, address(this), block.timestamp);
    }

    function _addLiq() internal {
        sushiRouter.addLiquidity(WETH, ALCX, iWETH.balanceOf(address(this)), iALCX.balanceOf(address(this)), 1, 1, address(this), uint256(-1));
    }

    function getReward() internal override {
        super.getReward();
        uint256 _earned = iALCX.balanceOf(address(this));
        if (_earned > 0) compoundRewardsToLP(_earned);
    }

    function prepareMigration(address _newStrategy) internal override {
        super.prepareMigration(_newStrategy);
        //On migration if we have earned any ALCX,add to lp before migrating assets
        uint256 _earned = iALCX.balanceOf(address(this));
        if (_earned > 0) compoundRewardsToLP(_earned);
    }
}
