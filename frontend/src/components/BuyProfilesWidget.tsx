import { Component, createSignal } from 'solid-js';
import { Settings, ChevronDown, Check } from 'lucide-solid';

interface BuyProfilesWidgetProps {
  class?: string;
}

export const BuyProfilesWidget: Component<BuyProfilesWidgetProps> = (props) => {
  const [selectedProfile, setSelectedProfile] = createSignal('basic');
  const [isDropdownOpen, setIsDropdownOpen] = createSignal(false);
  const [settings, setSettings] = createSignal({
    autoRenew: true,
    notifications: true,
    autoScan: false,
    priorityAccess: true
  });

  return (
    <div class={props.class}>
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-sm font-semibold text-white">Buy Profiles</h2>
        <Settings size={14} class="text-gray-400" />
      </div>
      
      {/* Profile Selector Dropdown */}
      <div class="relative mb-2">
        <button 
          onClick={() => setIsDropdownOpen(!isDropdownOpen())}
          class="w-full flex items-center justify-between bg-black/20 hover:bg-black/30 text-white px-2 py-1.5 rd transition-colors text-xs"
        >
          <span class="capitalize">{selectedProfile()} Profile</span>
          <ChevronDown size={12} class={`transform transition-transform ${isDropdownOpen() ? 'rotate-180' : ''}`} />
        </button>
        
        {isDropdownOpen() && (
          <div class="absolute w-full mt-1 bg-black/90 border border-gray-700 rd shadow-lg z-10">
            {['basic', 'pro', 'enterprise'].map(profile => (
              <button
                class="w-full px-2 py-1.5 text-left text-xs text-white hover:bg-white/10 transition-colors flex items-center justify-between"
                onClick={() => {
                  setSelectedProfile(profile);
                  setIsDropdownOpen(false);
                }}
              >
                <span class="capitalize">{profile}</span>
                {selectedProfile() === profile && <Check size={12} />}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Combined Price and Settings */}
      <div class="bg-black/20 p-2 rd mb-2">
        <div class="flex justify-between items-center mb-1">
          <span class="text-xs text-gray-400">Monthly Price</span>
          <span class="text-xs text-white font-medium">
            {selectedProfile() === 'basic' ? '$19.99' :
             selectedProfile() === 'pro' ? '$49.99' :
             '$99.99'}
          </span>
        </div>
        <div class="grid grid-cols-2 gap-x-4 gap-y-1">
          <label class="flex items-center justify-between text-xs">
            <span class="text-gray-300">Auto Renew</span>
            <input 
              type="checkbox" 
              checked={settings().autoRenew}
              onChange={(e) => setSettings({...settings(), autoRenew: e.currentTarget.checked})}
              class="rd border-gray-600 h-3 w-3"
            />
          </label>
          <label class="flex items-center justify-between text-xs">
            <span class="text-gray-300">Auto Scan</span>
            <input 
              type="checkbox" 
              checked={settings().autoScan}
              onChange={(e) => setSettings({...settings(), autoScan: e.currentTarget.checked})}
              class="rd border-gray-600 h-3 w-3"
            />
          </label>
        </div>
      </div>

      {/* Features List - Compact */}
      <div class="mb-2">
        <div class="text-2xs text-gray-400 mb-1">Features included:</div>
        <div class="grid grid-cols-2 gap-1 text-2xs text-gray-300">
          <div class="flex items-center gap-1">
            <Check size={10} class="text-green-500" />
            <span>Real-time scanning</span>
          </div>
          <div class="flex items-center gap-1">
            <Check size={10} class="text-green-500" />
            <span>Analytics</span>
          </div>
          <div class="flex items-center gap-1">
            <Check size={10} class="text-green-500" />
            <span>Priority support</span>
          </div>
          <div class="flex items-center gap-1">
            <Check size={10} class="text-green-500" />
            <span>Auto updates</span>
          </div>
        </div>
      </div>
      
      {/* Action Buttons */}
      <div class="flex gap-2">
        <button class="flex-1 bg-blue-500/50 hover:bg-blue-500/70 text-white py-1.5 rd text-xs transition-colors">
          Upgrade
        </button>
        <button class="flex-1 bg-gray-700/30 hover:bg-gray-700/50 text-gray-300 py-1.5 rd text-xs transition-colors">
          Details
        </button>
      </div>
    </div>
  );
}; 