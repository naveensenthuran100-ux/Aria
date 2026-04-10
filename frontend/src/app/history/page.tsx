"use client";
import React, { useEffect, useState } from 'react';
import GlassCard from '@/components/GlassCard';
import { DownloadCloud, Sparkles } from 'lucide-react';

export default function HistoryPage() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [aiReport, setAiReport] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/api/sessions')
      .then(res => res.json())
      .then(data => setSessions(data))
      .catch(err => console.error(err));
  }, []);

  const handleExportPDF = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch('http://localhost:8000/api/report');
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown server error' }));
        throw new Error(errorData.detail || 'Export failed');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `posture_wellness_report_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setIsGenerating(false);
    } catch (e: any) {
      console.error('PDF Export Error:', e);
      alert(`Failed to export PDF: ${e.message}`);
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-5xl mx-auto printable-area pb-10">
      <div className="flex justify-between items-end pb-4 border-b border-[rgba(0,0,0,0.05)] print:border-b-2 print:border-black">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">Session History</h1>
          <p className="text-[var(--text-secondary)] mt-1 print:hidden">Review your past wellness and posture trends.</p>
        </div>
        <button 
          onClick={handleExportPDF}
          disabled={isGenerating}
          className="print:hidden flex items-center gap-2 px-4 py-2 bg-[var(--text-primary)] text-white font-medium rounded-xl hover:bg-black transition-colors text-sm shadow-sm disabled:opacity-50"
        >
          {isGenerating ? <Sparkles size={14} className="animate-spin" /> : <DownloadCloud size={14} />}
          {isGenerating ? "Analyzing & Generating PDF..." : "Export PDF Summary"}
        </button>
      </div>

      <GlassCard className="print:shadow-none print:border-none print:bg-transparent print:p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-[var(--text-secondary)]">
            <thead className="text-xs text-[var(--text-primary)] uppercase bg-black/5 rounded-t-lg print:border-b-2 print:border-black print:bg-transparent">
              <tr>
                <th className="px-6 py-3 font-semibold rounded-tl-lg">Date</th>
                <th className="px-6 py-3 font-semibold">Duration</th>
                <th className="px-6 py-3 font-semibold">Posture</th>
                <th className="px-6 py-3 font-semibold">Stress</th>
                <th className="px-6 py-3 font-semibold rounded-tr-lg">Emotion</th>
              </tr>
            </thead>
            <tbody>
              {sessions.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-[var(--text-muted)]">
                    No sessions recorded yet. Start monitoring to collect data.
                  </td>
                </tr>
              ) : (
                sessions.map((session, i) => (
                  <tr key={i} className="border-b border-[rgba(0,0,0,0.05)] hover:bg-black/5 transition-colors print:border-black/20">
                    <td className="px-6 py-4 font-medium text-[var(--text-primary)]">
                      {new Date(session.timestamp * 1000).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">{session.duration_mins || 0} min</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-md text-xs font-semibold print:bg-transparent print:px-0 ${session.posture_score > 70 ? 'bg-[var(--success)]/10 text-[var(--success)] print:text-black' : 'bg-[var(--warning)]/10 text-[var(--warning)] print:text-black'}`}>
                        {session.posture_score || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4">{session.stress_index ? session.stress_index.toFixed(1) : 'Low'}</td>
                    <td className="px-6 py-4 capitalize">{session.dominant_emotion || 'Neutral'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  );
}
