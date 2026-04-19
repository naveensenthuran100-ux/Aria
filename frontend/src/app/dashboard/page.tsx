'use client';
import React, { useState, useEffect } from 'react';
import GlassCard from '@/components/GlassCard';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Info, Bell, BellOff } from 'lucide-react';
import GuidedRoutineModal from '@/components/GuidedRoutineModal';
import { StressReliefTools } from '@/components/StressReliefTools';
import { motion, AnimatePresence } from 'framer-motion';

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
  const [showPostureBreakdown, setShowPostureBreakdown] = useState(false);
  const [liveMetrics, setLiveMetrics] = useState<any>(null);

  // Poll for latest aggregated stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/sessions');
        const data = await res.json();
        if (data && data.length > 0) {
          setLiveMetrics(data[0]); // Use latest session
        }
      } catch (e) {
        console.error("Dashboard sync error:", e);
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const postureScore = liveMetrics?.posture_score || 85;

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
        <GlassCard 
          className={`p-6 transition-all duration-300 cursor-pointer hover:shadow-lg ${showPostureBreakdown ? 'bg-white/80 ring-1 ring-[var(--accent)]/20' : ''}`}
          onClick={() => setShowPostureBreakdown(!showPostureBreakdown)}
        >
          <div className="flex justify-between items-center mb-1">
            <div className="flex items-center gap-2">
              <div className="text-[11px] font-bold text-[#9CA3AF] uppercase tracking-widest">Posture Score</div>
              {liveMetrics?.is_live && (
                <span className="flex items-center gap-1 text-[8px] px-1.5 py-0.5 bg-[#2D5A27] text-white rounded-full font-bold animate-pulse">
                  <div className="w-1 h-1 bg-white rounded-full"></div> LIVE
                </span>
              )}
            </div>
            <div className="relative group/tip">
              <Info size={14} className="text-[#9CA3AF] hover:text-[#1C1C1E] cursor-help transition-colors" />
              <div className="pointer-events-none absolute right-0 bottom-full mb-3 opacity-0 group-hover/tip:opacity-100 transition-all duration-200 transform translate-y-2 group-hover/tip:translate-y-0 w-52 p-3 bg-[#1C1C1E] text-white text-[11px] leading-relaxed rounded-2xl shadow-2xl z-[100] font-bold border border-white/10">
                Overall posture health derived from tracking spine alignment and head position.
                <div className="absolute top-full right-2 -mt-1 border-4 border-transparent border-t-[#1C1C1E]"></div>
              </div>
            </div>
          </div>
          <div className="text-4xl font-extrabold text-[#1C1C1E] tracking-tight">
            {postureScore}
            <span className="text-lg text-[#9CA3AF] font-bold ml-1">/100</span>
          </div>
          <div className="mt-2 text-xs text-[#2D5A27] font-bold flex items-center justify-between">
            <span>↑ 5% from yesterday</span>
            <span className={`text-[10px] uppercase transition-opacity duration-300 ${showPostureBreakdown ? 'text-[var(--accent)] opacity-100' : 'text-[#9CA3AF] opacity-60'}`}>
              {showPostureBreakdown ? 'Hide Details' : 'Click to explain'}
            </span>
          </div>

          <AnimatePresence>
            {showPostureBreakdown && (
              <motion.div 
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-6 pt-4 border-t border-black/5 space-y-3">
                  <div className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider mb-2">Detailed Breakdown</div>
                  
                  {Object.entries({
                    "Neck Alignment": liveMetrics?.posture_details?.hn_penalty || 8.0,
                    "Forward Head": liveMetrics?.posture_details?.head_fwd_penalty || 5.0,
                    "Shoulder Tilt": liveMetrics?.posture_details?.slope_penalty || 2.0,
                    "Upper Back Slouch": liveMetrics?.posture_details?.slouch_penalty || 0.0,
                    "Lower Back Tension": liveMetrics?.posture_details?.back_penalty || 0.0
                  }).map(([label, val], i) => (
                    <div key={i} className="flex justify-between items-center text-xs font-bold">
                      <span className="text-[#6B7280]">{label}</span>
                      <span className={val > 5 ? "text-[#B05A5A]" : "text-[#9CA3AF]"}>
                        {val > 0 ? `-${val}%` : "0%"}
                      </span>
                    </div>
                  ))}
                  
                  <div className="mt-2 p-2 bg-[#2D5A27]/5 rounded-lg text-[10px] text-[#2D5A27] font-bold leading-tight">
                    {postureScore > 80 
                      ? "Great work! Your spinal alignment is stable. Keep this core tension." 
                      : "We noticed some slouching. Try rolling your shoulders back and lifting your chin."}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </GlassCard>
        
        <GlassCard className="p-6">
          <div className="flex justify-between items-center mb-2">
            <div className="text-[11px] font-bold text-[#9CA3AF] uppercase tracking-widest">Stress Index</div>
            <div className="relative group/tip">
              <Info size={14} className="text-[#9CA3AF] hover:text-[#1C1C1E] cursor-help transition-colors" />
              <div className="pointer-events-none absolute right-0 bottom-full mb-2 opacity-0 group-hover/tip:opacity-100 transition-opacity w-48 p-3 bg-[#1C1C1E] text-white text-[11px] leading-relaxed rounded-xl shadow-xl z-20 font-bold">
                Calculated by observing blink rates and facial strain relative to your baseline.
                <div className="absolute top-full right-1 -mt-1 border-4 border-transparent border-t-[#1C1C1E]"></div>
              </div>
            </div>
          </div>
          <div className="text-4xl font-extrabold text-[#1C1C1E]">Low</div>
          <div className="mt-2 text-xs text-[#9CA3AF] font-bold uppercase tracking-wider">Stable levels</div>
        </GlassCard>

        <GlassCard className="p-6">
          <div className="flex justify-between items-center mb-2">
            <div className="text-[11px] font-bold text-[#9CA3AF] uppercase tracking-widest">Time Seated</div>
            <div className="relative group/tip">
              <Info size={14} className="text-[#9CA3AF] hover:text-[#1C1C1E] cursor-help transition-colors" />
              <div className="pointer-events-none absolute right-0 bottom-full mb-2 opacity-0 group-hover/tip:opacity-100 transition-opacity w-48 p-3 bg-[#1C1C1E] text-white text-[11px] leading-relaxed rounded-xl shadow-xl z-20 font-bold">
                Continuous minutes seated. We recommend a standing break every 60 minutes.
                <div className="absolute top-full right-1 -mt-1 border-4 border-transparent border-t-[#1C1C1E]"></div>
              </div>
            </div>
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
