import { Users, Wifi, WifiOff, Hash } from 'lucide-react';

export default function Sidebar({ serverOnline, users }) {
  return (
    <aside className="w-72 bg-slate-900/80 backdrop-blur-xl border-r border-slate-800/80 flex flex-col hidden md:flex">
      {/* Cabecera de la barra lateral */}
      <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2 text-indigo-400 font-bold tracking-tight">
          <Hash size={18} />
          <span>Tick-Chat</span>
        </div>
        
        {serverOnline ? (
          <span className="flex items-center text-[11px] font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full gap-1.5 shadow-sm">
            <Wifi size={12} /> Online
          </span>
        ) : (
          <span className="flex items-center text-[11px] font-medium text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2.5 py-1 rounded-full gap-1.5 shadow-sm">
            <WifiOff size={12} /> Offline
          </span>
        )}
      </div>

      {/* Lista de usuarios */}
      <div className="p-4 flex-1 overflow-y-auto space-y-1">
        <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-3 px-2 flex items-center gap-1.5">
          <Users size={13} /> Conectados ({users.length})
        </div>
        
        <div className="space-y-1">
          {users.map((u, idx) => {
            const name = typeof u === 'string' ? u : u.username;
            const initials = name.substring(0, 2).toUpperCase();
            
            return (
              <div key={idx} className="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-slate-800/50 transition-colors group cursor-default">
                <div className="relative">
                  <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300 font-semibold text-xs shadow-sm">
                    {initials}
                  </div>
                  <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-slate-900"></span>
                </div>
                <div className="flex flex-col truncate">
                  <span className="text-sm font-medium text-slate-200 group-hover:text-white transition-colors truncate">{name}</span>
                  <span className="text-[10px] text-slate-400">Nodo Activo</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
}