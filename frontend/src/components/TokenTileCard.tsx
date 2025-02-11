import { Component } from 'solid-js';
import { Shield, Lock, Key, Info } from 'lucide-solid';
import type { Token } from '../types';
import { TrendBadge } from './TrendBadge';
import { TokenPrice } from './TokenPrice';
import { MiniChart } from './MiniChart';

interface TokenTileCardProps {
  token: Token;
  onClick: (e: MouseEvent) => void;
  trends?: {
    liquidity: 'up' | 'down' | 'stagnant';
    holders: 'up' | 'down' | 'stagnant';
  };
  history?: any[];
  dynamicScaling?: boolean;
  showDebugBorders?: boolean;
}

const securityStatus = {
  safe: 'bg-green-100 text-green-800 border border-green-200',
  warning: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
  danger: 'bg-red-100 text-red-800 border border-red-200'
} as const;

export const TokenTileCard: Component<TokenTileCardProps> = (props) => {
  const formatNumber = (num: number) => {
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`;
    return num.toFixed(2);
  };

  const getLiquidityInfo = () => {
    try {
      const lpHolders = JSON.parse(props.token.gpLpHolders || '[]');
      const dexInfo = JSON.parse(props.token.gpDexInfo || '[]');
      
      return {
        lpHolders,
        dexInfo,
        totalLocked: lpHolders.reduce((acc: number, holder: any) => 
          acc + (holder.is_locked ? Number(holder.percent) * 100 : 0), 0
        ),
        totalLiquidity: dexInfo[0]?.liquidity || 0
      };
    } catch {
      return { lpHolders: [], dexInfo: [], totalLocked: 0, totalLiquidity: 0 };
    }
  };

  const liquidityInfo = getLiquidityInfo();

  const getBorderClass = () => props.showDebugBorders ? 'border border-white/20' : 'border border-white/0';

  return (
    <div 
      onClick={props.onClick}
      class="w-full h-full bg-black/20 hover:bg-black/40 backdrop-blur-sm rd-lg border border-gray-700/50 hover:border-gray-600/50 overflow-hidden cursor-pointer transition-all duration-200"
    >
      <div class={`p-4 flex flex-col h-full space-y-4 ${getBorderClass()} transition-colors duration-200`}>
        {/* Header section with grid layout */}
        <div class={`grid grid-cols-2 gap-6 ${getBorderClass()} transition-colors duration-200`}>
          {/* Left side: Token name, symbol and price */}
          <div class={`p-2 ${getBorderClass()} transition-colors duration-200`}>
            <div class="flex justify-between items-start">
              <div>
                <h3 class="text-base fw-600 text-white truncate" title={props.token.tokenName}>
                  {props.token.tokenName}
                </h3>
                <p class="text-sm text-gray-400 truncate">
                  {props.token.tokenSymbol}
                </p>
              </div>
              <div class="ml-4 flex-shrink-0 text-right">
                <TokenPrice token={props.token} class="!text-sm" showBothFormats={true} />
              </div>
            </div>
          </div>

          {/* Right side: Tax, Age, and Risk Level */}
          <div class={`p-2 flex items-center justify-center h-full ${getBorderClass()}`}>
            <div class="flex items-center gap-3 shrink-0">
              <div class="w-[75px] h-[28px] flex-shrink-0 flex items-center justify-center text-center px-2.5 py-1.5 rd text-xs bg-gray-500/10 text-gray-300 border border-gray-500/30">
                {Math.round(props.token.gpBuyTax)}% / {Math.round(props.token.gpSellTax)}%
              </div>
              <span class="w-[75px] h-[28px] flex-shrink-0 flex items-center justify-center text-center px-2.5 py-1.5 rd text-xs bg-gray-500/10 text-gray-300 border border-gray-500/30">
                {(() => {
                  const totalMinutes = Math.round(props.token.tokenAgeHours * 60);
                  const hours = Math.floor(totalMinutes / 60);
                  const minutes = totalMinutes % 60;
                  if (hours > 0) {
                    return `${hours}h ${minutes}m`;
                  }
                  return `${minutes}m`;
                })()}
              </span>
              <span class={`w-[75px] h-[28px] flex-shrink-0 flex items-center justify-center text-center px-2.5 py-1.5 rd text-xs ${securityStatus[props.token.riskLevel]}`}>
                {props.token.hpIsHoneypot ? 'HONEYPOT' : props.token.riskLevel.toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        {/* Charts Section - Horizontal layout */}
        <div class={`grid grid-cols-2 gap-6 ${getBorderClass()}`}>
          {/* Holders Chart */}
          <div class={`bg-black/10 p-2 rd ${getBorderClass()}`}>
            <div class="flex justify-between items-center mb-2">
              <p class="text-gray-400 text-sm">Holders</p>
              <p class="text-white fw-600 text-sm">{formatNumber(props.token.gpHolderCount)}</p>
            </div>
            {props.history && (
              <MiniChart
                token={props.token}
                history={props.history}
                type="holders"
                dynamicScaling={props.dynamicScaling}
              />
            )}
          </div>

          {/* Liquidity Chart */}
          <div class={`bg-black/10 p-2 rd ${getBorderClass()}`}>
            <div class="flex justify-between items-center mb-2">
              <p class="text-gray-400 text-sm">Liquidity</p>
              <p class="text-white fw-600 text-sm">${formatNumber(props.token.hpLiquidityAmount)}</p>
            </div>
            {props.history && (
              <MiniChart
                token={props.token}
                history={props.history}
                type="liquidity"
                dynamicScaling={props.dynamicScaling}
              />
            )}
          </div>
        </div>

        {/* Main Info Grid - Two columns */}
        <div class={`grid grid-cols-2 gap-6 ${getBorderClass()}`}>
          {/* Left Column */}
          <div class={`p-2 space-y-1 ${getBorderClass()}`}>
            <p class={`fw-600 flex items-center gap-1 px-2 py-0.5 rd text-sm ${
              props.token.gpOwnerAddress === '0x0000000000000000000000000000000000000000'
                ? 'bg-green-500/20 text-green-300 border border-green-500/30'
                : 'bg-red-500/20 text-red-300 border border-red-500/30'
            }`}>
              <Key size={14} class="text-current" />
              {props.token.gpOwnerAddress === '0x0000000000000000000000000000000000000000' ? 'Renounced' : 'Owned'}
            </p>
            <p class="text-gray-300 text-xs flex items-center gap-2">
              <span class="shrink-0 text-white">Creator:</span>
              <span class="truncate opacity-60">{props.token.gpCreatorAddress}</span>
            </p>
            <p class="text-gray-300 text-xs flex items-center gap-2">
              <span class="shrink-0 text-white">Owner:</span>
              <span class="truncate opacity-60">{props.token.gpOwnerAddress}</span>
            </p>
          </div>

          {/* Right Column - Liquidity Info */}
          <div class={`p-2 space-y-2 ${getBorderClass()}`}>
            <div class="h-[110px] overflow-y-auto">
              <p class={`text-sm fw-600 flex items-center gap-1 px-2 py-0.5 rd ${
                liquidityInfo.totalLocked > 90 
                  ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
                  : liquidityInfo.totalLocked > 50 
                  ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30' 
                  : 'bg-red-500/20 text-red-300 border border-red-500/30'
              }`}>
                <Lock size={14} />
                {liquidityInfo.totalLocked.toFixed(2)}% Locked
              </p>
              {liquidityInfo.lpHolders.map((holder: any) => (
                <p class="text-gray-300 text-xs flex items-center gap-2 mt-2">
                  <span class="shrink-0 text-white">{(Number(holder.percent) * 100).toFixed(2)}%</span>
                  <span class="truncate opacity-60">{holder.tag || holder.address}</span>
                  {holder.is_locked && <Lock size={12} class="shrink-0" />}
                </p>
              ))}
              {liquidityInfo.dexInfo.map((dex: any) => (
                <p class="text-white text-sm mt-2">
                  {dex.name}: ${Number(dex.liquidity).toLocaleString()}
                </p>
              ))}
            </div>
          </div>
        </div>

        {/* Token Address Link */}
        <div class={`border-t border-gray-700/50 ${getBorderClass()}`}>
          <a 
            href={`https://www.dextools.io/app/en/ether/pair-explorer/${props.token.tokenAddress}`}
            class="text-xs text-gray-400 hover:text-gray-300 break-all block py-1 px-2"
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
          >
            {props.token.tokenAddress}
          </a>
        </div>
      </div>
    </div>
  );
}; 

