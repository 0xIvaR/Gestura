import React, { useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { FiCamera } from 'react-icons/fi';
import { getStatus } from '../utils/api';

const Dot: React.FC<{ intent: 'ready' | 'active' }> = ({ intent }) => {
  const className = intent === 'active' ? 'bg-[#4CAF50]' : 'bg-[#7FCDBB]';
  return <span className={`inline-block w-2 h-2 rounded-full ${className}`} aria-hidden="true" />;
};

const StatusBar: React.FC = () => {
  const { status, cameraConnected, setCameraConnected } = useApp();

  useEffect(() => {
    let mounted = true;
    const poll = async () => {
      try {
        const data = await getStatus();
        if (!mounted) return;
        if (typeof data?.cameraConnected === 'boolean') setCameraConnected(data.cameraConnected);
      } catch {
        if (!mounted) return;
        setCameraConnected(false);
      } finally {
        if (mounted) setTimeout(poll, 2000);
      }
    };
    poll();
    return () => { mounted = false; };
  }, [setCameraConnected]);

  return (
    <div className="w-full flex items-center justify-center gap-6">
      <div className="flex items-center gap-2 text-sm text-[#2C2C2C]">
        <Dot intent={status} />
        <span>Status: {status}</span>
      </div>
      <div className="w-px h-6 bg-black/10" />
      <div className="flex items-center gap-2 text-sm text-[#2C2C2C]">
        <FiCamera size={16} />
        <span>{cameraConnected ? 'Camera connected' : 'Camera disconnected'}</span>
      </div>
    </div>
  );
};

export default StatusBar;


