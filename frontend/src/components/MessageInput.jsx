import { useState } from 'react';
import { Send } from 'lucide-react';
import { postMessage } from '../services/api';

export default function MessageInput({ currentUsername }) {
  const [text, setText] = useState('');

  const handleSend = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;

    const success = await postMessage(`${currentUsername}@g1`, text.trim());
    if (success) {
      setText('');
    }
  };

  return (
    <form onSubmit={handleSend} className="p-4 bg-slate-900/60 backdrop-blur-md border-t border-slate-800/80 flex gap-3 items-center">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Escribe un mensaje a #general..."
        className="flex-1 px-4 py-3 rounded-xl bg-slate-950/80 border border-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-white placeholder-slate-500 text-sm transition-all shadow-inner"
      />
      <button
        type="submit"
        className="bg-indigo-600 hover:bg-indigo-500 active:scale-95 px-5 py-3 rounded-xl text-white flex items-center justify-center transition-all duration-200 shadow-lg shadow-indigo-600/25 group cursor-pointer"
      >
        <Send size={18} className="group-hover:translate-x-0.5 transition-transform" />
      </button>
    </form>
  );
}