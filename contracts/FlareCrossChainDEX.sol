
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@flarenetwork/flare-periphery-contracts/flare/ContractRegistry.sol";
import "@flarenetwork/flare-periphery-contracts/flare/FtsoV2Interface.sol";

// Interface for WFLR wrapping/unwrapping
interface IWFLR {
    function wrap(uint256 amount) external;
    function unwrap(uint256 amount) external;
    function transfer(address recipient, uint256 amount) external returns (bool);
}

// Interface for cross-chain bridge (e.g., LayerZero)
interface ICrossChainBridge {
    function bridgeAsset(address token, uint256 amount, string calldata destinationChain, address recipient) external;
}

// Interface for 1inch aggregator (simplified)
interface IOneInchRouter {
    function swap(
        address caller,
        address srcToken,
        address dstToken,
        uint256 amount,
        uint256 minReturn,
        bytes calldata data
    ) external returns (uint256 returnAmount);
}

contract FlareCrossChainDEX is Ownable {
    // State variables
    mapping(address => mapping(address => uint256)) public liquidityPools;
    mapping(address => uint256) public rewards;
    IERC20 public flrToken;
    IWFLR public wflrToken;
    ICrossChainBridge public bridge;
    IOneInchRouter public oneInchRouter; // 1inch aggregator
    FtsoV2Interface public ftsoV2;
    uint256 public constant FEE = 30; // 0.3% fee (in basis points)
    uint256 public constant REWARD_RATE = 1e18; // Reward rate per block

    // Events
    event Swap(address indexed user, address tokenIn, address tokenOut, uint256 amountIn, uint256 amountOut);
    event CrossChainSwap(address indexed user, address tokenIn, uint256 amountIn, string destinationChain, address tokenOut);
    event LiquidityAdded(address indexed provider, address tokenA, address tokenB, uint256 amountA, uint256 amountB);

    constructor(address _flrToken, address _wflrToken, address _bridge, address _oneInchRouter) Ownable(msg.sender) {
        flrToken = IERC20(_flrToken);
        wflrToken = IWFLR(_wflrToken);
        bridge = ICrossChainBridge(_bridge);
        oneInchRouter = IOneInchRouter(_oneInchRouter);
        ftsoV2 = ContractRegistry.getFtsoV2();
    }

    // Buy/Sell tokens using internal liquidity pool
    function swap(address tokenIn, address tokenOut, uint256 amountIn) external returns (uint256 amountOut) {
        require(liquidityPools[tokenIn][tokenOut] > 0, "No liquidity pool");
        (uint256 price, int8 decimals,) = ftsoV2.getFeedById(getPriceFeedId(tokenIn, tokenOut));
        amountOut = (amountIn * price) / (10 ** uint8(decimals));
        uint256 fee = (amountOut * FEE) / 10000;
        amountOut -= fee;

        require(IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn), "TokenIn transfer failed");
        require(IERC20(tokenOut).transfer(msg.sender, amountOut), "TokenOut transfer failed");
        liquidityPools[tokenIn][tokenOut] += amountIn;
        liquidityPools[tokenOut][tokenIn] -= amountOut;
        emit Swap(msg.sender, tokenIn, tokenOut, amountIn, amountOut);
        return amountOut;
    }

    // Buy/Sell tokens using 1inch aggregator
    function swapWithOneInch(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minReturn,
        bytes calldata oneInchData
    ) external returns (uint256 amountOut) {
        require(IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn), "TokenIn transfer failed");
        require(IERC20(tokenIn).approve(address(oneInchRouter), amountIn), "Approval failed");
        amountOut = oneInchRouter.swap(msg.sender, tokenIn, tokenOut, amountIn, minReturn, oneInchData);
        require(IERC20(tokenOut).transfer(msg.sender, amountOut), "TokenOut transfer failed");
        emit Swap(msg.sender, tokenIn, tokenOut, amountIn, amountOut);
        return amountOut;
    }

    // Cross-chain swap via bridge
    function crossChainSwap(
        address tokenIn,
        uint256 amountIn,
        string calldata destinationChain,
        address tokenOut,
        address recipient
    ) external {
        require(IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn), "TokenIn transfer failed");
        bridge.bridgeAsset(tokenIn, amountIn, destinationChain, recipient);
        emit CrossChainSwap(msg.sender, tokenIn, amountIn, destinationChain, tokenOut);
    }

    // FLR to WFLR swap
    function swapFLRtoWFLR(uint256 amount) external {
        require(flrToken.transferFrom(msg.sender, address(this), amount), "FLR transfer failed");
        wflrToken.wrap(amount);
        require(wflrToken.transfer(msg.sender, amount), "WFLR transfer failed");
        emit Swap(msg.sender, address(flrToken), address(wflrToken), amount, amount);
    }

    // Add liquidity to a pool
    function addLiquidity(address tokenA, address tokenB, uint256 amountA, uint256 amountB) external {
        require(IERC20(tokenA).transferFrom(msg.sender, address(this), amountA), "TokenA transfer failed");
        require(IERC20(tokenB).transferFrom(msg.sender, address(this), amountB), "TokenB transfer failed");
        liquidityPools[tokenA][tokenB] += amountA;
        liquidityPools[tokenB][tokenA] += amountB;
        emit LiquidityAdded(msg.sender, tokenA, tokenB, amountA, amountB);
    }

    // Placeholder for price feed ID
    function getPriceFeedId(address tokenIn, address tokenOut) private pure returns (bytes21) {
        return 0x01464c522f55534400000000000000000000000000; // Example FLR/USD
    }
}
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@flarenetwork/flare-periphery-contracts/flare/ContractRegistry.sol";
import "@flarenetwork/flare-periphery-contracts/flare/FtsoV2Interface.sol";

