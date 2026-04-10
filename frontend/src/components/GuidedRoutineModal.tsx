'use client';
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, X } from 'lucide-react';

interface RoutineStep {
  title: string;
  description: string;
  imagePath: string;
  holdTime: number;
}

interface RoutineConfig {
  id: string;
  title: string;
  subtitle: string;
  steps: RoutineStep[];
}

export const ROUTINES_DATA: Record<string, RoutineConfig> = {
  shoulderDrop: {
    id: "shoulderDrop",
    title: "Shoulder drop",
    subtitle: "Release upper-body tension with a soft shoulder reset.",
    steps: [
      { title: "Start position", description: "Sit tall. Let your arms rest naturally by your sides.", imagePath: "/shoulder_1.png", holdTime: 0 },
      { title: "Lift gently", description: "Inhale and bring both shoulders slightly up toward your ears.", imagePath: "/shoulder_2.png", holdTime: 5 },
      { title: "Drop and soften", description: "Exhale slowly and let both shoulders drop down. Keep your jaw relaxed.", imagePath: "/shoulder_3.png", holdTime: 8 },
      { title: "Reset", description: "Stay in this softer position and take one calm breath.", imagePath: "/shoulder_4.png", holdTime: 0 }
    ]
  },
  neckRelease: {
    id: "neckRelease",
    title: "Neck release",
    subtitle: "Ease neck tension with slow, gentle movement.",
    steps: [
      { title: "Start position", description: "Sit upright. Drop your shoulders and soften your face.", imagePath: "/neck_1.png", holdTime: 0 },
      { title: "Tilt left", description: "Bring your left ear toward your left shoulder. Keep the movement light.", imagePath: "/neck_2.png", holdTime: 5 },
      { title: "Tilt right", description: "Return to center, then bring your right ear toward your right shoulder.", imagePath: "/neck_3.png", holdTime: 5 },
      { title: "Return and breathe", description: "Come back to center and take one slower breath before continuing.", imagePath: "/neck_4.png", holdTime: 3 }
    ]
  }
};

export default function GuidedRoutineModal({
  routineId,
  onClose
}: {
  routineId: string | null;
  onClose: () => void;
}) {
  const [step, setStep] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [isCounting, setIsCounting] = useState(false);

  const routine = routineId ? ROUTINES_DATA[routineId] : null;

  useEffect(() => {
    if (routineId) setStep(0);
  }, [routineId]);

  useEffect(() => {
    if (!routine) return;
    const hold = routine.steps[step].holdTime;
    setTimeLeft(hold);
    setIsCounting(hold > 0);
  }, [step, routine]);

  useEffect(() => {
    if (!isCounting || timeLeft <= 0) return;
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) { setIsCounting(false); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [isCounting, timeLeft]);

  if (!routine) return null;

  const currentData = routine.steps[step];
  const isLastStep = step === routine.steps.length - 1;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[70] flex items-end sm:items-center justify-center">
        {/* Persistent Backdrop - moved outside the inner step transition to stay blurred throughout */}
        <motion.div
          initial={{ opacity: 0 }} 
          animate={{ opacity: 1 }} 
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/40 backdrop-blur-md"
        />

        <motion.div
          initial={{ opacity: 0, y: 50 }} 
          animate={{ opacity: 1, y: 0 }} 
          exit={{ opacity: 0, y: 50 }}
          className="relative w-full max-w-md bg-[#F7F4EE] rounded-t-[40px] sm:rounded-[40px] overflow-hidden shadow-2xl flex flex-col font-sans"
        >
          {/* Mobile Pill */}
          <div className="flex justify-center pt-3 pb-1 sm:hidden">
            <div className="w-10 h-1 bg-[#D4CFC6] rounded-full" />
          </div>

          <div className="px-8 pt-4 pb-10 flex flex-col flex-1">
            {/* Header controls */}
            <div className="flex justify-between items-center mb-6">
              <button
                onClick={() => step > 0 ? setStep(s => s - 1) : onClose()}
                className="flex items-center gap-1 text-[#2D5A27] font-bold text-sm"
              >
                <ChevronLeft size={18} /> Back
              </button>
              <button onClick={onClose} className="p-1 text-[#9CA3AF] hover:text-[#4B5563]">
                <X size={20} />
              </button>
            </div>

            {/* Content titles */}
            <h2 className="text-3xl font-extrabold text-[#1C1C1E] mb-1 tracking-tight">{routine.title}</h2>
            <p className="text-[15px] text-[#6B7280] mb-6 font-medium leading-relaxed">{routine.subtitle}</p>

            {/* Pagination & Timer */}
            <div className="flex justify-between items-center mb-6">
              <span className="text-[11px] font-bold text-[#9CA3AF] uppercase tracking-widest">
                Step {step + 1} of {routine.steps.length}
              </span>
              <div className={`px-3.5 py-1.5 rounded-full text-xs font-bold border transition-all ${timeLeft > 0 ? 'bg-[#ECFDF5] text-[#2D5A27] border-[#A7F3D0]' : 'bg-[#F3F4F6] text-[#9CA3AF] border-[#E5E7EB]'}`}>
                Hold {String(timeLeft).padStart(2, '0')}s
              </div>
            </div>

            {/* Transitioning step card */}
            <div className="flex-1">
              <AnimatePresence mode="wait">
                <motion.div
                  key={step}
                  initial={{ opacity: 0, x: 20 }} 
                  animate={{ opacity: 1, x: 0 }} 
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.25 }}
                  className="bg-white rounded-[32px] p-6 shadow-xl shadow-black/5 border border-[#EEEBE4] flex flex-col w-full h-full min-h-[380px]"
                >
                  <h3 className="text-xl font-extrabold text-[#1C1C1E] mb-4 tracking-tight">{currentData.title}</h3>

                  <div className="w-full h-56 bg-[#FAF8F5] rounded-3xl overflow-hidden mb-6 flex items-center justify-center border border-[#EEEBE4]">
                    <img
                      src={currentData.imagePath}
                      alt={currentData.title}
                      className="w-full h-full object-contain block select-none"
                    />
                  </div>

                  <p className="text-[#4B5563] leading-relaxed text-[15px] font-medium">{currentData.description}</p>
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Action footer */}
            <div className="flex gap-4 mt-8">
              <button
                onClick={() => step > 0 ? setStep(s => s - 1) : onClose()}
                className="flex-1 py-4.5 rounded-2xl font-bold text-[15px] border-2 border-[#2D5A27] text-[#2D5A27] hover:bg-white transition-all active:scale-[0.98]"
              >
                Back
              </button>
              <button
                onClick={() => { if (!isLastStep) setStep(s => s + 1); else { setStep(0); onClose(); } }}
                className="flex-1 py-4.5 rounded-2xl font-bold text-[15px] bg-[#2D5A27] text-white hover:bg-[#1E3F1A] transition-all shadow-lg shadow-[#2D5A27]/20 active:scale-[0.98]"
              >
                {isLastStep ? 'Done' : 'Next'}
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
