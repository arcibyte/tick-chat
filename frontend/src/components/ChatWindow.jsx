import { useEffect, useRef } from 'react';

export default function ChatWindow({ messages, currentUsername }) {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 p-6 overflow-y-auto space-y-6">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center text-slate-500">
          <p className="text-sm font-medium">No hay mensajes todavía en esta sala.</p>
          <p className="text-xs text-slate-600 mt-1">¡Sé el primero en escribir algo!</p>
        </div>
      ) : (
        messages.map((msg, idx) => {
          const sender = msg.from_user || msg.from || 'anónimo';
          const isMe = sender.startsWith(currentUsername);

          return (
            <div key={idx} className={`flex flex-col ${isMe ? 'items-end' : 'items-start'} group`}>
              <div className="flex items-center gap-2 mb-1 px-1">
                <span className="text-xs font-semibold text-slate-400">{sender}</span>
                <span className="text-[10px] bg-slate-800 text-indigo-300 px-2 py-0.5 rounded-md border border-slate-700/60 font-mono">
                  Lamport [L{msg.lamport ?? 0}]
                </span>
              </div>
              <div
                className={`p-3.5 rounded-2xl max-w-lg text-sm shadow-md leading-relaxed ${
                  isMe
                    ? 'bg-indigo-600 text-white rounded-tr-sm shadow-indigo-600/10'
                    : 'bg-slate-900 text-slate-200 border border-slate-800 rounded-tl-sm'
                }`}
              >
                {msg.body}
              </div>
            </div>
          );
        })
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}