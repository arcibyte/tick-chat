import { useState, useEffect, useRef } from 'react';
import LoginModal from './components/LoginModal';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import { checkHealth, getUsers, getHistory } from './services/api';
import { Terminal, X } from 'lucide-react';

export default function App() {
  const [username, setUsername] = useState(null);
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [serverOnline, setServerOnline] = useState(true);
  
  const [consoleData, setConsoleData] = useState({ isOpen: false, title: '', content: '' });
  const clearLimitRef = useRef(0);

  // Normalizamos el usuario al hacer login para que SIEMPRE sea "nombre@g1"
  const handleLogin = (rawUser) => {
    const clean = rawUser.trim();
    const formatted = clean.includes('@') ? clean : `${clean}@g1`;
    setUsername(formatted);
  };

  useEffect(() => {
    if (!username) {
      clearLimitRef.current = 0;
      return;
    }

    const savedLimit = localStorage.getItem(`tick_chat_clear_limit_${username}`);
    clearLimitRef.current = savedLimit ? parseInt(savedLimit, 10) : 0;

    const fetchData = async () => {
      const isOnline = await checkHealth();
      setServerOnline(isOnline);

      const histData = await getHistory();
      if (histData && Array.isArray(histData)) {
        const sortedMessages = histData.sort((a, b) => (a.lamport || 0) - (b.lamport || 0));
        
        const filteredMessages = clearLimitRef.current > 0
          ? sortedMessages.filter(msg => (msg.lamport || 0) > clearLimitRef.current)
          : sortedMessages;

        setMessages(filteredMessages);
      }

      const userData = await getUsers();
      if (userData) setUsers(userData);
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [username]);

  const handleSendMessageInterceptor = async (text) => {
    const trimmed = text.trim().toLowerCase();

    if (trimmed === '/history') {
      const histData = await getHistory();
      setConsoleData({
        isOpen: true,
        title: 'Terminal Node - Distributed History (Lamport Clocks)',
        content: JSON.stringify(histData, null, 2),
      });
      return true;
    }

    if (trimmed === '/users') {
      const userData = await getUsers();
      setConsoleData({
        isOpen: true,
        title: 'Terminal Node - Active Nodes / Users',
        content: JSON.stringify(userData, null, 2),
      });
      return true;
    }

    if (trimmed === '/ayuda' || trimmed === '/help') {
      const helpText = {
        available_commands: {
          "/history": "Displays full message history synchronized via Lamport Clocks.",
          "/users": "Displays active nodes and connected users.",
          "/clear | /limpiar": "Clears the local chat view permanently until a new message arrives.",
          "/ayuda | /help": "Displays this interactive help menu.",
          "/salir | /exit": "Closes current session and returns to login."
        },
        architecture: "Tick-Chat - FastAPI & React Distributed Chat System"
      };
      setConsoleData({
        isOpen: true,
        title: 'Terminal Node - System Help / Ayuda',
        content: JSON.stringify(helpText, null, 2),
      });
      return true;
    }

    if (trimmed === '/clear' || trimmed === '/limpiar') {
      const histData = await getHistory();
      const maxLamport = histData && Array.isArray(histData)
        ? histData.reduce((max, m) => Math.max(max, m.lamport || 0), 0)
        : 0;

      clearLimitRef.current = maxLamport;
      localStorage.setItem(`tick_chat_clear_limit_${username}`, maxLamport);
      
      setMessages([]);
      return true;
    }

    if (trimmed === '/salir' || trimmed === '/exit') {
      setUsername(null); 
      return true;
    }

    return false; 
  };

  if (!username) {
    return <LoginModal onLogin={handleLogin} />;
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090d16] text-slate-100 justify-center items-center p-0 md:p-4">
      <div className="flex h-full w-full max-w-7xl md:h-[92vh] bg-slate-900/40 backdrop-blur-2xl md:border md:border-slate-800/80 md:rounded-3xl shadow-2xl overflow-hidden relative">
        
        <Sidebar serverOnline={serverOnline} users={users} />

        <div className="flex-1 flex flex-col h-full bg-slate-950/30 relative">
          <header className="px-6 py-4 bg-slate-900/60 backdrop-blur-md border-b border-slate-800/80 flex items-center justify-between z-10 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse shadow-lg shadow-emerald-500/50" />
              <div>
                <h1 className="text-sm font-bold tracking-wide text-slate-200">#general</h1>
                <p className="text-[11px] text-slate-400">Sala Global Distribuida</p>
              </div>
            </div>
            
            {/* Ya no duplicamos @g1 porque username ya está normalizado */}
            <div className="flex items-center gap-2 bg-slate-950/60 border border-slate-800/80 px-3.5 py-1.5 rounded-full text-xs font-medium text-indigo-300 shadow-inner">
              <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
              {username}
            </div>
          </header>

          <ChatWindow messages={messages} currentUsername={username} />

          {consoleData.isOpen && (
            <div className="absolute bottom-20 left-6 right-6 bg-slate-950/95 border border-indigo-500/40 rounded-2xl shadow-2xl p-4 z-50 backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
                <div className="flex items-center gap-2 text-indigo-400 text-xs font-mono font-bold">
                  <Terminal size={16} /> {consoleData.title}
                </div>
                <button
                  onClick={() => setConsoleData({ ...consoleData, isOpen: false })}
                  className="text-slate-400 hover:text-white transition-colors p-1"
                >
                  <X size={16} />
                </button>
              </div>
              <pre className="text-xs font-mono text-slate-300 overflow-x-auto max-h-60 p-2 bg-slate-900/80 rounded-xl border border-slate-800/60 scrollbar-thin">
                {consoleData.content}
              </pre>
            </div>
          )}

          <MessageInput currentUsername={username} onInterceptSend={handleSendMessageInterceptor} />
        </div>
      </div>
    </div>
  );
}