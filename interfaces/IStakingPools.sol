pragma solidity 0.6.12;

interface IStakingPools {
    function claim(uint256 _poolId) external;

    function deposit(uint256 _poolId, uint256 _depositAmount) external;

    function exit(uint256 _poolId) external;

    function getPoolRewardWeight(uint256 _poolId) external view returns (uint256);

    function getPoolToken(uint256 _poolId) external view returns (address);

    function getStakeTotalDeposited(address _account, uint256 _poolId) external view returns (uint256);

    function getStakeTotalUnclaimed(address _account, uint256 _poolId) external view returns (uint256);

    function withdraw(uint256 _poolId, uint256 _withdrawAmount) external;
}
