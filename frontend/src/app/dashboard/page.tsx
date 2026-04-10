'use client';
import React, { useState } from 'react';
import GlassCard from '@/components/GlassCard';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Info, Bell, BellOff } from 'lucide-react';
import GuidedRoutineModal from '@/components/GuidedRoutineModal';
import { StressReliefTools } from '@/components/StressReliefTools';

const mockData = [
  { time: '10:00', posture: 85, stress: 20 },
  { time: '10:30', posture: 82, stress: 25 },
  { time: '11:00', posture: 70, stress: 45 },
  { time: '11:30', posture: 65, stress: 60 },
  { time: '12:00', posture: 90, stress: 30 },
  { time: '12:30', posture: 95, stress: 15 },
  { time: '13:00', posture: 80, stress: 35 },
];

export default function DashboardPage() {
  const [dndActive, setDndActive] = useState(false);
  const [routineId, setRoutineId] = useState<string | null>(null);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-12 font-sans">
      {/* Header */}
      <div className="flex justify-between items-end pb-4 border-b border-[rgba(0,0,0,0.05)]">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-[#1C1C1E]">Dashboard</h1>
          <p className="text-[#6B7280] mt-1 font-medium">Overview of your recent wellness and posture data.</p>
        </div>
        <button 
          onClick={() => setDndActive(!dndActive)}
          title="Toggle Do Not Disturb Mode"
          className={`flex items-center gap-2 px-5 py-2.5 font-bold rounded-2xl transition-all text-sm shadow-sm ${dndActive ? 'bg-[#2D5A27] text-white' : 'bg-white/60 border border-[rgba(0,0,0,0.05)] text-[#1C1C1E] hover:bg-white'}`}
        >
          {dndActive ? <BellOff size={16} /> : <Bell size={16} />} 
          {dndActive ? "DND Active" : "Alerts On"}
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <GlassCard className="p-6">
          <div className="flex justify-between items-center mb-2 group relative">
            <div className="text-[11px] font-bold text-[#9CA3AF] uppercase tracking-widest">Posture Score</div>
            <Info size={14} className="text-[#9CA3AF] hover:text-[#1C1C1E] cursor-help" />
          </div>
          <div className="text-4xl font-extrabold text-[#1C1C1E]">85<span className="text-lg text-[#9CA3AF] font-bold ml-1">/100</span></div>
          <div className="mt-2 text-xs text-[#2D5A27] font-bold">↑ 5% from yesterday</div>
        </GlassCard>
        
        <GlassCard className="p-6">
          <div className="flex justify-between items-center mb-2 group relative">
            <div className="text-[11px] font-bold text-[#9CA3AF] uppercase tracking-widest">Stress Index</div>
            <Info size={14} className="text-[#9CA3AF] hover:text-[#1C1C1E] cursor-help" />
          </div>
          <div className="text-4xl font-extrabold text-[#1C1C1E]">Low</div>
          <div className="mt-2 text-xs text-[#9CA3AF] font-bold uppercase tracking-wider">Stable levels</div>
        </GlassCard>

        <GlassCard className="p-6">
          <div className="flex justify-between items-center mb-2 group relative">
            <div className="text-[11px] font-bold text-[#9CA3AF] uppercase tracking-widest">Time Seated</div>
            <Info size={14} className="text-[#9CA3AF] hover:text-[#1C1C1E] cursor-help" />
          </div>
          <div className="text-4xl font-extrabold text-[#1C1C1E]">45<span className="text-lg text-[#9CA3AF] font-bold ml-1">m</span></div>
          <div className="mt-2 text-xs text-[#B05A5A] font-bold uppercase tracking-wider">Consider a stretch</div>
        </GlassCard>
      </div>

      {/* Chart */}
      <GlassCard className="h-[420px] p-8 flex flex-col">
        <div className="mb-8">
          <h2 className="text-xl font-extrabold text-[#1C1C1E] tracking-tight">Today's Trends</h2>
        </div>
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={mockData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
              <defs>
                <linearGradient id="colorPosture" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2D5A27" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#2D5A27" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorStress" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#B05A5A" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#B05A5A" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="rgba(0,0,0,0.03)" />
              <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fill: '#9CA3AF', fontSize: 11, fontWeight: 600 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#9CA3AF', fontSize: 11, fontWeight: 600 }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  borderRadius: '16px',
                  border: 'none',
                  boxShadow: '0 10px 30px rgba(0,0,0,0.05)',
                  fontSize: '12px',
                  fontWeight: 'bold'
                }} 
              />
              <Area type="monotone" dataKey="posture" stroke="#2D5A27" strokeWidth={3} fillOpacity={1} fill="url(#colorPosture)" />
              <Area type="monotone" dataKey="stress" stroke="#B05A5A" strokeWidth={3} fillOpacity={1} fill="url(#colorStress)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>

      {/* Stress & Routines Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* Left: Stress Relief Section (Matched to screenshot layout) */}
        <StressReliefTools />

        {/* Right: Interactive Routines (Icon-less minimalist cards) */}
        <div className="flex flex-col gap-4">
          <h3 className="text-sm font-bold text-[#6B7280] uppercase tracking-[0.1em]">
            Physical Reset
          </h3>
          <p className="text-sm text-[#9CA3AF] -mt-2">Guided posture corrections.</p>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-1">
            <button 
              onClick={() => setRoutineId('shoulderDrop')}
              className="text-left p-6 rounded-3xl bg-white border border-white hover:bg-[#FDFCF9] transition-all shadow-sm group active:scale-[0.98]"
            >
              <div className="text-xl font-extrabold text-[#1C1C1E] mb-1 group-hover:text-[#2D5A27] transition-colors">
                Shoulder drop
              </div>
              <div className="text-sm text-[#6B7280]">4 steps • 15 seconds</div>
            </button>

            <button 
              onClick={() => setRoutineId('neckRelease')}
              className="text-left p-6 rounded-3xl bg-white border border-white hover:bg-[#FDFCF9] transition-all shadow-sm group active:scale-[0.98]"
            >
              <div className="text-xl font-extrabold text-[#1C1C1E] mb-1 group-hover:text-[#2D5A27] transition-colors">
                Neck release
              </div>
              <div className="text-sm text-[#6B7280]">4 steps • Gentle reset</div>
            </button>
          </div>
        </div>
      </div>

      <GuidedRoutineModal routineId={routineId} onClose={() => setRoutineId(null)} />
    </div>
  );
}
