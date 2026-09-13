import React, { useState, useEffect, useMemo } from 'react';
import { createRoot } from 'react-dom/client';
import { 
  Menu, Bell, QrCode, UserRound, ChevronRight, CreditCard, Send, 
  Smartphone, ReceiptText, ShoppingCart, Gift, Home, Package, 
  HandCoins, LayoutDashboard, Search, X, Moon, Sun, ShieldAlert, DollarSign, Activity, MessageCircle, Eye
} from 'lucide-react';
import './styles.css';

// --- ESTILOS INYECTADOS CORREGIDOS ---
const extraStyles = `
  /* Modo Oscuro */
  .dark-theme {
    --bg-color: #121212;
    --text-color: #ffffff;
    --card-bg: #1e1e1e;
    --border-color: #333333;
    background-color: var(--bg-color);
    color: var(--text-color);
  }
  .dark-theme .app, 
  .dark-theme .content, 
  .dark-theme .header,
  .dark-theme .welcome {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
  }
  .dark-theme .welcome-title, 
  .dark-theme .welcome-sub {
    color: var(--text-color) !important;
  }
  .dark-theme .single-card, 
  .dark-theme .actions-card, 
  .dark-theme .bottom-nav, 
  .dark-theme .client-card, 
  .dark-theme .modal-content,
  .dark-theme .analytics-card {
    background-color: var(--card-bg);
    color: var(--text-color);
    border-color: var(--border-color);
  }
  .dark-theme .bottom-nav { border-top: 1px solid var(--border-color); }
  .dark-theme input { background: var(--bg-color); color: var(--text-color); border: 1px solid var(--border-color); }
  .dark-theme .modal-header p, .dark-theme .stat-box div, .dark-theme .analytics-subtitle { color: #aaa !important; }

  /* Corrección de iconos en círculos de colores para Modo Oscuro (Forzar iconos a negro) */
  .dark-theme .action-icon {
    filter: none !important;
  }
  .dark-theme .action-icon svg {
    color: #000000 !important;
    stroke: #000000 !important;
  }

  /* Ajuste de Cabecera y Notificaciones */
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
  }
  .header-actions {
    display: flex;
    align-items: center;
    gap: 15px;
  }
  .header-action {
    background: none;
    border: none;
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
    color: inherit;
    font-size: 11px;
  }
  .header-action .bell, .header-action .qr {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .header-action .bell b {
    position: absolute;
    top: -5px;
    right: -8px;
    background: #d32f2f;
    color: #fff;
    font-size: 10px;
    padding: 1px 4px;
    border-radius: 50%;
  }

  /* Tarjeta de Gráfico de Pastel Analítico Corregido */
  .analytics-card {
    background: #fff;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    margin-bottom: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .analytics-title { font-size: 16px; font-weight: bold; margin-bottom: 4px; align-self: flex-start; }
  .analytics-subtitle { font-size: 13px; color: #888; margin-bottom: 15px; align-self: flex-start; }
  
  .pie-chart-container {
    display: flex;
    align-items: center;
    gap: 20px;
    width: 100%;
    justify-content: center;
  }
  .pie-legend {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
  }
  .legend-color {
    width: 12px;
    height: 12px;
    border-radius: 3px;
  }

  /* Lista Moderna de Clientes */
  .search-container { position: relative; margin-bottom: 20px; }
  .search-container input { width: 100%; padding: 12px 15px 12px 40px; border-radius: 12px; border: 1px solid #ddd; font-size: 15px; outline: none; transition: border 0.2s;}
  .search-container input:focus { border-color: #ffd719; }
  .search-container svg { position: absolute; left: 12px; top: 12px; color: #888; }
  .client-list { display: flex; flex-direction: column; gap: 12px; padding-bottom: 90px; }
  .client-card { display: flex; justify-content: space-between; align-items: center; padding: 15px; background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid transparent; transition: border-color 0.2s;}
  .client-card:hover { border-color: #ffd719; }
  
  .risk-badge { padding: 4px 8px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; }
  .risk-high { background: #ffebee; color: #d32f2f; }
  .risk-medium { background: #fff8e1; color: #f57f17; }
  
  /* Botón de Ojito */
  .eye-btn { background: rgba(82, 197, 223, 0.1); color: #52c5df; border: none; padding: 8px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; margin-left: 10px; }
  .eye-btn:hover { background: #52c5df; color: #fff; transform: scale(1.05); }

  /* Botones Flotantes */
  .fab-group { position: fixed; bottom: 85px; right: 15px; display: flex; flex-direction: column; gap: 10px; z-index: 9999; }
  .fab-btn { width: 50px; height: 50px; border-radius: 25px; border: none; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.15); transition: background 0.2s; }
  .fab-qr { background: #ffd719; color: #000; }
  .fab-view { background: #27272a; color: #ffd719; }
  .fab-theme { background: #fff; color: #27272a; border: 1px solid #ddd; }
  .dark-theme .fab-theme { background: #333; color: #ffd719; border: none; }

  /* Modal */
  .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: flex-end; justify-content: center; animation: fadeIn 0.2s ease-out; }
  .modal-content { background: #fff; width: 100%; max-width: 500px; border-radius: 24px 24px 0 0; padding: 25px; position: relative; animation: slideUp 0.3s ease-out; }
  .modal-close { position: absolute; top: 20px; right: 20px; background: none; border: none; cursor: pointer; color: #888; }
  .modal-header { border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 15px; }
  .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
  .stat-box { background: rgba(0,0,0,0.03); padding: 15px; border-radius: 12px; }
  .dark-theme .stat-box { background: rgba(255,255,255,0.05); }
  @keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
`;

