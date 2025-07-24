
const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying FlareCrossChainDEX to Flare Network...");

  // Contract addresses on Flare mainnet
  const FLR_TOKEN = "0x0000000000000000000000000000000000000001"; // Native FLR
  const WFLR_TOKEN = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"; // Official WFLR
  const BRIDGE_ADDRESS = "0x0000000000000000000000000000000000000000"; // Placeholder - replace with actual bridge
  const ONEINCH_ROUTER = "0x0000000000000000000000000000000000000000"; // Placeholder - replace with actual 1inch router

  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  
  const balance = await deployer.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "FLR");

  // Deploy the contract
  const FlareCrossChainDEX = await ethers.getContractFactory("FlareCrossChainDEX");
  const dex = await FlareCrossChainDEX.deploy(
    FLR_TOKEN,
    WFLR_TOKEN, 
    BRIDGE_ADDRESS,
    ONEINCH_ROUTER
  );

  await dex.waitForDeployment();
  const contractAddress = await dex.getAddress();

  console.log("FlareCrossChainDEX deployed to:", contractAddress);
  console.log("Transaction hash:", dex.deploymentTransaction().hash);

  // Verify on explorer (optional)
  console.log("Verify with:");
  console.log(`npx hardhat verify --network flare ${contractAddress} "${FLR_TOKEN}" "${WFLR_TOKEN}" "${BRIDGE_ADDRESS}" "${ONEINCH_ROUTER}"`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
