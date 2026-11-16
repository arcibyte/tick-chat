import { useState } from 'react';
import { registerUser } from '../services/api';
import { MessageSquareCode, ArrowRight } from 'lucide-react';

export default function LoginModal({ onLogin }) {
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim()) return;
    
    setLoading(true);
    const cleanUsername = username.trim().split('@')[0];
    
    await registerUser(cleanUsername);
    onLogin(cleanUsername);
    setLoading(false);
  };

  return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-950 via-[#0b0f19] to-slate-900 text-white p-4">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b15_1px,transparent_1px),linear-gradient(to_bottom,#1e293b15_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none" />

      <form onSubmit={handleSubmit} className="relative bg-slate-900/80 backdrop-blur-xl p-8 rounded-2xl shadow-2xl w-full max-w-md border border-slate-800/80">
        <div className="flex justify-center mb-4">
          <div className="p-3 bg-indigo-600/10 border border-indigo-500/20 rounded-2xl text-indigo-400 shadow-inner">
            <MessageSquareCode size={32} />
          </div>
        </div>

        <h2 className="text-2xl font-bold text-center text-slate-100 tracking-tight">Tick-Chat Web</h2>
        <p className="text-xs text-slate-400 text-center mt-1 mb-6 uppercase tracking-wider font-medium">Sistema Distribuido • Nodo G1</p>
        
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Nombre de usuario</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="ej. jhon"
              className="w-full px-4 py-3 rounded-xl bg-slate-950/60 border border-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-white placeholder-slate-600 transition-all text-sm"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 active:scale-[0.99] text-white p-3.5 rounded-xl font-medium transition-all duration-200 shadow-lg shadow-indigo-600/25 flex items-center justify-center gap-2 group disabled:opacity-50"
          >
            {loading ? 'Conectando...' : <>Entrar al chat <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" /></>}
          </button>
        </div>
      </form>
    </div>
  );
}