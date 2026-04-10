"use client";
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import GlassCard from '@/components/GlassCard';
import { RefreshCw, Bell, Moon } from 'lucide-react';

export default function SettingsPage() {
  const router = useRouter();
  const [dndEnabled, setDndEnabled] = useState(false);
  const [notifStyle, setNotifStyle] = useState('gentle');

  const handleRecalibrate = () => {
    // Redo the onboarding to recalibrate baseline for demo purposes
    router.push('/');
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
      <div className="flex justify-between items-end pb-4 border-b border-[rgba(0,0,0,0.05)]">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">Settings</h1>
          <p className="text-[var(--text-secondary)] mt-1">Manage your profile, thresholds, and AI privacy.</p>
        </div>
        <button 
          onClick={handleRecalibrate}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--text-primary)] text-white font-medium rounded-xl hover:bg-black transition-colors text-sm shadow-sm"
        >
          <RefreshCw size={14} /> Redo Onboarding
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Signal Controls */}
        <GlassCard>
          <h2 className="text-lg font-bold text-[var(--text-primary)] tracking-tight mb-4">Signal Controls</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-white/40 rounded-xl border border-white/50">
              <div>
                <div className="font-semibold text-sm text-[var(--text-primary)]">Target Posture Score</div>
                <div className="text-xs text-[var(--text-muted)]">Minimum acceptable score (0-100)</div>
              </div>
              <input type="number" defaultValue="75" className="w-16 bg-white border border-[rgba(0,0,0,0.1)] rounded-lg px-2 py-1 text-sm text-center" />
            </div>
            
            <div className="flex items-center justify-between p-3 bg-white/40 rounded-xl border border-white/50">
              <div>
                <div className="font-semibold text-sm text-[var(--text-primary)]">Sitting Timeout</div>
                <div className="text-xs text-[var(--text-muted)]">Minutes before stretch reminder</div>
              </div>
              <input type="number" defaultValue="45" className="w-16 bg-white border border-[rgba(0,0,0,0.1)] rounded-lg px-2 py-1 text-sm text-center" />
            </div>

            <div className="flex items-center justify-between p-3 bg-white/40 rounded-xl border border-white/50">
              <div>
                <div className="font-semibold text-sm text-[var(--text-primary)]">Keyboard Tracking</div>
                <div className="text-xs text-[var(--text-muted)]">Monitor typing patterns for stress</div>
              </div>
              <div 
                className="w-10 h-5 bg-[#4F46E5] rounded-full relative shadow-inner cursor-pointer"
              >
                <div className="w-4 h-4 bg-white rounded-full absolute top-0.5 shadow-sm translate-x-5"></div>
              </div>
            </div>
          </div>
        </GlassCard>

        {/* Notifications & DND */}
        <GlassCard>
          <h2 className="text-lg font-bold text-[var(--text-primary)] tracking-tight mb-4">Notifications & Focus</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-white/40 rounded-xl border border-white/50">
              <div className="flex gap-3 items-center">
                <Bell size={20} className="text-[var(--accent)]" />
                <div>
                  <div className="font-semibold text-sm text-[var(--text-primary)]">Notification Style</div>
                  <div className="text-xs text-[var(--text-muted)]">Tone of posture reminders</div>
                </div>
              </div>
              <select 
                value={notifStyle} 
                onChange={(e) => setNotifStyle(e.target.value)}
                className="bg-white border border-[rgba(0,0,0,0.1)] rounded-lg px-2 py-1 text-sm"
              >
                <option value="gentle">Gentle</option>
                <option value="assertive">Assertive</option>
                <option value="strict">Strict Coach</option>
              </select>
            </div>

            <div className="flex items-start justify-between p-3 bg-white/40 rounded-xl border border-white/50">
              <div className="flex gap-3 items-center">
                <Moon size={20} className="text-[#4F46E5]" />
                <div>
                   <div className="font-semibold text-sm text-[var(--text-primary)]">Do Not Disturb (DND)</div>
                   <div className="text-xs text-[var(--text-muted)]">Mute session alerts during meetings</div>
                </div>
              </div>
              <div 
                onClick={() => setDndEnabled(!dndEnabled)}
                className={`w-10 h-5 rounded-full relative shadow-inner cursor-pointer transition-colors ${dndEnabled ? 'bg-[#4F46E5]' : 'bg-[rgba(0,0,0,0.1)]'}`}
              >
                <div className={`w-4 h-4 bg-white rounded-full absolute top-0.5 shadow-sm transition-transform ${dndEnabled ? 'translate-x-5' : 'translate-x-0.5'}`}></div>
              </div>
            </div>
             
            {dndEnabled && (
               <div className="flex gap-2 items-center pl-11 pr-3 py-1 animate-in fade-in zoom-in duration-200">
                  <div className="text-[10px] uppercase font-bold text-[var(--text-secondary)]">DND Range:</div>
                  <input type="time" defaultValue="13:00" className="bg-white border border-[rgba(0,0,0,0.1)] rounded px-1.5 py-0.5 text-xs text-center" />
                  <span className="text-xs">—</span>
                  <input type="time" defaultValue="14:00" className="bg-white border border-[rgba(0,0,0,0.1)] rounded px-1.5 py-0.5 text-xs text-center" />
               </div>
            )}
          </div>
        </GlassCard>

        {/* AI Transparency */}
        <GlassCard className="md:col-span-2">
          <h2 className="text-lg font-bold text-[var(--text-primary)] tracking-tight mb-4">AI Transparency & Data Privacy</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 bg-[var(--text-primary)] text-white rounded-xl">
              <div className="font-semibold text-sm mb-1 text-[var(--warning)]">Local ML Processing Only</div>
              <div className="text-xs leading-relaxed opacity-90">
                All data (camera frames, voice signals, typing rhythms) is processed securely on this machine via FastAPI. 
                External API requests to Groq only include statistical metadata, never raw imagery.
              </div>
            </div>
            
            <div className="flex flex-col justify-center gap-3 p-3 bg-white/40 rounded-xl border border-white/50">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-sm">Save Session Data</div>
                  <div className="text-xs text-[var(--text-muted)]">Store telemetry in local SQLite DB</div>
                </div>
                <div className="w-10 h-5 bg-[var(--success)] rounded-full relative shadow-inner cursor-pointer">
                  <div className="w-4 h-4 bg-white rounded-full absolute translate-x-5 top-0.5 shadow-sm"></div>
                </div>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
