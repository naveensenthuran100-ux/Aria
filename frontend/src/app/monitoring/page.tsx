"use client";
import React, { useEffect, useRef, useState } from 'react';
import GlassCard from '@/components/GlassCard';
import { Camera, CameraOff, BrainCircuit, Activity, MessageSquare, Info } from 'lucide-react';

export default function MonitoringPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);         // Offscreen canvas for emitting frames
  const overlayRef = useRef<HTMLCanvasElement>(null);        // Onscreen canvas for drawing skeleton
  const wsRef = useRef<WebSocket | null>(null);

  const [isMonitoring, setIsMonitoring] = useState(false);
  const [metrics, setMetrics] = useState<any>({});
  
  // Chat state
  const [messages, setMessages] = useState<{role: string, text: string}[]>([]);
  const [input, setInput] = useState('');

  // Setup WebCam and WebSocket
  useEffect(() => {
    let stream: MediaStream | null = null;
    
    if (isMonitoring) {
      // 1. Start Camera
      navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        .then(s => {
          stream = s;
          if (videoRef.current) {
            videoRef.current.srcObject = s;
          }
        })
        .catch(err => console.error("Camera error:", err));

      // 2. Start WebSocket
      const ws = new WebSocket('ws://localhost:8000/ws/stream');
      ws.onopen = () => console.log('WS Connected');
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.status === 'ok' && data.metrics) {
          setMetrics((prev: any) => ({...prev, ...data.metrics}));
        }
      };
      wsRef.current = ws;

      // 3. Sender Loop (1 FPS to avoid overloading local CPU)
      const interval = setInterval(() => {
        if (videoRef.current && canvasRef.current && ws.readyState === WebSocket.OPEN) {
          const ctx = canvasRef.current.getContext('2d');
          if (ctx) {
            ctx.drawImage(videoRef.current, 0, 0, 320, 240);
            const dataUrl = canvasRef.current.toDataURL('image/jpeg', 0.5);
            ws.send(dataUrl);
          }
        }
      }, 1000);

      return () => {
        clearInterval(interval);
        ws.close();
        if (stream) {
          stream.getTracks().forEach(t => t.stop());
        }
      };
    }
  }, [isMonitoring]);

  // Draw Skeleton Overlay
  useEffect(() => {
    if (overlayRef.current && metrics.keypoints) {
      const cvs = overlayRef.current;
      const ctx = cvs.getContext('2d');
      if (!ctx) return;
      
      // Match canvas size to video layout
      cvs.width = cvs.offsetWidth;
      cvs.height = cvs.offsetHeight;
      
      ctx.clearRect(0, 0, cvs.width, cvs.height);
      
      metrics.keypoints.forEach((kp: any) => {
        const conf = kp[2];
        if (conf > 0.5) {
          // Normalize YOLO pixel coordinates based on sent frame size (320x240)
          const normX = kp[0] / 320.0;
          const normY = kp[1] / 240.0;

          // Flip X because video is mirrored on frontend
          const x = (1.0 - normX) * cvs.width;
          const y = normY * cvs.height;
          
          ctx.beginPath();
          ctx.arc(x, y, 4, 0, 2 * Math.PI);
          ctx.fillStyle = 'var(--accent)';
          ctx.fill();
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      });
    }
  }, [metrics.keypoints]);

  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    setMessages(prev => [...prev, {role: 'user', text: input}]);
    const currentInput = input;
    setInput('');
    
    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({text: currentInput})
      });
      const data = await res.json();
      setMessages(prev => [...prev, {role: 'aria', text: data.reply}]);
    } catch (e) {
      setMessages(prev => [...prev, {role: 'aria', text: "I'm having trouble connecting to my logic center."}]);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 min-h-full flex flex-col">
      <div className="flex justify-between items-end pb-4 border-b border-[rgba(0,0,0,0.05)]">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">Live Monitoring</h1>
          <p className="text-[var(--text-secondary)] mt-1">Real-time biometric ML tracking & AI Chat.</p>
        </div>
        <button 
          onClick={() => setIsMonitoring(!isMonitoring)}
          className={`px-6 py-2 rounded-xl font-medium transition-all shadow-md flex items-center gap-2 ${isMonitoring ? 'bg-[var(--danger)] text-white hover:bg-red-800' : 'bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)]'}`}
        >
          {isMonitoring ? <><CameraOff size={18}/> Stop Session</> : <><Camera size={18}/> Start Session</>}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
        {/* Left Column: Camera feed + Metrics */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <GlassCard className="relative flex flex-col items-center justify-center min-h-[360px] bg-black/5 p-0 overflow-hidden">
            {!isMonitoring ? (
               <div className="flex flex-col items-center justify-center text-[var(--text-muted)] gap-4 p-8">
                 <CameraOff size={48} opacity={0.5} />
                 <p className="font-medium">Camera is inactive</p>
               </div>
            ) : (
               <div className="w-full h-full relative flex items-center justify-center">
                 <video 
                   ref={videoRef} 
                   autoPlay 
                   playsInline 
                   muted 
                   className="w-full h-full object-cover transform -scale-x-100" 
                 />
                 <canvas ref={canvasRef} width={320} height={240} className="hidden" />
                 
                 {/* Skeletal Overlay Canvas */}
                 <canvas ref={overlayRef} className="absolute top-0 left-0 w-full h-full pointer-events-none" />
                 
                 {/* Live ML Badges Overlay */}
                 <div className="absolute top-4 left-4 flex flex-col gap-2">
                   <div className="glass px-3 py-1.5 rounded-lg flex items-center gap-2 text-xs font-semibold backdrop-blur-md">
                     <BrainCircuit size={14} className="text-[var(--accent)]" />
                     {metrics.emotion || 'Analyzing...'}
                   </div>
                 </div>
               </div>
            )}
          </GlassCard>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
             <GlassCard className="p-4 text-center group relative">
               <div className="flex justify-center items-center gap-1 mb-1 relative">
                 <div className="text-[10px] uppercase tracking-wider font-bold text-[var(--text-secondary)]">Posture</div>
                 <div className="absolute -top-1 -right-1 text-[var(--text-muted)] group-hover:text-[var(--text-primary)] cursor-help z-10"><Info size={12}/></div>
                 <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1 w-36 p-2 rounded-lg text-[10px] leading-snug glass opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20 text-[var(--text-primary)]">Combined torso & shoulder alignment.</div>
               </div>
               <div className="text-2xl font-bold text-[var(--text-primary)] relative z-0">{metrics.posture || '--'}</div>
             </GlassCard>
             <GlassCard className="p-4 text-center group relative">
               <div className="flex justify-center items-center gap-1 mb-1 relative">
                 <div className="text-[10px] uppercase tracking-wider font-bold text-[var(--text-secondary)]">Alignment</div>
                 <div className="absolute -top-1 -right-1 text-[var(--text-muted)] group-hover:text-[var(--text-primary)] cursor-help z-10"><Info size={12}/></div>
                 <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1 w-36 p-2 rounded-lg text-[10px] leading-snug glass opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20 text-[var(--text-primary)]">Current categorization of pose (good vs bad).</div>
               </div>
               <div className="text-sm font-bold text-[var(--text-primary)] mt-2 relative z-0">{metrics.posture_cat || '--'}</div>
             </GlassCard>
             <GlassCard className="p-4 text-center group relative">
               <div className="flex justify-center items-center gap-1 mb-1 relative">
                 <div className="text-[10px] uppercase tracking-wider font-bold text-[var(--text-secondary)]">Blinks/min</div>
                 <div className="absolute -top-1 -right-1 text-[var(--text-muted)] group-hover:text-[var(--text-primary)] cursor-help z-10"><Info size={12}/></div>
                 <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1 w-36 p-2 rounded-lg text-[10px] leading-snug glass opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20 text-[var(--text-primary)]">Live eye movement tracking for strain.</div>
               </div>
               <div className="text-2xl font-bold text-[var(--text-primary)] relative z-0">{metrics.blink_rate ? metrics.blink_rate.toFixed(1) : '--'}</div>
             </GlassCard>
             <GlassCard className="p-4 text-center group relative">
               <div className="flex justify-center items-center gap-1 mb-1 relative">
                 <div className="text-[10px] uppercase tracking-wider font-bold text-[var(--text-secondary)]">Emotion</div>
                 <div className="absolute -top-1 -right-1 text-[var(--text-muted)] group-hover:text-[var(--text-primary)] cursor-help z-10"><Info size={12}/></div>
                 <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1 w-36 p-2 rounded-lg text-[10px] leading-snug glass opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20 text-[var(--text-primary)]">Real-time facial expression classifier.</div>
               </div>
               <div className="text-sm font-bold text-[var(--text-primary)] mt-2 capitalize relative z-0">{metrics.emotion || '--'}</div>
             </GlassCard>
          </div>

        </div>

        {/* Right Column: AI Chat */}
        <div className="flex flex-col h-[500px]">
          <GlassCard className="flex flex-col h-full !p-0 overflow-hidden">
            <div className="p-4 border-b border-[rgba(0,0,0,0.05)] flex items-center gap-2 bg-white/40">
              <MessageSquare size={18} className="text-[var(--accent)]" />
              <h2 className="font-bold text-[var(--text-primary)]">Chat with Aria</h2>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-[var(--text-muted)] p-6">
                  <Activity size={32} className="mb-2 opacity-50" />
                  <p className="text-sm">Aria is monitoring your session. Ask her how you're doing!</p>
                </div>
              ) : (
                messages.map((m, i) => (
                  <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`p-3 rounded-2xl max-w-[85%] text-sm ${m.role === 'user' ? 'bg-[var(--accent)] text-white rounded-br-none' : 'bg-white border border-[rgba(0,0,0,0.05)] text-[var(--text-primary)] rounded-bl-none shadow-sm'}`}>
                      {m.text}
                    </div>
                  </div>
                ))
              )}
            </div>

            <form onSubmit={handleSendChat} className="p-3 border-t border-[rgba(0,0,0,0.05)] bg-white/40">
              <input 
                type="text" 
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="Ask about your posture..."
                className="w-full bg-white border border-[rgba(0,0,0,0.1)] rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
              />
            </form>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