// Interface for WFLR wrapping/unwrapping
interface IWFLR {
    function wrap(uint256 amount) external;
    function unwrap(uint256 amount) external;
    function transfer(address recipient, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

// Interface for cross-chain bridge (LayerZero/Wormhole)
interface ICrossChainBridge {
    function bridgeAsset(address token, uint256 amount, string calldata destinationChain, address recipient) external payable;
    function estimateBridgeFee(address token, uint256 amount, string calldata destinationChain) external view returns (uint256);
}

// Interface for 1inch aggregator
interface IOneInchRouter {
    function swap(
        address caller,
        address srcToken,
        address dstToken,
        uint256 amount,
        uint256 minReturn,
        bytes calldata data
    ) external returns (uint256 returnAmount);
    
    function getExpectedReturn(
        address srcToken,
        address dstToken,
        uint256 amount
    ) external view returns (uint256 returnAmount, uint256[] memory distribution);
}

contract FlareCrossChainDEX is Ownable, ReentrancyGuard {
    // State variables
    mapping(address => mapping(address => uint256)) public liquidityPools;
    mapping(address => uint256) public rewards;
    mapping(address => bool) public supportedTokens;
    mapping(string => bool) public supportedChains;
    
    IERC20 public flrToken;
    IWFLR public wflrToken;
    ICrossChainBridge public bridge;
    IOneInchRouter public oneInchRouter;
    FtsoV2Interface public ftsoV2;
    
    uint256 public constant FEE = 30; // 0.3% fee (in basis points)
    uint256 public constant REWARD_RATE = 1e18; // Reward rate per block
    uint256 public constant MIN_LIQUIDITY = 1000; // Minimum liquidity threshold

    // Events
    event Swap(address indexed user, address tokenIn, address tokenOut, uint256 amountIn, uint256 amountOut);
    event CrossChainSwap(address indexed user, address tokenIn, uint256 amountIn, string destinationChain, address tokenOut);
    event LiquidityAdded(address indexed provider, address tokenA, address tokenB, uint256 amountA, uint256 amountB);
    event LiquidityRemoved(address indexed provider, address tokenA, address tokenB, uint256 amountA, uint256 amountB);
    event BridgeInitiated(address indexed user, address token, uint256 amount, string destinationChain);

    constructor(
        address _flrToken, 
        address _wflrToken, 
        address _bridge, 
        address _oneInchRouter
    ) Ownable(msg.sender) {
        flrToken = IERC20(_flrToken);
        wflrToken = IWFLR(_wflrToken);
        bridge = ICrossChainBridge(_bridge);
        oneInchRouter = IOneInchRouter(_oneInchRouter);
        ftsoV2 = ContractRegistry.getFtsoV2();
        
        // Initialize supported chains
        supportedChains["ethereum"] = true;
        supportedChains["polygon"] = true;
        supportedChains["avalanche"] = true;
        supportedChains["bsc"] = true;
    }

    // Internal liquidity pool swap
    function swap(address tokenIn, address tokenOut, uint256 amountIn, uint256 minAmountOut) 
        external 
        nonReentrant 
        returns (uint256 amountOut) 
    {
        require(supportedTokens[tokenIn] && supportedTokens[tokenOut], "Unsupported token");
        require(liquidityPools[tokenIn][tokenOut] >= MIN_LIQUIDITY, "Insufficient liquidity");
        
        // Get price from FTSO
        (uint256 price, int8 decimals,) = ftsoV2.getFeedById(getPriceFeedId(tokenIn, tokenOut));
        amountOut = (amountIn * price) / (10 ** uint8(decimals));
        
        // Apply fee
        uint256 fee = (amountOut * FEE) / 10000;
        amountOut = amountOut - fee;
        
        require(amountOut >= minAmountOut, "Slippage too high");
        
        // Execute swap
        IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn);
        IERC20(tokenOut).transfer(msg.sender, amountOut);
        
        // Update liquidity pools
        liquidityPools[tokenIn][tokenOut] += amountIn;
        liquidityPools[tokenOut][tokenIn] -= amountOut;
        
        emit Swap(msg.sender, tokenIn, tokenOut, amountIn, amountOut);
    }

    // 1inch aggregated swap
    function swapVia1inch(
        address srcToken,
        address dstToken,
        uint256 amount,
        uint256 minReturn,
        bytes calldata data
    ) external nonReentrant returns (uint256 returnAmount) {
        require(supportedTokens[srcToken] && supportedTokens[dstToken], "Unsupported token");
        
        IERC20(srcToken).transferFrom(msg.sender, address(this), amount);
        IERC20(srcToken).approve(address(oneInchRouter), amount);
        
        returnAmount = oneInchRouter.swap(
            address(this),
            srcToken,
            dstToken,
            amount,
            minReturn,
            data
        );
        
        IERC20(dstToken).transfer(msg.sender, returnAmount);
        
        emit Swap(msg.sender, srcToken, dstToken, amount, returnAmount);
    }

    // Cross-chain swap via bridge
    function crossChainSwap(
        address tokenIn,
        uint256 amountIn,
        string calldata destinationChain,
        address tokenOut,
        address recipient
    ) external payable nonReentrant {
        require(supportedTokens[tokenIn], "Unsupported input token");
        require(supportedChains[destinationChain], "Unsupported destination chain");
        
        IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn);
        IERC20(tokenIn).approve(address(bridge), amountIn);
        
        bridge.bridgeAsset{value: msg.value}(tokenIn, amountIn, destinationChain, recipient);
        
        emit CrossChainSwap(msg.sender, tokenIn, amountIn, destinationChain, tokenOut);
        emit BridgeInitiated(msg.sender, tokenIn, amountIn, destinationChain);
    }

