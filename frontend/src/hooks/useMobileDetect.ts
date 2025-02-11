import { createSignal, onMount, onCleanup } from 'solid-js';

export const useMobileDetect = () => {
  const [isMobile, setIsMobile] = createSignal(window.innerWidth < 768);
  
  const checkMobile = () => setIsMobile(window.innerWidth < 768);

  onMount(() => {
    window.addEventListener('resize', checkMobile);
  });

  onCleanup(() => {
    window.removeEventListener('resize', checkMobile);
  });

  return isMobile;
}; 