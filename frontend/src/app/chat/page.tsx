"use client";
import React, { useState } from 'react';
import GlassCard from '@/components/GlassCard';
import { MessageSquare, Activity } from 'lucide-react';

export default function ChatPage() {
  const [messages, setMessages] = useState<{role: string, text: string}[]>([]);
  const [input, setInput] = useState('');

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
    <div className="h-[85vh] animate-in fade-in slide-in-from-bottom-4 duration-500 flex flex-col">
      <div className="flex justify-between items-end pb-4 border-b border-[rgba(0,0,0,0.05)] mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">Aria Chat</h1>
          <p className="text-[var(--text-secondary)] mt-1">Talk to your personal wellness companion.</p>
        </div>
      </div>

      <GlassCard className="flex-1 flex flex-col overflow-hidden !p-0">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center text-[var(--text-muted)] p-6">
              <Activity size={48} className="mb-4 opacity-30 text-[var(--accent)]" />
              <h2 className="text-xl font-bold mb-2 text-[var(--text-primary)]">How are you feeling?</h2>
              <p className="max-w-md">I can give you stretching advice, read your current posture data, or just talk to you about ergonomic wellness.</p>
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`p-4 rounded-2xl max-w-[70%] text-sm leading-relaxed ${m.role === 'user' ? 'bg-[var(--accent)] text-white rounded-br-none shadow-md' : 'bg-white border border-[rgba(0,0,0,0.05)] text-[var(--text-primary)] rounded-bl-none shadow-md'}`}>
                  {m.text}
                </div>
              </div>
            ))
          )}
        </div>

        <form onSubmit={handleSendChat} className="p-4 border-t border-[rgba(0,0,0,0.05)] bg-white/40 glass">
          <input 
            type="text" 
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask Aria about your posture..."
            className="w-full bg-white/80 border border-[rgba(0,0,0,0.1)] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)] shadow-sm"
          />
        </form>
      </GlassCard>
    </div>
  );
}
