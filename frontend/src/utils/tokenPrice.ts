import { Token } from '../types';

/**
 * Calculate token price from reserves and decimals
 */
export function calculateTokenPrice(token: Token): { priceInUSD: number | null } {
  try {
    // Get reserves from the token data
    const reserve0 = token.hpPairReserves0;
    const reserve1 = token.hpPairReserves1;
    
    if (!reserve0 || !reserve1) {
      console.debug('[Price] Missing reserves data');
      return { priceInUSD: null };
    }

    // Convert reserves to adjusted values using decimals
    const decimals = token.tokenDecimals;
    const adjustedReserve0 = Number(reserve0) / (10 ** decimals);
    const adjustedReserve1 = Number(reserve1) / (10 ** 18); // Assuming other token is WETH with 18 decimals

    // Calculate price ratios
    const priceInETH = adjustedReserve1 / adjustedReserve0;
    
    // Get liquidity amount in USD from token data
    const liquidityUSD = token.hpLiquidityAmount;
    if (!liquidityUSD) {
      console.debug('[Price] Missing liquidity data');
      return { priceInUSD: null };
    }

    // Calculate approximate ETH price from liquidity
    const ethPriceUSD = liquidityUSD / (2 * adjustedReserve1);
    
    // Calculate final USD price
    const priceInUSD = priceInETH * ethPriceUSD;

    return { priceInUSD };
  } catch (error) {
    console.error('[Price] Error calculating price:', error);
    return { priceInUSD: null };
  }
}

/**
 * Format price for display in both scientific and decimal notation
 */
export function formatPrice(price: number | null): { scientific: string; decimal: string } {
  if (price === null) {
    return { scientific: 'N/A', decimal: 'N/A' };
  }

  // Scientific notation for bottom value
  let scientific = '';
  if (price < 0.0001) {
    scientific = `$${price.toExponential(2)}`;
  } else if (price < 1000) {
    scientific = `$${price.toFixed(2)}`;
  } else {
    scientific = `$${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  }

  // Full decimal notation for top value
  let decimal = '';
  if (price === 0) {
    decimal = '$0.00';
  } else if (price < 0.0000000001) { // 1e-10
    decimal = `$${price.toFixed(12)}`;
  } else if (price < 0.000000001) { // 1e-9
    decimal = `$${price.toFixed(11)}`;
  } else if (price < 0.00000001) { // 1e-8
    decimal = `$${price.toFixed(10)}`;
  } else if (price < 0.0000001) { // 1e-7
    decimal = `$${price.toFixed(9)}`;
  } else if (price < 0.000001) { // 1e-6
    decimal = `$${price.toFixed(8)}`;
  } else if (price < 0.00001) { // 1e-5
    decimal = `$${price.toFixed(7)}`;
  } else if (price < 0.0001) { // 1e-4
    decimal = `$${price.toFixed(6)}`;
  } else if (price < 0.001) { // 1e-3
    decimal = `$${price.toFixed(5)}`;
  } else if (price < 0.01) { // 1e-2
    decimal = `$${price.toFixed(4)}`;
  } else if (price < 0.1) { // 1e-1
    decimal = `$${price.toFixed(3)}`;
  } else if (price < 1) {
    decimal = `$${price.toFixed(2)}`;
  } else if (price < 1000) {
    decimal = `$${price.toFixed(2)}`;
  } else {
    decimal = `$${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  }

  return { scientific, decimal };
} 