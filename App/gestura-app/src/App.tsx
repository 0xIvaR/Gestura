import React from 'react';
import { AppProvider } from './context/AppContext';
import Sidebar from './components/Sidebar';
import CursorControl from './components/CursorControl';
import StartButton from './components/StartButton';
import StatusBar from './components/StatusBar';

const App: React.FC = () => {
  return (
    <AppProvider>
      <div className="w-full h-full gradient-background gradient-animated">
        <div className="min-h-full w-full p-10 flex flex-col gap-8">
          <header className="text-center select-none">
            <h1 className="brand-title text-4xl font-semibold text-[#1A1A1A] tracking-tight">GESTURA</h1>
          </header>

          <main className="flex-1 grid grid-cols-[180px,1fr] gap-6 items-start">
            <aside className="glass-card p-6 rounded-[20px]">
              <Sidebar />
            </aside>
            <section className="glass-card p-8">
              <CursorControl />
            </section>
          </main>

          <div className="flex justify-center">
            <StartButton />
          </div>

          <footer className="status-bar h-[60px] px-8 flex items-center justify-center gap-6">
            <StatusBar />
          </footer>
        </div>
      </div>
    </AppProvider>
  );
};

export default App;


