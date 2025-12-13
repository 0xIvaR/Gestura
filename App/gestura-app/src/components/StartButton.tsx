import React, { useCallback, useState } from 'react';
import { useApp } from '../context/AppContext';
import { FiPlay, FiSquare } from 'react-icons/fi';
import { startGestureControl, stopGestureControl, updateSettings } from '../utils/api';

const StartButton: React.FC = () => {
  const { isActive, toggleActive, smoothness, sensitivity, liveCameraPreview, mode } = useApp();
  const [loading, setLoading] = useState(false);

  const handleClick = useCallback(async () => {
    if (loading) return;
    setLoading(true);
    try {
      await updateSettings({ mode, smoothness, sensitivity, liveCameraPreview });
      if (!isActive) {
        await startGestureControl();
        toggleActive(true);
      } else {
        await stopGestureControl();
        toggleActive(false);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [loading, isActive, mode, smoothness, sensitivity, liveCameraPreview, toggleActive]);

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className={
        'focus-outline inline-flex items-center gap-3 px-8 py-4 rounded-2xl text-lg font-medium text-[#1A1A1A] shadow-brand transition duration-300 ease-in-out btn-primary ' +
        (isActive ? 'btn-primary--active' : '')
      }
    >
      {isActive ? <FiSquare size={20} /> : <FiPlay size={20} />}
      {isActive ? 'Stop Gesture Control' : 'Start Gesture Control'}
    </button>
  );
};

export default StartButton;


