import React, { createContext, useContext, useState, useMemo } from 'react';

export type AppState = {
  mode: 'Study' | 'General';
  smoothness: number;
  sensitivity: number;
  liveCameraPreview: boolean;
  isActive: boolean;
  cameraConnected: boolean;
  status: 'ready' | 'active';
};

type AppContextValue = AppState & {
  setMode: (mode: 'Study' | 'General') => void;
  setSmoothness: (value: number) => void;
  setSensitivity: (value: number) => void;
  setLiveCameraPreview: (value: boolean) => void;
  toggleActive: (active?: boolean) => void;
  setCameraConnected: (connected: boolean) => void;
  setStatus: (status: 'ready' | 'active') => void;
};

const initialState: AppState = {
  mode: 'Study',
  smoothness: 50,
  sensitivity: 30,
  liveCameraPreview: false,
  isActive: false,
  cameraConnected: true,
  status: 'ready'
};

const AppContext = createContext<AppContextValue | null>(null);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AppState>(initialState);

  const value = useMemo<AppContextValue>(() => ({
    ...state,
    setMode: (mode) => setState((s) => ({ ...s, mode })),
    setSmoothness: (smoothness) => setState((s) => ({ ...s, smoothness })),
    setSensitivity: (sensitivity) => setState((s) => ({ ...s, sensitivity })),
    setLiveCameraPreview: (liveCameraPreview) => setState((s) => ({ ...s, liveCameraPreview })),
    toggleActive: (active) => setState((s) => ({ ...s, isActive: typeof active === 'boolean' ? active : !s.isActive, status: typeof active === 'boolean' ? (active ? 'active' : 'ready') : (!s.isActive ? 'active' : 'ready') })),
    setCameraConnected: (cameraConnected) => setState((s) => ({ ...s, cameraConnected })),
    setStatus: (status) => setState((s) => ({ ...s, status }))
  }), [state]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useApp = (): AppContextValue => {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
};