    // Add liquidity to pool
    function addLiquidity(
        address tokenA,
        address tokenB,
        uint256 amountA,
        uint256 amountB
    ) external nonReentrant {
        require(supportedTokens[tokenA] && supportedTokens[tokenB], "Unsupported token");
        
        IERC20(tokenA).transferFrom(msg.sender, address(this), amountA);
        IERC20(tokenB).transferFrom(msg.sender, address(this), amountB);
        
        liquidityPools[tokenA][tokenB] += amountA;
        liquidityPools[tokenB][tokenA] += amountB;
        
        // Mint rewards (simplified)
        rewards[msg.sender] += (amountA + amountB) * REWARD_RATE / 1e18;
        
        emit LiquidityAdded(msg.sender, tokenA, tokenB, amountA, amountB);
    }

    // Wrap FLR to WFLR
    function wrapFLR(uint256 amount) external {
        require(msg.value >= amount, "Insufficient FLR sent");
        wflrToken.wrap{value: amount}(amount);
        wflrToken.transfer(msg.sender, amount);
    }

    // Unwrap WFLR to FLR
    function unwrapWFLR(uint256 amount) external {
        wflrToken.transferFrom(msg.sender, address(this), amount);
        wflrToken.unwrap(amount);
        payable(msg.sender).transfer(amount);
    }

    // Get swap quote
    function getSwapQuote(address tokenIn, address tokenOut, uint256 amountIn)
        external
        view
        returns (uint256 amountOut, uint256 fee, uint256 priceImpact)
    {
        if (liquidityPools[tokenIn][tokenOut] < MIN_LIQUIDITY) {
            return (0, 0, 10000); // High price impact if no liquidity
        }
        
        (uint256 price, int8 decimals,) = ftsoV2.getFeedById(getPriceFeedId(tokenIn, tokenOut));
        amountOut = (amountIn * price) / (10 ** uint8(decimals));
        fee = (amountOut * FEE) / 10000;
        amountOut = amountOut - fee;
        
        // Calculate price impact (simplified)
        priceImpact = (amountIn * 10000) / liquidityPools[tokenIn][tokenOut];
    }

    // Get cross-chain bridge quote
    function getBridgeQuote(address token, uint256 amount, string calldata destinationChain)
        external
        view
        returns (uint256 bridgeFee, uint256 estimatedGas)
    {
        bridgeFee = bridge.estimateBridgeFee(token, amount, destinationChain);
        estimatedGas = 200000; // Estimated gas for bridge transaction
    }

    // Admin functions
    function addSupportedToken(address token) external onlyOwner {
        supportedTokens[token] = true;
    }

    function addSupportedChain(string calldata chain) external onlyOwner {
        supportedChains[chain] = true;
    }

    function getPriceFeedId(address tokenIn, address tokenOut) internal pure returns (bytes21) {
        // Simplified - would map to actual FTSO feed IDs
        return bytes21(keccak256(abi.encodePacked(tokenIn, tokenOut)));
    }

    // Emergency functions
    function emergencyWithdraw(address token, uint256 amount) external onlyOwner {
        IERC20(token).transfer(owner(), amount);
    }

    receive() external payable {}
}
