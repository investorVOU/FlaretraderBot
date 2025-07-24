
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
