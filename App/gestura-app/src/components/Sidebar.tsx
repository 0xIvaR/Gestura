import React from 'react';
import { useApp } from '../context/AppContext';
import { FiBookOpen, FiSettings } from 'react-icons/fi';

const Sidebar: React.FC = () => {
  const { mode, setMode } = useApp();

  const Item: React.FC<{ label: 'Study' | 'General'; icon: React.ReactNode }> = ({ label, icon }) => {
    const active = mode === label;
    return (
      <button
        onClick={() => setMode(label)}
        className={
          'w-full flex flex-col items-center gap-2 p-4 rounded-xl transition duration-200 ease-in-out focus-outline ' +
          (active ? 'bg-white/40' : 'hover:bg-white/20')
        }
        aria-label={`Select ${label} mode`}
      >
        <div className="text-[#1A1A1A] opacity-90">{icon}</div>
        <span className="text-sm font-medium text-[#2D3748]">{label}</span>
      </button>
    );
  };

  return (
    <nav className="flex flex-col gap-3">
      <Item label="Study" icon={<FiBookOpen size={24} strokeWidth={1.5} />} />
      <Item label="General" icon={<FiSettings size={24} strokeWidth={1.5} />} />
    </nav>
  );
};

export default Sidebar;


