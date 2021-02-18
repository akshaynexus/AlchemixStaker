pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

interface ISharer {
    struct Contributor {
        address contributor;
        uint256 numOfShares;
    }

    function acceptStratMs() external;

    function changeStratMs(address _ms) external;

    function checkBalance(address _strategy) external view returns (uint256);

    function distribute(address _strategy) external;

    function pendingStrategistMs() external view returns (address);

    function setContributors(
        address strategy,
        address[] calldata _contributors,
        uint256[] calldata _numOfShares
    ) external;

    function shares(address, uint256) external view returns (address contributor, uint256 numOfShares);

    function strategistMs() external view returns (address);

    function viewContributors(address strategy) external view returns (Contributor[] memory);
}
