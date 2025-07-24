
const { ethers } = require("hardhat");

async function main() {
    console.log("Deploying FlareCrossChainDEX to Flare Network...");

    // Get contract factory
    const FlareCrossChainDEX = await ethers.getContractFactory("FlareCrossChainDEX");

    // Contract addresses on Flare Network
    const FLR_TOKEN = "0x0000000000000000000000000000000000000001"; // Native FLR
    const WFLR_TOKEN = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"; // Official WFLR
    const BRIDGE_ADDRESS = "0xa318dE26c2e812EE9A96BaDF63Bc32Be0a5D0f3A"; // LayerZero endpoint
    const ONEINCH_ROUTER = "0x1111111254fb6c44bAC0beD2854e76F90643097d"; // 1inch v5

    // Deploy contract
    const dex = await FlareCrossChainDEX.deploy(
        FLR_TOKEN,
        WFLR_TOKEN, 
        BRIDGE_ADDRESS,
        ONEINCH_ROUTER
    );

    await dex.deployed();

    console.log("FlareCrossChainDEX deployed to:", dex.address);
    console.log("Transaction hash:", dex.deployTransaction.hash);

    // Add initial supported tokens
    console.log("Adding supported tokens...");
    
    const tokens = [
        { name: "WFLR", address: "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d" },
        { name: "USDT", address: "0xf56dc6695cF1f5c364eDEbC7Dc7077ac9B586068" },
        { name: "ETH", address: "0x6B7a87899490EcE95443e979cA9485CBE7E71522" }
    ];

    for (const token of tokens) {
        const tx = await dex.addSupportedToken(token.address);
        await tx.wait();
        console.log(`Added ${token.name} as supported token`);
    }

    console.log("Deployment completed successfully!");
    
    // Save deployment info
    const deploymentInfo = {
        network: "flare",
        contractAddress: dex.address,
        deploymentBlock: dex.deployTransaction.blockNumber,
        timestamp: new Date().toISOString(),
        tokens: tokens
    };

    console.log("Deployment Info:", JSON.stringify(deploymentInfo, null, 2));
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
