"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu } from 'lucide-react';

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  const navItems = [
    { label: "Dashboard", icon: "⊞", href: "/dashboard" },
    { label: "Monitoring", icon: "◉", href: "/monitoring" },
    { label: "Chat", icon: "✧", href: "/chat" },
    { label: "History", icon: "◷", href: "/history" },
    { label: "Settings", icon: "⎈", href: "/settings" }
  ];

  return (
    <aside
      className={`glass fixed left-0 top-0 h-screen transition-all duration-300 ease-in-out flex flex-col items-center py-6 border-y-0 border-l-0 rounded-none z-50`}
      style={{ width: collapsed ? 'var(--sidebar-collapsed)' : 'var(--sidebar-expanded)' }}
    >
      {/* Header / Logo / Hamburger */}
      <div className={`flex w-full mb-8 items-center justify-between px-4 transition-all duration-300 ${collapsed ? 'justify-center px-0 flex-col gap-4' : ''}`}>
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[var(--accent)] text-white flex items-center justify-center font-bold text-lg shrink-0">
              ✦
            </div>
            <div className="animate-in fade-in zoom-in duration-300">
              <h1 className="font-bold text-lg leading-none tracking-tight">PosturePal</h1>
            </div>
          </div>
        )}
        {collapsed && (
           <div className="w-8 h-8 rounded-lg bg-[var(--accent)] text-white flex items-center justify-center font-bold text-lg shrink-0">
             ✦
           </div>
        )}
        <button 
          onClick={() => setCollapsed(!collapsed)}
          className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors focus:outline-none"
        >
          <Menu size={24} strokeWidth={2.5} />
        </button>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 w-full flex flex-col gap-2 px-3">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (pathname === '/' && item.href === '/dashboard');
          return (
            <Link 
              key={item.href} 
              href={item.href}
              title={collapsed ? item.label : ""}
              className={`flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group relative
                ${isActive ? 'bg-[var(--accent)] text-white font-medium shadow-md' : 'text-[var(--text-secondary)] hover:bg-[var(--glass-bg)] hover:text-[var(--text-primary)]'}
                ${collapsed ? 'justify-center px-0' : ''}
              `}
            >
              <span className="text-xl leading-none">{item.icon}</span>
              {!collapsed && (
                <span className="text-sm">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Active Profile */}
      <div className={`w-full mt-auto px-4 transition-all pb-2 ${collapsed ? 'px-0 text-center flex justify-center' : ''}`}>
        {!collapsed ? (
            <div className="pt-4 border-t border-[rgba(0,0,0,0.05)] w-full">
              <p className="text-[10px] text-[var(--text-muted)] font-semibold uppercase tracking-wider mb-1">Active Profile</p>
              <p className="text-sm font-bold truncate">User</p>
            </div>
        ) : (
          <div className="w-8 h-8 rounded-full border border-[var(--glass-border)] flex items-center justify-center text-xs font-bold text-[var(--text-primary)] shrink-0">
            U
          </div>
        )}
      </div>
    </aside>
  );
}
