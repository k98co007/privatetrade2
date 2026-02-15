import { useEffect } from 'react';

import { useUiStore } from '../store/uiStore';

export function useNetworkStatus() {
  const setNetworkState = useUiStore((state) => state.setNetworkState);

  useEffect(() => {
    const onOnline = () => setNetworkState('online');
    const onOffline = () => setNetworkState('offline');

    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);

    if (!navigator.onLine) {
      setNetworkState('offline');
    }

    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }, [setNetworkState]);
}
