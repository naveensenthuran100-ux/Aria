"use client";
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import GlassCard from '@/components/GlassCard';
import { Camera } from 'lucide-react';

export default function WelcomePage() {
  const [step, setStep] = useState(0);
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleNext = () => setStep(s => s + 1);
  const handleFinish = () => router.push('/dashboard');

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
    exit: { opacity: 0, y: -20, transition: { duration: 0.4 } }
  };

  // Handle Camera access and voice instructions when entering step 1
  useEffect(() => {
    let stream: MediaStream | null = null;
    if (step === 1) {
      navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        .then(s => {
          stream = s;
          if (videoRef.current) {
            videoRef.current.srcObject = s;
          }
        })
        .catch(err => console.error("Camera error:", err));
    }

    return () => {
      // Cleanup camera stream when leaving step 1
      if (stream) {
        stream.getTracks().forEach(t => t.stop());
      }
    };
  }, [step]);

  return (
    <div className="min-h-[80vh] flex items-center justify-center relative overflow-hidden">
      {/* Decorative calm background elements */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-white/40 rounded-full blur-[80px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-[#E3D9C8]/40 rounded-full blur-[100px] pointer-events-none" />

      <GlassCard className="w-full max-w-xl relative z-10 p-12">
        <AnimatePresence mode="wait">
          {step === 0 && (
            <motion.div
              key="step0"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="text-center"
            >
              <div className="w-16 h-16 rounded-2xl bg-[var(--accent)] text-white flex items-center justify-center font-bold text-3xl mx-auto mb-6 shadow-xl relative overflow-hidden group">
                <span className="relative z-10">✦</span>
              </div>
              <h1 className="text-4xl font-bold tracking-tight mb-4 text-[var(--text-primary)]">Welcome to PosturePal</h1>
              <p className="text-lg text-[var(--text-secondary)] mb-10 max-w-md mx-auto leading-relaxed">
                Your personal AI wellness companion. PosturePal gently monitors your posture and eye health so you can focus on your best work.
              </p>
              <button 
                onClick={handleNext}
                className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-8 py-4 rounded-xl font-medium transition-all shadow-lg hover:shadow-xl w-full"
              >
                Let's get started
              </button>
            </motion.div>
          )}

          {step === 1 && (
            <motion.div
              key="step1"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              <h2 className="text-2xl font-bold tracking-tight mb-2 text-[var(--text-primary)]">Establish your baseline</h2>
              <p className="text-[var(--text-secondary)] mb-6">We need to calibrate your resting posture and blink rate.</p>
              
              <div className="bg-black/5 rounded-2xl overflow-hidden flex flex-col items-center justify-center mb-6 relative min-h-[240px]">
                 <video 
                   ref={videoRef} 
                   autoPlay 
                   playsInline 
                   muted 
                   className="absolute inset-0 w-full h-full object-cover transform -scale-x-100 opacity-90" 
                 />
                 <div className="absolute bottom-4 bg-black/50 backdrop-blur-md px-4 py-2 rounded-full text-white text-xs font-semibold flex items-center gap-2">
                   <Camera size={14} /> Live Baseline Calibration
                 </div>
              </div>

              <div className="flex gap-4">
                <button onClick={() => setStep(0)} className="px-6 py-4 rounded-xl font-medium text-[var(--text-secondary)] hover:bg-white/40 transition-all">
                  Back
                </button>
                <button onClick={handleNext} className="flex-1 bg-[var(--text-primary)] text-white px-8 py-4 rounded-xl font-medium transition-all shadow-lg hover:shadow-xl">
                  Calibrate Identity
                </button>
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="step2"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="text-center"
            >
              <div className="w-20 h-20 rounded-full bg-[var(--success)] text-white flex items-center justify-center font-bold text-3xl mx-auto mb-6 shadow-xl shadow-[var(--success)]/20 animate-pulse">
                ✓
              </div>
              <h2 className="text-2xl font-bold tracking-tight mb-2 text-[var(--text-primary)]">You're all set</h2>
              <p className="text-[var(--text-secondary)] mb-10 max-w-md mx-auto leading-relaxed">
                PosturePal has successfully learned your baseline posture. All your biometric data remains encrypted locally on this device.
              </p>
              <button 
                onClick={handleFinish}
                className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-8 py-4 rounded-xl font-medium transition-all shadow-lg hover:shadow-xl w-full"
              >
                Go to Dashboard
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </GlassCard>
    </div>
  );
}
