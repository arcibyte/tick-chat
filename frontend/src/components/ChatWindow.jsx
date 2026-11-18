import { useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';

export default function ChatWindow({ messages, currentUsername }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const myGroup = currentUsername?.includes('@')
    ? currentUsername.split('@')[1]
    : 'g1';

  const normalizedCurrent = currentUsername?.includes('@')
    ? currentUsername
    : `${currentUsername}@${myGroup}`;

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin scrollbar-thumb-slate-800">
      {messages.length === 0 ? (
        <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs font-mono gap-2">
          <Terminal size={24} className="opacity-40 text-indigo-400" />
          <p>No hay mensajes en la sala. El canal está limpio.</p>
        </div>
      ) : (
        messages.map((msg, index) => {
          const rawSender = msg.from || msg.from_user || msg.sender || 'Desconocido';
          const parts = rawSender.split('@');
          const name = parts[0];
          const group = msg.origin || parts[1] || 'g1';

          // colores para usuarios de otros grupos, requisito 10
          const isExternal = group !== myGroup;
          const isMe = rawSender === normalizedCurrent || rawSender === currentUsername;

          const content = msg.body || msg.text || msg.content || '';

          return (
            <div
              key={msg.id || index}
              className={`flex flex-col ${isMe ? 'items-end' : 'items-start'} space-y-1`}
            >
              <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400 px-1">
                <span className={`font-bold ${isExternal ? 'text-amber-400' : 'text-slate-300'}`}>
                  {name}
                </span>

                <span
                  className={`px-1.5 py-0.5 rounded text-[9px] uppercase font-semibold ${
                    isExternal
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                  }`}
                >
                  @{group}
                </span>

                {msg.lamport !== undefined && (
                  <span className="bg-slate-900 border border-slate-800 text-slate-500 px-1.5 py-0.5 rounded text-[10px]">
                    Lamport [L{msg.lamport}]
                  </span>
                )}
              </div>

              <div
                className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed shadow-md ${
                  isMe
                    ? 'bg-indigo-600 text-white rounded-br-xs'
                    : isExternal
                    ? 'bg-amber-950/40 border border-amber-500/40 text-amber-100 rounded-bl-xs'
                    : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-xs'
                }`}
              >
                {content}
              </div>
            </div>
          );
        })
      )}
      <div ref={scrollRef} />
    </div>
  );
}