import { Component } from 'solid-js';
import type { PerformanceMetrics } from '../types';

interface LiveStatusBarProps {
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  metrics: PerformanceMetrics;
  onBgColorChange: (color: string) => void;
  onResetBgColor: () => void;
  currentBgColor: string;
  showDebugBorders: boolean;
  onToggleDebugBorders: () => void;
}

export const LiveStatusBar: Component<LiveStatusBarProps> = (props) => {
  return (
    <div class={`w-full bg-black/80 backdrop-blur-sm text-white border-b border-gray-800 ${props.showDebugBorders ? 'border border-white/20' : ''}`}>
      <div class={`flex flex-col xs:flex-row justify-between items-center p-2 space-y-2 xs:space-y-0 ${props.showDebugBorders ? 'border border-white/20' : ''}`}>
        {/* Status indicators - stack on mobile */}
        <div class={`flex items-center space-x-2 w-full xs:w-auto justify-between xs:justify-start ${props.showDebugBorders ? 'border border-white/20' : ''}`}>
          <div class={`flex items-center space-x-2 ${props.showDebugBorders ? 'border border-white/20' : ''}`}>
            <div class={`w-2 h-2 rd-full ${props.isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span class="text-sm truncate max-w-[160px] xs:max-w-none">
              {props.isConnected ? 'Connected' : 'Disconnected'}
              {props.isLoading && ' (Loading...)'}
            </span>
          </div>
          {props.error && (
            <div class={`text-sm text-red-400 truncate max-w-[200px] xs:max-w-none ${props.showDebugBorders ? 'border border-white/20' : ''}`}>
              Error: {props.error}
            </div>
          )}
        </div>

        {/* Metrics and controls - grid layout on mobile */}
        <div class={`grid grid-cols-2 xs:flex items-center gap-2 xs:gap-4 text-sm text-gray-400 w-full xs:w-auto ${props.showDebugBorders ? 'border border-white/20' : ''}`}>
          <div class={`hidden xs:block ${props.showDebugBorders ? 'border border-white/20' : ''}`}>
            FPS: {props.metrics.fps.toFixed(1)}
          </div>
          <div class={`hidden xs:block ${props.showDebugBorders ? 'border border-white/20' : ''}`}>
            Memory: {(props.metrics.memory / 1024 / 1024).toFixed(1)} MB
          </div>
          <div class={`col-span-2 text-center xs:text-left flex items-center justify-center xs:justify-start space-x-2 ${props.showDebugBorders ? 'border border-white/20' : ''}`}>
            <input
              type="color"
              value={props.currentBgColor}
              onChange={(e) => props.onBgColorChange(e.currentTarget.value)}
              class="w-6 h-6 rd cursor-pointer bg-transparent"
              title="Change background color"
            />
            <button
              onClick={props.onResetBgColor}
              class="text-xs px-2 py-1 bg-gray-700/50 hover:bg-gray-700 rd transition-colors"
              title="Reset background color"
            >
              Reset
            </button>
            <button
              onClick={props.onToggleDebugBorders}
              class={`text-xs px-2 py-1 rd transition-colors ${
                props.showDebugBorders 
                  ? 'bg-blue-500/50 hover:bg-blue-500/70' 
                  : 'bg-gray-700/50 hover:bg-gray-700'
              }`}
              title="Toggle debug borders"
            >
              Borders
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
