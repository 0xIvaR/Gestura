import React from 'react';
import { useApp } from '../context/AppContext';

const Slider: React.FC<{
  label: string;
  value: number;
  onChange: (value: number) => void;
}> = ({ label, value, onChange }) => {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-[#2D3748] text-base font-medium">{label}</span>
        <span className="text-[#4A4A4A] text-sm">{value}</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-[6px] rounded-[3px] appearance-none focus:outline-none bg-[rgba(200,200,200,0.3)] range-filled"
        style={{ ['--value' as any]: `${value}%` }}
        aria-label={label}
      />
    </div>
  );
};

const Toggle: React.FC<{ label: string; checked: boolean; onChange: (v: boolean) => void }> = ({ label, checked, onChange }) => {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[#2D3748] text-base font-medium">{label}</span>
      <label className="inline-block" aria-label={label} title={label}>
        <span className="relative inline-block w-12 h-7 align-middle">
          <input
            type="checkbox"
            className="sr-only peer"
            checked={checked}
            onChange={(e) => onChange(e.target.checked)}
          />
          <span className="absolute inset-0 rounded-full transition-colors duration-200 ease-in-out bg-[rgba(200,200,200,0.3)] peer-checked:bg-[rgba(127,205,187,0.6)]" />
          <span className="absolute top-0.5 left-0.5 w-6 h-6 rounded-full bg-white shadow transition-transform duration-200 ease-in-out peer-checked:translate-x-5" />
        </span>
      </label>
    </div>
  );
};

const CursorControl: React.FC = () => {
  const { smoothness, sensitivity, liveCameraPreview, setSmoothness, setSensitivity, setLiveCameraPreview } = useApp();

  return (
    <div className="flex flex-col gap-8">
      <h2 className="text-2xl font-medium text-[#1A1A1A] tracking-tight">Cursor Control</h2>

      <div className="flex flex-col gap-6">
        <Slider label="Smoothness" value={smoothness} onChange={setSmoothness} />
        <Slider label="Sensitivity" value={sensitivity} onChange={setSensitivity} />
        <Toggle label="Live Camera Preview" checked={liveCameraPreview} onChange={setLiveCameraPreview} />
      </div>
    </div>
  );
};

export default CursorControl;


