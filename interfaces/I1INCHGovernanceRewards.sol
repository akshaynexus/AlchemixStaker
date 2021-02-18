pragma solidity 0.6.12;

interface I1INCHGovernanceRewards {
    function earned(address account) external view returns (uint256);

    function getReward() external;
}
