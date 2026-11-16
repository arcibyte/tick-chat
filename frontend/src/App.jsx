import { useState, useEffect } from 'react';
import LoginModal from './components/LoginModal';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import { checkHealth, getUsers, getHistory } from './services/api';

export default function App() {
  const [username, setUsername] = useState(null);
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [serverOnline, setServerOnline] = useState(true);

  useEffect(() => {
    if (!username) return;

    const fetchData = async () => {
      const isOnline = await checkHealth();
      setServerOnline(isOnline);

      const histData = await getHistory();
      if (histData) setMessages(histData);

      const userData = await getUsers();
      if (userData) setUsers(userData);
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [username]);

  if (!username) {
    return <LoginModal onLogin={setUsername} />;
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090d16] text-slate-100 justify-center items-center p-0 md:p-4">
      {/* Contenedor principal con efecto glassmorphism centrado */}
      <div className="flex h-full w-full max-w-7xl md:h-[92vh] bg-slate-900/40 backdrop-blur-2xl md:border md:border-slate-800/80 md:rounded-3xl shadow-2xl overflow-hidden">
        
        {/* Barra lateral */}
        <Sidebar serverOnline={serverOnline} users={users} />

        {/* Panel del Chat */}
        <div className="flex-1 flex flex-col h-full bg-slate-950/30">
          {/* Cabecera del chat */}
          <header className="px-6 py-4 bg-slate-900/60 backdrop-blur-md border-b border-slate-800/80 flex items-center justify-between z-10 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse shadow-lg shadow-emerald-500/50" />
              <div>
                <h1 className="text-sm font-bold tracking-wide text-slate-200">#general</h1>
                <p className="text-[11px] text-slate-400">Sala Global Distribuida</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2 bg-slate-950/60 border border-slate-800/80 px-3.5 py-1.5 rounded-full text-xs font-medium text-indigo-300 shadow-inner">
              <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
              {username}@g1
            </div>
          </header>

          {/* Ventana de mensajes */}
          <ChatWindow messages={messages} currentUsername={username} />

          {/* Input de mensajes */}
          <MessageInput currentUsername={username} />
        </div>
      </div>
    </div>
  );
}