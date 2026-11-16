import { useState, useEffect } from 'react';
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
  
  // Estado para la consola flotante de comandos
  const [consoleData, setConsoleData] = useState({ isOpen: false, title: '', content: '' });

  useEffect(() => {
    if (!username) return;

    const fetchData = async () => {
      const isOnline = await checkHealth();
      setServerOnline(isOnline);

      const histData = await getHistory();
      if (histData && Array.isArray(histData)) {
        // Ordenamiento estricto por Relojes de Lamport
        const sortedMessages = histData.sort((a, b) => (a.lamport || 0) - (b.lamport || 0));
        setMessages(sortedMessages);
      }

      const userData = await getUsers();
      if (userData) setUsers(userData);
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [username]);

  // Interceptor global de comandos (/history, /users, /ayuda, /help, /salir, /exit)
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
          "/history": "Displays full message history synchronized via Lamport Clocks / Muestra el historial completo sincronizado con Relojes de Lamport.",
          "/users": "Displays active nodes and connected users in the distributed network / Muestra nodos y usuarios activos en la red.",
          "/ayuda | /help": "Displays this interactive help menu / Muestra este menú de ayuda.",
          "/salir | /exit": "Closes current session and returns to login / Cierra la sesión actual y regresa al login."
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

    if (trimmed === '/salir' || trimmed === '/exit') {
      setUsername(null); 
      return true;
    }

    return false; 
  };

  if (!username) {
    return <LoginModal onLogin={setUsername} />;
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090d16] text-slate-100 justify-center items-center p-0 md:p-4">
      {/* Contenedor principal */}
      <div className="flex h-full w-full max-w-7xl md:h-[92vh] bg-slate-900/40 backdrop-blur-2xl md:border md:border-slate-800/80 md:rounded-3xl shadow-2xl overflow-hidden relative">
        
        <Sidebar serverOnline={serverOnline} users={users} />

        <div className="flex-1 flex flex-col h-full bg-slate-950/30 relative">
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

          {/* Consola flotante de comandos */}
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

          {/* Input de mensajes */}
          <MessageInput currentUsername={username} onInterceptSend={handleSendMessageInterceptor} />
        </div>
      </div>
    </div>
  );
}