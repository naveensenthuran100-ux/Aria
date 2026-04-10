'use client';
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, X } from 'lucide-react';

// ─── Shared palette matching the app's refined Inter aesthetic ─────────────────────
const BG = '#F7F4EE';
const GREEN_DARK = '#2D5A27';
const GREEN_PROGRESS = '#2D5A27';

// ─── 5-4-3-2-1 GROUNDING MODAL ─────────────────────────────────────────────
const GROUNDING_STEPS = [
  { count: 5, sense: 'See',   prompt: 'Notice 5 things around you. Let your eyes move slowly.' },
  { count: 4, sense: 'Touch', prompt: 'Notice 4 things you can feel. Chair, clothes, air, hands.' },
  { count: 3, sense: 'Hear',  prompt: 'Notice 3 sounds around you. Near and far both count.' },
  { count: 2, sense: 'Smell', prompt: 'Notice 2 scents. Fresh air, fabric, anything subtle.' },
  { count: 1, sense: 'Taste', prompt: 'Notice 1 thing you can taste. Breathe slowly as you do.' },
];

function GroundingModal({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState(0);
  const isLast = step === GROUNDING_STEPS.length - 1;
  const current = GROUNDING_STEPS[step];

  return (
    <div className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center">
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose}
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
      />
      <motion.div
        initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 40 }}
        className="relative w-full max-w-md rounded-t-[32px] sm:rounded-[32px] overflow-hidden shadow-2xl flex flex-col font-sans"
        style={{ background: BG, minHeight: 480 }}
      >
        {/* Pill */}
        <div className="flex justify-center pt-3 pb-1 sm:hidden">
          <div className="w-10 h-1 bg-[#D4CFC6] rounded-full" />
        </div>

        <div className="px-8 pt-4 pb-8 flex flex-col flex-1">
          {/* Back row */}
          <div className="flex justify-between items-center mb-6">
            <button
              onClick={() => step > 0 ? setStep(s => s - 1) : onClose()}
              style={{ color: GREEN_DARK }}
              className="flex items-center gap-1 font-bold text-sm"
            >
              <ChevronLeft size={18} /> Back
            </button>
            <button onClick={onClose} className="p-1 text-[#9CA3AF] hover:text-[#4B5563]">
              <X size={20} />
            </button>
          </div>

          {/* Dot progress */}
          <div className="flex justify-center gap-2 mb-10">
            {GROUNDING_STEPS.map((_, i) => (
              <div
                key={i}
                className="w-2.5 h-2.5 rounded-full transition-all"
                style={{ background: i === step ? GREEN_DARK : '#D4CFC6' }}
              />
            ))}
          </div>

          {/* Content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.25 }}
              className="flex flex-col items-center text-center flex-1"
            >
              {/* Large number */}
              <div
                className="text-[120px] font-bold leading-none select-none mb-1 tracking-tight"
                style={{ color: '#E5EADF' }} // Light green/grey for the number
              >
                {current.count}
              </div>

              {/* Sense word */}
              <div className="text-4xl font-extrabold mb-4 tracking-tight" style={{ color: GREEN_DARK }}>
                {current.sense}
              </div>

              {/* Prompt */}
              <p className="text-[#6B7280] text-[16px] leading-relaxed max-w-xs font-medium">
                {current.prompt}
              </p>
            </motion.div>
          </AnimatePresence>

          {/* CTA */}
          <button
            onClick={() => { if (!isLast) setStep(s => s + 1); else { setStep(0); onClose(); } }}
            className="mt-8 w-full py-4.5 rounded-2xl font-bold text-white text-[16px] transition-all shadow-lg active:scale-[0.98]"
            style={{ background: GREEN_DARK }}
          >
            {isLast ? 'Done' : 'I noticed them'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ─── BOX BREATHING MODAL ────────────────────────────────────────────────────
const PHASES = ['Breathe in', 'Hold', 'Breathe out', 'Hold'] as const;
type Phase = typeof PHASES[number];
const PHASE_DURATION = 4;
const TOTAL_ROUNDS = 4;

function BoxBreathingModal({ onClose }: { onClose: () => void }) {
  const [phaseIdx, setPhaseIdx] = useState(0);
  const [timeLeft, setTimeLeft] = useState(PHASE_DURATION);
  const [round, setRound] = useState(1);
  const [running, setRunning] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const phase: Phase = PHASES[phaseIdx];
  const isExpanding = phase === 'Breathe in' || (phase === 'Hold' && phaseIdx === 1);

  useEffect(() => {
    if (running) {
      intervalRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            setPhaseIdx(pi => {
              const next = (pi + 1) % 4;
              if (next === 0) setRound(r => (r < TOTAL_ROUNDS ? r + 1 : r));
              return next;
            });
            return PHASE_DURATION;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
      setPhaseIdx(0);
      setTimeLeft(PHASE_DURATION);
      setRound(1);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [running]);

  const r = 95;
  const circumference = 2 * Math.PI * r;
  const progress = running ? 1 - (timeLeft / PHASE_DURATION) : 0;
  const strokeDash = circumference * progress;

  return (
    <div className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center">
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose}
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
      />
      <motion.div
        initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 40 }}
        className="relative w-full max-w-md rounded-t-[32px] sm:rounded-[32px] overflow-hidden shadow-2xl flex flex-col font-sans"
        style={{ background: BG, minHeight: 520 }}
      >
        {/* Pill */}
        <div className="flex justify-center pt-3 pb-1 sm:hidden">
          <div className="w-10 h-1 bg-[#D4CFC6] rounded-full" />
        </div>

        <div className="px-8 pt-4 pb-8 flex flex-col flex-1">
          <div className="flex justify-between items-center mb-6">
            <button
              onClick={onClose}
              style={{ color: GREEN_DARK }}
              className="flex items-center gap-1 font-bold text-sm"
            >
              <ChevronLeft size={18} /> Back
            </button>
            <button onClick={onClose} className="p-1 text-[#9CA3AF] hover:text-[#4B5563]">
              <X size={20} />
            </button>
          </div>

          {/* Phase + Countdown */}
          <div className="text-center mb-4">
            <AnimatePresence mode="wait">
              <motion.div
                key={phase}
                initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}
                className="text-3xl font-extrabold tracking-tight"
                style={{ color: GREEN_DARK }}
              >
                {running ? phase : 'Box Breathing'}
              </motion.div>
            </AnimatePresence>
            <div className="text-2xl font-bold mt-2 text-[#9CA3AF] tabular-nums">
              {running ? timeLeft : ''}
            </div>
            {!running && (
              <div className="text-[#6B7280] text-sm mt-1">A steady 4-4-4-4 cycle.</div>
            )}
          </div>

          {/* Orb + Ring */}
          <div className="flex-1 flex items-center justify-center relative">
            <div className="relative flex items-center justify-center" style={{ width: 240, height: 240 }}>
              <svg className="absolute inset-0" width={240} height={240} viewBox="0 0 240 240">
                <circle cx={120} cy={120} r={r} fill="none" stroke="#E2DDD8" strokeWidth={10} />
                {running && (
                  <circle
                    cx={120} cy={120} r={r}
                    fill="none" stroke={GREEN_DARK} strokeWidth={10} strokeLinecap="round"
                    strokeDasharray={`${strokeDash} ${circumference}`}
                    strokeDashoffset={0}
                    transform="rotate(-90 120 120)"
                    style={{ transition: 'stroke-dasharray 0.9s linear' }}
                  />
                )}
              </svg>

              <motion.div
                animate={{ scale: running ? (isExpanding ? 1.2 : 0.8) : 1 }}
                transition={{ duration: PHASE_DURATION * 0.9, ease: 'easeInOut' }}
                className="rounded-full shadow-2xl"
                style={{
                  width: 170, height: 170,
                  background: `linear-gradient(135deg, #5A9E4C, #2D5A27)`
                }}
              />
            </div>
          </div>

          <div className="text-center text-[#9CA3AF] text-sm font-semibold mb-8">
            {running ? `Round ${round} of ${TOTAL_ROUNDS}` : '4 rounds · ~1 minute'}
          </div>

          <button
            onClick={() => setRunning(r => !r)}
            className="w-full py-4.5 rounded-2xl font-bold text-[16px] transition-all shadow-lg shadow-black/5"
            style={running ? { background: '#E5E7EB', color: '#4B5563' } : { background: GREEN_DARK, color: '#fff' }}
          >
            {running ? 'End session' : 'Start session'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ─── DASHBOARD TOOLS ────────────────────────────────────────────────────────
export function StressReliefTools() {
  const [modal, setModal] = useState<'breathing' | 'grounding' | null>(null);

  return (
    <>
      <div className="flex flex-col gap-4">
        <h3 className="text-sm font-bold text-[var(--text-secondary)] uppercase tracking-[0.1em]">
          Stress Relief
        </h3>
        <p className="text-sm text-[var(--text-muted)] -mt-2">Pick what helps right now.</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <button
            onClick={() => setModal('breathing')}
            className="text-left p-6 rounded-3xl bg-white border border-white hover:bg-[#FDFCF9] transition-all shadow-sm group active:scale-[0.98]"
          >
            <div className="text-xl font-extrabold text-[#1C1C1E] mb-1 group-hover:text-[#2D5A27] transition-colors">
              Box breathing
            </div>
            <div className="text-sm text-[#6B7280]">A steady 4-4-4-4 cycle.</div>
          </button>

          <button
            onClick={() => setModal('grounding')}
            className="text-left p-6 rounded-3xl bg-white border border-white hover:bg-[#FDFCF9] transition-all shadow-sm group active:scale-[0.98]"
          >
            <div className="text-xl font-extrabold text-[#1C1C1E] mb-1 group-hover:text-[#2D5A27] transition-colors">
              Notice around you
            </div>
            <div className="text-sm text-[#6B7280]">A gentle 5-4-3-2-1 reset.</div>
          </button>
        </div>
      </div>

      <AnimatePresence>
        {modal === 'grounding' && <GroundingModal onClose={() => setModal(null)} />}
        {modal === 'breathing' && <BoxBreathingModal onClose={() => setModal(null)} />}
      </AnimatePresence>
    </>
  );
}
