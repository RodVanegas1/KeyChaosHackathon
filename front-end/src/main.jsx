import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { 
  Menu, Bell, QrCode, UserRound, ChevronRight, CreditCard, Send, 
  Smartphone, ReceiptText, ShoppingCart, Gift, Home, Package, 
  HandCoins, LayoutDashboard, AlertTriangle, TrendingUp, MessageCircle, CheckCircle, Users 
} from 'lucide-react';
import './styles.css';

// --- CONFIGURACIÓN VISTA USUARIO ---
const quickActions = [
  ['Transferir dinero', Send, 'pink'],
  ['Recargar celular', Smartphone, 'mint'],
  ['Pagar tarjeta', CreditCard, 'yellow'],
  ['Pagar servicios', ReceiptText, 'gray'],
];
const bottom = [['Inicio', Home], ['Mis Productos', Package], ['Gestiones', HandCoins], ['Para Ti', Gift]];

// ==========================================
// 1. COMPONENTE: VISTA DEL CLIENTE (Tu código intacto)
// ==========================================
function UserView() {
  const [active, setActive] = useState('Inicio');
  return (
    <div className="app">
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

      <button className="floating-qr" type="button" aria-label="Mi QR"><QrCode size={34}/></button>
      <nav className="bottom-nav">
        {bottom.map(([label, Icon]) => (
          <button key={label} className={`nav ${active === label ? 'active' : ''}`} onClick={() => setActive(label)} type="button">
            <Icon size={27}/><span>{label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}

// ==========================================
// 2. COMPONENTE: VISTA DEL ADMINISTRADOR / BANCO
// ==========================================
function AdminView() {
  // Estado inicial con datos mockeados para que la demo nunca se caiga
  const [metrics, setMetrics] = useState({
    riesgo_alto: 14,
    conversaciones_activas: 5,
    compromisos_obtenidos: 8,
    monto_recuperado: 3450.00
  });

  // Aquí conectarías con tu backend FastAPI
  /*
  useEffect(() => {
    fetch('http://localhost:8000/api/dashboard/metrics')
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(err => console.error("Error al cargar métricas", err));
  }, []);
  */

  return (
    <div className="app" style={{ background: '#f8f9fa' }}>
      <header className="header" style={{ borderBottom: '1px solid #ddd' }}>
        <div className="heading" style={{ width: '100%' }}>
          <TrendingUp size={28} color="#52c5df" />
          <h2 style={{ fontSize: '20px', margin: 0 }}>Panel de Control IA</h2>
        </div>
      </header>

      <main className="content" style={{ paddingBottom: '30px' }}>
        <section className="welcome" style={{ background: 'transparent', paddingBottom: '0' }}>
          <div>
            <div className="welcome-title">Monitoreo de Cobranza Preventiva</div>
            <div className="welcome-sub">Resultados del modelo de riesgo en tiempo real.</div>
          </div>
        </section>

        <section className="section">
          {/* Tarjeta de Riesgo Principal */}
          <div className="account-card" style={{ borderColor: '#fa6267', marginBottom: '15px' }}>
            <div className="account-label">
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <AlertTriangle size={16} /> Clientes en Riesgo Alto
              </span>
            </div>
            <div className="balance">
              <strong>{metrics.riesgo_alto}</strong> <span>detectados hoy</span>
            </div>
          </div>

          {/* Tarjeta de Éxito de Recuperación */}
          <div className="account-card" style={{ borderColor: '#52c5df' }}>
            <div className="account-label">
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle size={16} /> Acuerdos de Pago Generados
              </span>
            </div>
            <div className="balance">
              <strong style={{ color: '#27272a' }}>${metrics.monto_recuperado.toLocaleString()}</strong> 
              <span>({metrics.compromisos_obtenidos} compromisos)</span>
            </div>
          </div>
        </section>

        <section className="needs section">
          <h2>Estado del Agente LLM</h2>
          <div className="actions-card" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
            <div className="action">
              <span className="action-icon mint"><MessageCircle size={29}/></span>
              <span><strong>{metrics.conversaciones_activas}</strong><br/><small>Chats Activos</small></span>
            </div>
            <div className="action">
              <span className="action-icon yellow"><Users size={29}/></span>
              <span><strong>92%</strong><br/><small>Efectividad</small></span>
            </div>
          </div>
        </section>

        {/* Lista rápida de usuarios en gestión (Opcional visual para la demo) */}
        <section className="section">
          <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>Gestiones Recientes</h2>
          <div style={{ background: '#fff', borderRadius: '18px', padding: '15px', boxShadow: '0 2px 4px rgba(0,0,0,.04)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #eee' }}>
              <div><strong>Carlos</strong><br/><small style={{color: '#fa6267'}}>84% Riesgo</small></div>
              <div style={{ textAlign: 'right' }}><strong>$850.00</strong><br/><small style={{color: '#52c5df'}}>Compromiso 17/09</small></div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0' }}>
              <div><strong>María</strong><br/><small style={{color: '#f5a623'}}>71% Riesgo</small></div>
              <div style={{ textAlign: 'right' }}><strong>$320.00</strong><br/><small style={{color: '#777'}}>En conversación...</small></div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

// ==========================================
// 3. CONTROLADOR: BOTÓN FLOTANTE PARA LA DEMO
// ==========================================
function App() {
  const [view, setView] = useState('user'); // 'user' o 'admin'

  return (
    <>
      {/* Botón Switch absoluto para no interferir con el diseño */}
      <button 
        onClick={() => setView(view === 'user' ? 'admin' : 'user')}
        style={{
          position: 'fixed',
          top: '15px',
          right: '50%',
          transform: 'translateX(50%)',
          zIndex: 9999,
          background: '#27272a',
          color: '#ffd719',
          border: '2px solid #ffd719',
          padding: '8px 20px',
          borderRadius: '30px',
          fontWeight: 'bold',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
          cursor: 'pointer'
        }}
      >
        <LayoutDashboard size={18} />
        {view === 'user' ? 'Ir a Dashboard Admin' : 'Ver Vista Cliente'}
      </button>

      {/* Renderizado dinámico */}
      {view === 'user' ? <UserView /> : <AdminView />}
    </>
  );
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App/></React.StrictMode>);