import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Menu, Bell, QrCode, UserRound, ChevronRight, CreditCard, Send, Smartphone, ReceiptText, ShoppingCart, Gift, Home, Package, HandCoins } from 'lucide-react';
import './styles.css';

const quickActions = [
  ['Transferir dinero', Send, 'pink'],
  ['Recargar celular', Smartphone, 'mint'],
  ['Pagar tarjeta', CreditCard, 'yellow'],
  ['Pagar servicios', ReceiptText, 'gray'],
];
const bottom = [['Inicio', Home], ['Mis Productos', Package], ['Gestiones', HandCoins], ['Para Ti', Gift]];

function App(){
  const [active,setActive]=useState('Inicio');
  return <div className="app">
    <header className="header">
      <button className="plain icon" aria-label="Menú"><Menu size={30}/></button>
      <div className="header-actions">
        <button className="header-action" aria-label="Mensajería"><span className="bell"><Bell size={25}/><b>3</b></span><small>Mensajería</small></button>
        <button className="header-action" aria-label="Mi QR"><span className="qr"><QrCode size={23}/></span><small>Mi QR</small></button>
      </div>
    </header>

    <main className="content">
      <section className="welcome">
        <span className="avatar"><UserRound size={26}/></span>
        <div><div className="welcome-title">Bienvenido <ChevronRight size={22}/></div><div className="welcome-sub">Tu banca, simple y segura.</div></div>
      </section>

      <button className="single-card" type="button"><CreditCard size={30}/><strong>Mis Tarjetas</strong><ChevronRight className="ml-auto" size={27}/></button>

      <section className="needs section"><h2>¿Qué necesitas hacer hoy?</h2><div className="actions-card">{quickActions.map(([label,Icon,tone])=><button key={label} className="action" type="button" aria-label={label}><span className={`action-icon ${tone}`}><Icon size={29}/></span><span>{label}</span></button>)}</div></section>

      <button className="single-card promo" type="button"><ShoppingCart size={30}/><strong>Promociones y descuentos</strong><ChevronRight className="ml-auto" size={27}/></button>
    </main>

    <button className="floating-qr" type="button" aria-label="Mi QR"><QrCode size={34}/></button>
    <nav className="bottom-nav">{bottom.map(([label,Icon])=><button key={label} className={`nav ${active===label?'active':''}`} onClick={()=>setActive(label)} type="button"><Icon size={27}/><span>{label}</span></button>)}</nav>
  </div>
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App/></React.StrictMode>);
