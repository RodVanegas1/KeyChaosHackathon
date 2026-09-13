import React, {useEffect, useMemo, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './styles.css';
import {MASTER_PROMPT} from './prompt.js';

const OLLAMA_BASE = import.meta.env.VITE_OLLAMA_URL || 'http://127.0.0.1:11434';
const MODEL = import.meta.env.VITE_OLLAMA_MODEL || 'llama3.2:3b';
const BACKEND = import.meta.env.VITE_BACKEND_URL || '';

const clean = s => String(s||'').replace(/\s+/g,' ').trim();
const cap = s => s ? s.charAt(0).toUpperCase()+s.slice(1) : s;

const VALID_NAMES = [
  'Ana Beatriz Hernández',
  'Douglas Alexander Portillo',
  'Marta Elena Cortez',
  'Jorge Iván Meléndez',
  'Katherine Sofia Aguilar',
  'Óscar Renato Villalta'
];

const normalizeName = s => String(s || '')
  .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  .toLowerCase().replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim();

function matchedDatabaseName(text){
  const n = normalizeName(text);
  return VALID_NAMES.find(name => {
    const nn = normalizeName(name);
    return n.includes(nn) || nn.split(' ').every(part => n.includes(part));
  }) || null;
}

function preferredVoice(){
  const voices = window.speechSynthesis?.getVoices?.() || [];
  const es = voices.filter(v=>/^es(?:-|_)/i.test(v.lang));
  if(!es.length) return null;

  // Prioriza voces neuronales/online disponibles en Windows/Edge/Chrome.
  const neural = /microsoft.*(?:natural|online)|google.*(?:espa[nñ]ol|spanish).*?(?:natural|online)|natural|neural/i;
  const female = /helena|luc[ií]a|sofia|sabina|zira|monica|paulina|fernanda|paloma|dalia|elena|laura|maria|carmen|isabel|teresa|ximena|valeria|camila|daniela|marisol/i;

  return es.find(v=>neural.test(v.name) && female.test(v.name))
      || es.find(v=>neural.test(v.name))
      || es.find(v=>female.test(v.name))
      || es[0]
      || null;
}

function speak(text, onEnd){
  // Voz más estable: usa una voz explícita y divide solo respuestas largas en bloques naturales.
  const phrase = clean(text)
    .replace(/\s*([,:;])\s*/g,'$1 ')
    .replace(/\.{2,}/g,'.')
    .trim();
  if(!phrase) { onEnd?.(); return; }

  const synth = window.speechSynthesis;
  if(!synth) { onEnd?.(); return; }
  synth.cancel();

  const chunks = [];
  const sentences = phrase.match(/[^.!?¿¡]+[.!?]+|[^.!?¿¡]+$/g) || [phrase];
  let buffer='';
  for(const sentence of sentences){
    const part=clean(sentence);
    if(!part) continue;
    if((buffer+' '+part).trim().length<=150){
      buffer=(buffer+' '+part).trim();
    }else{
      if(buffer) chunks.push(buffer);
      buffer=part;
    }
  }
  if(buffer) chunks.push(buffer);

  let index=0;
  let ended=false;
  let watchdog=null;
  const finish=()=>{
    if(ended) return;
    ended=true;
    clearTimeout(watchdog);
    onEnd?.();
  };
  const speakNext=()=>{
    if(index>=chunks.length){ finish(); return; }
    const u=new SpeechSynthesisUtterance(chunks[index++]);
    u.lang='es-SV';
    u.rate=1.01;
    u.pitch=1.0;
    u.volume=1;
    const voice=preferredVoice();
    if(voice) u.voice=voice;
    let localDone=false;
    const next=()=>{
      if(localDone) return;
      localDone=true;
      clearTimeout(watchdog);
      setTimeout(speakNext,35);
    };
    u.onend=next;
    u.onerror=(e)=>{
      if(e?.error==='canceled' || e?.error==='interrupted'){ next(); return; }
      next();
    };
    u.onpause=()=>{
      clearTimeout(watchdog);
      watchdog=setTimeout(()=>{ try{ synth.resume(); }catch{} },220);
    };
    u.onresume=()=>clearTimeout(watchdog);
    synth.speak(u);
  };
  speakNext();
}

async function askOllama(messages){
  const r=await fetch(`${OLLAMA_BASE}/api/chat`,{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({model:MODEL,stream:false,options:{temperature:.10,num_predict:96,top_p:.85,repeat_penalty:1.05},messages})
  });
  if(!r.ok) throw new Error('Ollama no disponible');
  const j=await r.json();
  return clean(j?.message?.content);
}

function classifyIntent(text){
  const t=text.toLowerCase();
  if(/no puedo|no me alcanza|sin dinero|desemple|complicad|dif[ií]cil/.test(t)) return 'NO_PUEDE_PAGAR';
  if(/puedo pagar|sí puedo|si puedo|voy a pagar|haré el pago|hare el pago/.test(t)) return 'PUEDE_PAGAR';
  if(/viernes|lunes|martes|miércoles|miercoles|jueves|sábado|sabado|domingo|mañana|manana|hoy/.test(t)) return 'FECHA_PROPUESTA';
  return 'EN_CONVERSACIÓN';
}
function extractDate(text){
  const m=String(text).match(/\b(hoy|mañana|manana|lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b/i);
  return m?cap(m[1].replace('manana','mañana')):'No detectada';
}
function extractAmount(text){
  const m=String(text).match(/\$\s?(\d+(?:[.,]\d{1,2})?)/);
  return m ? `$${m[1].replace(',', '.')}` : 'No mencionado';
}
function detectReason(text){
  const t=text.toLowerCase();
  if(/desemple|despid|sin trabajo/.test(t)) return 'Situación laboral';
  if(/gasto|emergenc|accidente|choque|enferm|médic|medic/.test(t)) return 'Imprevisto o gasto extraordinario';
  if(/poco ingreso|ingreso|salario|dinero|me alcanza/.test(t)) return 'Dificultad de liquidez';
  return 'No definido';
}

function makeAnalytics(messages, meta){
  const users=messages.filter(m=>m.role==='user').map(m=>m.content);
  const all=users.join(' ');
  const last=users[users.length-1]||'';
  let intent='EN_CONVERSACIÓN';
  if(users.some(t=>/asesor|asesora|humano|persona real|transfer/i.test(t))) intent='TRANSFERENCIA_ASESOR';
  else if(users.some(t=>/no puedo|sin dinero|no me alcanza|desemple|complicad|dif[ií]cil/i.test(t))) intent='NO_PUEDE_PAGAR';
  else if(users.some(t=>/puedo pagar|sí puedo|si puedo|voy a pagar|haré el pago|hare el pago/i.test(t))) intent='PUEDE_PAGAR';
  const paymentIntent = /viernes|lunes|martes|miércoles|miercoles|jueves|sábado|sabado|domingo|mañana|manana|hoy|pagaré|pagare|puedo pagar|voy a pagar/i.test(all) ? 'Presente' : 'No definido';
  let sentiment='Neutral';
  if(/gracias|tranquil|bien|perfecto|sí|si /i.test(all) && !/no puedo|dif[ií]cil|complicad/i.test(all)) sentiment='Positivo';
  if(/preocup|molest|enoj|dif[ií]cil|complicad|estres/i.test(all)) sentiment='Tenso / preocupado';
  return {
    verified: meta.verified ? 'Sí':'Pendiente',
    intent,
    reason: detectReason(all),
    sentiment,
    paymentIntent,
    proposedDate: extractDate(all),
    amount: extractAmount(all),
    incentive: /puntos|beneficio|premio|incentivo|recompensa/i.test(all) ? 'Mencionado en conversación':'No mencionado',
    obstacle: last && intent==='NO_PUEDE_PAGAR' ? last : 'No definido',
    result: intent==='TRANSFERENCIA_ASESOR'?'Transferir a asesor':intent==='PUEDE_PAGAR'?'Avance hacia pago':'Seguimiento',
    nextAction: intent==='TRANSFERENCIA_ASESOR'?'Comunicar con asesor':intent==='PUEDE_PAGAR'?'Validar y registrar según backend':'Continuar gestión',
  };
}

async function enrichAnalytics(base, messages){
  // Enriquecimiento opcional; no envía ni usa datos bancarios privados.
  const compact=messages.slice(-8).map(m=>({role:m.role,content:m.content}));
  try{
    const r=await askOllama([
      {role:'system',content:`Extrae solo analítica de conversación para un panel interno. No incluyas saldo, crédito, riesgo, salario, edad, teléfono ni otros datos bancarios privados. Devuelve una sola línea JSON válida con estas claves: motivo, sentimiento, intencion, intencion_pago, fecha_propuesta, monto_mencionado, obstaculo, incentivo_mencionado, resultado, siguiente_accion. Si no hay dato usa "No definido".`},
      {role:'user',content:JSON.stringify(compact)}
    ]);
    const start=r.indexOf('{'), end=r.lastIndexOf('}');
    if(start>=0&&end>start){const j=JSON.parse(r.slice(start,end+1)); return {...base, ...{
      reason:j.motivo||base.reason, sentiment:j.sentimiento||base.sentiment, intent:j.intencion||base.intent,
      paymentIntent:j.intencion_pago||base.paymentIntent, proposedDate:j.fecha_propuesta||base.proposedDate,
      amount:j.monto_mencionado||base.amount, obstacle:j.obstaculo||base.obstacle,
      incentive:j.incentivo_mencionado||base.incentive, result:j.resultado||base.result,
      nextAction:j.siguiente_accion||base.nextAction
    }};}
  }catch{}
  return base;
}

function App(){
  const [phone] = useState(new URLSearchParams(location.search).get('telefono')||'');
  const [messages,setMessages]=useState([]);
  const [running,setRunning]=useState(false);
  const [listening,setListening]=useState(false);
  const [busy,setBusy]=useState(false);
  const [partial,setPartial]=useState('');
  const [status,setStatus]=useState('Listo');
  const [analytics,setAnalytics]=useState({verified:'Pendiente',intent:'Pendiente',reason:'Pendiente',sentiment:'Pendiente',paymentIntent:'Pendiente',proposedDate:'No detectada',amount:'No mencionado',incentive:'No mencionado',obstacle:'No definido',result:'En curso',nextAction:'Continuar gestión'});
  const recognitionRef=useRef(null), messagesRef=useRef([]), messagesBoxRef=useRef(null), runningRef=useRef(false), busyRef=useRef(false), verifiedRef=useRef(false), closingRef=useRef(false), micStreamRef=useRef(null), micReadyRef=useRef(false), recognitionStartingRef=useRef(false), retryTimerRef=useRef(null);
  useEffect(()=>{messagesRef.current=messages},[messages]);
  useEffect(()=>{
    const box=messagesBoxRef.current;
    if(!box) return;
    box.scrollTo({top:box.scrollHeight, behavior:'smooth'});
  },[messages,partial]);
  useEffect(()=>{window.speechSynthesis?.getVoices?.();},[]);

  const supported=!!(window.SpeechRecognition||window.webkitSpeechRecognition);

  function add(role,content){setMessages(m=>[...m,{role,content}]);}

  function setupRecognition(){
    const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(!SR){setStatus('Usa Edge o Chrome para la transcripción.');return null;}
    const r=new SR();
    r.lang='es-SV'; r.continuous=true; r.interimResults=true; r.maxAlternatives=3;
    try{r.serviceURI='';}catch{}
    r.onstart=()=>{recognitionStartingRef.current=false;setListening(true);setStatus('Escuchando');};
    r.onnomatch=()=>{setListening(true);setStatus('Escuchando');};
    r.onspeechend=()=>{ /* no detenemos la escucha manualmente */ };
    r.onerror=e=>{
      recognitionStartingRef.current=false;
      setListening(false);
      if(e.error==='not-allowed'||e.error==='service-not-allowed'){
        setStatus('Permite el micrófono en el navegador.');
        return;
      }
      if(e.error==='audio-capture'){
        setStatus('No detecto el micrófono. Revisando el dispositivo…');
        setTimeout(()=>startRecognition(),700);
        return;
      }
      if(e.error==='network'){
        setStatus('Reintentando conexión de voz…');
        setTimeout(()=>startRecognition(),900);
        return;
      }
      if(e.error!=='aborted') setTimeout(()=>startRecognition(),400);
    };
    r.onend=()=>{
      recognitionStartingRef.current=false;
      setListening(false);
      if(runningRef.current && !closingRef.current && !busyRef.current){
        clearTimeout(retryTimerRef.current);
        retryTimerRef.current=setTimeout(()=>startRecognition(),220);
      }
    };
    r.onresult=(e)=>{
      let interim=''; let finalText='';
      for(let i=e.resultIndex;i<e.results.length;i++){
        const t=clean(e.results[i][0]?.transcript);
        if(e.results[i].isFinal) finalText += (finalText?' ':'')+t; else interim += (interim?' ':'')+t;
      }
      setPartial(interim);
      if(finalText && !busyRef.current && runningRef.current) handleUser(finalText);
    };
    recognitionRef.current=r;
    return r;
  }

  async function openMic(){
    if(micReadyRef.current && micStreamRef.current) return true;
    if(!navigator.mediaDevices?.getUserMedia){
      setStatus('Este navegador no permite acceder al micrófono.');
      return false;
    }
    try{
      const stream=await navigator.mediaDevices.getUserMedia({
        audio:{
          echoCancellation:true,
          noiseSuppression:true,
          autoGainControl:true,
          channelCount:1,
          sampleRate:48000,
          sampleSize:16
        }
      });
      stream.getAudioTracks().forEach(track=>{
        try{track.enabled=true;}catch{}
      });
      micStreamRef.current=stream;
      micReadyRef.current=true;
      return true;
    }catch(err){
      micReadyRef.current=false;
      const name=err?.name||'';
      if(name==='NotAllowedError'||name==='SecurityError') setStatus('Permite el micrófono en el navegador.');
      else if(name==='NotFoundError') setStatus('No encontré un micrófono conectado.');
      else setStatus('No pude activar el micrófono.');
      return false;
    }
  }

  function startRecognition(){
    const r=recognitionRef.current;
    if(!r || !runningRef.current || closingRef.current || busyRef.current || recognitionStartingRef.current) return;
    recognitionStartingRef.current=true;
    try{
      r.start();
    }catch(err){
      recognitionStartingRef.current=false;
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current=setTimeout(()=>startRecognition(),350);
    }
  }

  async function start(){
    if(running) return;
    closingRef.current=false; verifiedRef.current=false; setMessages([]); setAnalytics({verified:'Pendiente',intent:'Pendiente',reason:'Pendiente',sentiment:'Pendiente',paymentIntent:'Pendiente',proposedDate:'No detectada',amount:'No mencionado',incentive:'No mencionado',obstacle:'No definido',result:'En curso',nextAction:'Continuar gestión'});
    setStatus('Verificando…');
    await new Promise(res=>setTimeout(res,700));
    const ok=await openMic(); if(!ok) return;
    const r=setupRecognition();
    runningRef.current=true; setRunning(true);
    const opening='Hola, soy Beany, asistente virtual de Bancoagrícola. Te llamo para dar seguimiento preventivo a un pago. ¿Tengo el gusto con el titular?';
    add('assistant',opening); setStatus('Beany está hablando');
    speak(opening,()=>{setStatus('Escuchando');setTimeout(()=>startRecognition(),180);});
  }

  async function handleUser(text){
    if(!clean(text) || busyRef.current || closingRef.current) return;
    const t=clean(text); setPartial(''); add('user',t);
    if(!verifiedRef.current){
      const matched = matchedDatabaseName(t);
      if(matched){
        verifiedRef.current=true; setAnalytics(a=>({...a,verified:'Sí'}));
      } else {
        await finish('Lo siento, creo que nos equivocamos de contacto. Que tengas un feliz día.', 'No confirmado'); return;
      }
    }
    if(/(?:muchas gracias|gracias|ad[ií]os|hasta luego|eso es todo)\b/i.test(t)){await finish('Con gusto. Gracias por tu tiempo y que tengas un buen día.','Cierre por cliente');return;}
    if(/asesor|asesora|agente|persona real|ejecutiv|humano|transfer/i.test(t)){await finish('Claro, con gusto. Te comunicaré con un asesor.','Transferencia a asesor');return;}
    busyRef.current=true; setBusy(true); setStatus('Preparando respuesta…');
    try{
      recognitionRef.current?.stop();
      const history=messagesRef.current.slice(-10).map(m=>({role:m.role,content:m.content}));
      const recentAssistant=messagesRef.current.filter(m=>m.role==='assistant').slice(-3).map(m=>m.content).join(' | ');
      const response=await askOllama([
        {role:'system',content:MASTER_PROMPT+'\nIDIOMA ÚNICO: español.\nNo uses datos bancarios privados en la respuesta.\nIMPORTANTE: nunca dejes una frase incompleta. Termina siempre la idea antes de detenerte, con puntuación final. Máximo 2 frases breves.\nRESPUESTAS RECIENTES DE BEANY (NO REPETIR NI REFORMULAR): '+recentAssistant},
        ...history,
        {role:'user',content:t}
      ]);
      let reply=clean(response)||'Gracias por contármelo. Veamos cuál sería un siguiente paso que te resulte posible.';
      if(reply && !/[.!?]$/.test(reply)) {
        try {
          const completed=await askOllama([
            {role:'system',content:'Completa la frase de Beany sin cambiar su sentido. Devuelve únicamente la frase completa, en español natural, breve y con puntuación final. No agregues otra idea ni una pregunta nueva.'},
            {role:'user',content:reply}
          ]);
          if(completed) reply=clean(completed);
        } catch {}
      }
      const lastAI=messagesRef.current.filter(m=>m.role==='assistant').slice(-1)[0]?.content||'';
      const norm=x=>clean(x).toLowerCase().replace(/[^a-záéíóúüñ0-9 ]/gi,'');
      const replyWords=new Set(norm(reply).split(' ').filter(w=>w.length>3));
      const prevWords=new Set(norm(lastAI).split(' ').filter(w=>w.length>3));
      const overlap=[...replyWords].filter(w=>prevWords.has(w)).length;
      const replyCount=Math.max(1, replyWords.size);
      if(lastAI && overlap/replyCount>=0.8){
        reply=/fecha|viernes|lunes|martes|miércoles|jueves|sábado|domingo|mañana/i.test(t)
          ? 'Tomemos esa fecha y sigamos desde ahí.'
          : 'Gracias por decírmelo. Sigamos con lo que sí puedes hacer.';
      }
      add('assistant',reply); setStatus('Beany está hablando');
      speak(reply,()=>{busyRef.current=false;setBusy(false);if(runningRef.current&&!closingRef.current){setStatus('Escuchando');setTimeout(()=>startRecognition(),180);}});
    }catch{
      const fallback='Gracias por contármelo. Busquemos una opción que te resulte posible.';
      add('assistant',fallback); setStatus('Beany está hablando');
      speak(fallback,()=>{busyRef.current=false;setBusy(false);setStatus('Escuchando');setTimeout(()=>startRecognition(),180)});
    }
    setAnalytics(makeAnalytics([...messagesRef.current,{role:'user',content:t}],{verified:verifiedRef.current}));
  }

  async function finish(text,result){
    closingRef.current=true; runningRef.current=false; setRunning(false); setListening(false); setStatus('Finalizando…'); recognitionRef.current?.stop(); window.speechSynthesis.cancel();
    add('assistant',text); speak(text,async()=>{
      const base=makeAnalytics(messagesRef.current,{verified:verifiedRef.current});
      const enriched=await enrichAnalytics({...base,result,nextAction:result==='Transferencia a asesor'?'Comunicar con asesor':'Gestión finalizada'},messagesRef.current);
      setAnalytics(enriched); setStatus('Llamada finalizada');
      clearTimeout(retryTimerRef.current); micStreamRef.current?.getTracks?.().forEach(t=>t.stop()); micStreamRef.current=null; micReadyRef.current=false;
    });
  }

  return <div className="app">
    <header><div className="brand"><div className="logo">BA</div><div><div className="title">Beany · Bancoagrícola</div><div className="sub">Asistente de cobranza preventiva</div></div></div><div className={`status ${running?'on':''}`}><span></span>{status}</div></header>
    <main>
      <section className="call-card"><div className="avatar">B</div><div className="call-title">Beany</div><div className="call-sub">Llamada preventiva</div><button className={`phone ${running?'active':''}`} onClick={running?()=>finish('Gracias por tu tiempo. Que tengas un buen día.','Cierre manual'):start} aria-label={running?'Finalizar llamada':'Iniciar llamada'}>{running?'☎':'☎'}</button><div className="hint">{supported?'Pulsa para iniciar la llamada':'Este navegador no admite reconocimiento de voz.'}</div></section>
      <section className="conversation"><div className="panel-title">Conversación</div><div className="messages" ref={messagesBoxRef}>{!messages.length?<div className="empty"><div className="big-phone">☎</div><div>La llamada empezará con una breve verificación.</div></div>:messages.map((m,i)=><div key={i} className={`bubble ${m.role}`}>{m.content}</div>)}{partial&&<div className="bubble user interim">{partial}</div>}</div></section>
      <aside className="facts"><div className="panel-title">Datos para analistas</div><div className="facts-note">Solo información derivada de la conversación. No muestra datos bancarios privados.</div>
        {[['Verificación',analytics.verified],['Intención',analytics.intent],['Motivo',analytics.reason],['Sentimiento',analytics.sentiment],['Intención de pago',analytics.paymentIntent],['Fecha propuesta',analytics.proposedDate],['Monto mencionado',analytics.amount],['Incentivo mencionado',analytics.incentive],['Obstáculo',analytics.obstacle],['Resultado',analytics.result],['Siguiente acción',analytics.nextAction]].map(([k,v])=><div className="fact" key={k}><span>{k}</span><strong>{v}</strong></div>)}
      </aside>
    </main>
  </div>
}

createRoot(document.getElementById('root')).render(<App/>);
