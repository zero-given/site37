import { Component, createMemo } from 'solid-js';
import type { Token } from '../types';
import { calculateTokenPrice, formatPrice } from '../utils/tokenPrice';

interface TokenPriceProps {
  token: Token;
  class?: string;
  showBothFormats?: boolean;
}

export const TokenPrice: Component<TokenPriceProps> = (props) => {
  const price = createMemo(() => {
    const { priceInUSD } = calculateTokenPrice(props.token);
    return formatPrice(priceInUSD);
  });

  return (
    <div class={`flex flex-col ${props.class || ''}`}>
      <div class="flex flex-col">
        <div class="text-green-400 fw-600">{price().decimal}</div>
        {props.showBothFormats && price().scientific !== price().decimal && (
          <div class="text-white text-sm">{price().scientific}</div>
        )}
      </div>
    </div>
  );
}; 