const quickActions = [
  ['Transferir dinero', Send, 'pink'],
  ['Recargar celular', Smartphone, 'mint'],
  ['Pagar tarjeta', CreditCard, 'yellow'],
  ['Pagar servicios', ReceiptText, 'gray'],
];
const bottom = [['Inicio', Home], ['Mis Productos', Package], ['Gestiones', HandCoins], ['Para Ti', Gift]];

function UserView() {
  const [active, setActive] = useState('Inicio');
  return (
    <>
      <header className="header">
        <button className="plain icon" aria-label="Menú"><Menu size={30}/></button>
        <div className="header-actions">
          <button className="header-action" aria-label="Mensajería">
            <span className="bell"><Bell size={25}/><b>3</b></span><small>Mensajería</small>
          </button>
          <button className="header-action" aria-label="Mi QR">
            <span className="qr"><QrCode size={23}/></span><small>Mi QR</small>
          </button>
        </div>
      </header>

      <main className="content">
        <section className="welcome">
          <span className="avatar"><UserRound size={26}/></span>
          <div>
            <div className="welcome-title">Bienvenido <ChevronRight size={22}/></div>
            <div className="welcome-sub">Tu banca, simple y segura.</div>
          </div>
        </section>

        <button className="single-card" type="button">
          <CreditCard size={30}/><strong>Mis Tarjetas</strong><ChevronRight className="ml-auto" size={27}/>
        </button>

        <section className="needs section">
          <h2>¿Qué necesitas hacer hoy?</h2>
          <div className="actions-card">
            {quickActions.map(([label, Icon, tone]) => (
              <button key={label} className="action" type="button" aria-label={label}>
                <span className={`action-icon ${tone}`}><Icon size={29}/></span><span>{label}</span>
              </button>
            ))}
          </div>
        </section>

        <button className="single-card promo" type="button">
          <ShoppingCart size={30}/><strong>Promociones y descuentos</strong><ChevronRight className="ml-auto" size={27}/>
        </button>
      </main>

      <nav className="bottom-nav">
        {bottom.map(([label, Icon]) => (
          <button key={label} className={`nav ${active === label ? 'active' : ''}`} onClick={() => setActive(label)} type="button">
            <Icon size={27}/><span>{label}</span>
          </button>
        ))}
      </nav>
    </>
  );
}

