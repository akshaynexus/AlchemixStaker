pragma solidity 0.6.12;

interface IVaultRegistry {
    function setGovernance(address _governance) external;

    function acceptGovernance() external;

    function latestRelease() external view returns (string memory);

    function latestVault(address token) external view returns (address);

    function newRelease(address vault) external;

    function newVault(
        address token,
        address guardian,
        address rewards,
        string calldata name,
        string calldata symbol
    ) external returns (address);

    function newExperimentalVault(
        address token,
        address _governance,
        address guardian,
        address rewards,
        string calldata name,
        string calldata symbol
    ) external returns (address);

    function endorseVault(address vault) external;

    function setBanksy(address tagger) external;

    function setBanksy(address tagger, bool allowed) external;

    function tagVault(address vault, string calldata tag) external;

    function nextRelease() external view returns (uint256);

    function releases(uint256 arg0) external view returns (address);

    function nextDeployment(address arg0) external view returns (uint256);

    function vaults(address arg0, uint256 arg1) external view returns (address);

    function governance() external view returns (address);

    function tags(address arg0) external view returns (string memory);

    function banksy(address arg0) external view returns (bool);
}