function AdminView() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClient, setSelectedClient] = useState(null);
  const [clients, setClients] = useState([]);

  useEffect(() => {
    const fetchClients = async () => {
      try {
        const mockData = [
          { id: 1, nombre: 'Carlos Mendoza', telefono: '+503 7777-1111', riesgo_score: 92, saldo_pendiente: 1450.00, estado_gestion: 'Sin contactar', dias_mora: 45 },
          { id: 2, nombre: 'Ana Gabriela Reyes', telefono: '+503 6655-2222', riesgo_score: 85, saldo_pendiente: 890.50, estado_gestion: 'Conversación IA Activa', dias_mora: 30 },
          { id: 3, nombre: 'Luis Fernando Ortiz', telefono: '+503 7000-3333', riesgo_score: 74, saldo_pendiente: 320.00, estado_gestion: 'Compromiso de Pago', dias_mora: 15 },
          { id: 4, nombre: 'Mónica Castro', telefono: '+503 7888-4444', riesgo_score: 60, saldo_pendiente: 150.00, estado_gestion: 'Sin contactar', dias_mora: 5 },
        ];
        setClients(mockData);
      } catch (error) {
        console.error('Error fetching clients:', error);
      }
    };
    fetchClients();
  }, []);

  const filteredClients = useMemo(() => {
    return clients.filter(c => c.nombre.toLowerCase().includes(searchTerm.toLowerCase()));
  }, [clients, searchTerm]);

  // Cálculos precisos para SVG con viewBox 0 0 100 100 (Círculo real)
  const statsPie = useMemo(() => {
    if (clients.length === 0) return { high: 0, medium: 0, highPercent: 0, mediumPercent: 0 };
    const high = clients.filter(c => c.riesgo_score > 80).length;
    const medium = clients.length - high;
    const highPercent = Math.round((high / clients.length) * 100);
    const mediumPercent = 100 - highPercent;
    
    return { high, medium, highPercent, mediumPercent };
  }, [clients]);

  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const highStroke = (statsPie.highPercent / 100) * circumference;
  const mediumStroke = circumference - highStroke;

  return (
    <>
      <header className="header" style={{ borderBottom: 'none' }}>
        <div className="heading" style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <LayoutDashboard size={28} color="#ffd719" style={{ background: '#27272a', padding: '4px', borderRadius: '6px' }} />
          <h2 style={{ fontSize: '20px', margin: 0, marginLeft: '10px' }}>Gestión de Cartera</h2>
        </div>
      </header>

      <main className="content" style={{ padding: '20px' }}>
        {/* Gráfico Circular Real (SVG Círculo perfecto con viewBox de 100x100) */}
        <div className="analytics-card">
          <div className="analytics-title">Análisis de Cartera por Riesgo</div>
          <div className="analytics-subtitle">Distribución porcentual de clientes</div>
          
          <div className="pie-chart-container">
            <svg width="110" height="110" viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
              {/* Fondo (Riesgo Moderado/Bajo) */}
              <circle 
                cx="50" cy="50" r={radius} 
                fill="transparent" 
                stroke="#f57f17" 
                strokeWidth="16" 
              />
              {/* Segmento de Riesgo Alto */}
              <circle 
                cx="50" cy="50" r={radius} 
                fill="transparent" 
                stroke="#d32f2f" 
                strokeWidth="16" 
                strokeDasharray={`${highStroke} ${circumference}`}
                strokeDashoffset="0"
              />
            </svg>
            <div className="pie-legend">
              <div className="legend-item">
                <span className="legend-color" style={{ background: '#d32f2f' }}></span>
                <span>Riesgo Alto (&gt;80%): <strong>{statsPie.highPercent}%</strong> ({statsPie.high})</span>
              </div>
              <div className="legend-item">
                <span className="legend-color" style={{ background: '#f57f17' }}></span>
                <span>Riesgo Moderado/Bajo: <strong>{statsPie.mediumPercent}%</strong> ({statsPie.medium})</span>
              </div>
            </div>
          </div>
        </div>

        <div className="search-container">
          <Search size={20} />
          <input 
            type="text" 
            placeholder="Buscar por nombre o ID..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="client-list">
          {filteredClients.map(client => (
            <div key={client.id} className="client-card">
              <div>
                <strong style={{ display: 'block', fontSize: '16px', marginBottom: '4px' }}>{client.nombre}</strong>
                <small style={{ color: '#888' }}>{client.estado_gestion}</small>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{ textAlign: 'right' }}>
                  <span className={`risk-badge ${client.riesgo_score > 80 ? 'risk-high' : 'risk-medium'}`}>
                    Riesgo: {client.riesgo_score}%
                  </span>
                  <strong style={{ display: 'block', marginTop: '6px' }}>${client.saldo_pendiente?.toFixed(2)}</strong>
                </div>
                <button 
                  className="eye-btn" 
                  onClick={() => setSelectedClient(client)}
                  aria-label="Ver detalles"
                >
                  <Eye size={20} />
                </button>
              </div>
            </div>
          ))}
          {filteredClients.length === 0 && <p style={{ textAlign: 'center', color: '#888', marginTop: '20px' }}>No se encontraron clientes.</p>}
        </div>
      </main>

      {/* MODAL EMERGENTE */}
      {selectedClient && (
        <div className="modal-overlay" onClick={() => setSelectedClient(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedClient(null)}><X size={24} /></button>
            
            <div className="modal-header">
              <h2 style={{ margin: '0 0 5px 0' }}>{selectedClient?.nombre}</h2>
              <p style={{ margin: 0, color: '#888', display: 'flex', alignItems: 'center', gap: '5px' }}>
                <Smartphone size={16}/> {selectedClient?.telefono}
              </p>
            </div>

            <div className="stat-grid">
              <div className="stat-box">
                <ShieldAlert size={20} color={selectedClient?.riesgo_score > 80 ? '#d32f2f' : '#f57f17'} style={{ marginBottom: '8px' }}/>
                <div style={{ fontSize: '13px', color: '#888' }}>Probabilidad Impago</div>
                <strong style={{ fontSize: '20px' }}>{selectedClient?.riesgo_score}%</strong>
              </div>
              
              <div className="stat-box">
                <DollarSign size={20} color="#52c5df" style={{ marginBottom: '8px' }}/>
                <div style={{ fontSize: '13px', color: '#888' }}>Deuda Total</div>
                <strong style={{ fontSize: '20px' }}>${selectedClient?.saldo_pendiente?.toFixed(2)}</strong>
              </div>

              <div className="stat-box">
                <Activity size={20} color="#9c27b0" style={{ marginBottom: '8px' }}/>
                <div style={{ fontSize: '13px', color: '#888' }}>Días en Mora</div>
                <strong style={{ fontSize: '20px' }}>{selectedClient?.dias_mora} días</strong>
              </div>
              
              <div className="stat-box">
                <MessageCircle size={20} color="#4caf50" style={{ marginBottom: '8px' }}/>
                <div style={{ fontSize: '13px', color: '#888' }}>Estado LLM</div>
                <strong style={{ fontSize: '15px' }}>{selectedClient?.estado_gestion}</strong>
              </div>
            </div>

            <button style={{ width: '100%', padding: '15px', background: '#ffd719', color: '#000', border: 'none', borderRadius: '12px', marginTop: '20px', fontWeight: 'bold', fontSize: '16px', cursor: 'pointer' }}>
              Iniciar Intervención IA
            </button>
          </div>
        </div>
      )}
    </>
  );
}

function App() {
  const [view, setView] = useState('user');
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const styleEl = document.createElement('style');
    styleEl.innerHTML = extraStyles;
    document.head.appendChild(styleEl);
    return () => document.head.removeChild(styleEl);
  }, []);

  return (
    <div className={`app-wrapper ${isDark ? 'dark-theme' : ''}`} style={{ minHeight: '100vh', background: isDark ? '#121212' : '#f8f9fa' }}>
      <div className="app">
        {view === 'user' ? <UserView /> : <AdminView />}

        <div className="fab-group">
          <button className="fab-btn fab-theme" onClick={() => setIsDark(!isDark)} aria-label="Alternar Tema">
            {isDark ? <Sun size={24} /> : <Moon size={24} />}
          </button>
          <button className="fab-btn fab-view" onClick={() => setView(view === 'user' ? 'admin' : 'user')} aria-label="Cambiar Vista">
            {view === 'user' ? <LayoutDashboard size={24} /> : <Smartphone size={24} />}
          </button>
          {view === 'user' && (
            <button className="fab-btn fab-qr" aria-label="Mi QR"><QrCode size={26} /></button>
          )}
        </div>
      </div>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App/></React.StrictMode>);