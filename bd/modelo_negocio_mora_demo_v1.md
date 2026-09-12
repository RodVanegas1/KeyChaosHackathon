# Modelo de negocio — Demo de prevención de mora

## 1. Objetivo

La primera versión del sistema busca demostrar un flujo preventivo de mora:

1. El sistema identifica usuarios con un riesgo elevado de caer en mora.
2. El backend determina si corresponde iniciar una comunicación preventiva.
3. El sistema establece una conversación mediante WhatsApp.
4. Un LLM interpreta los mensajes y genera respuestas siguiendo las reglas de negocio.
5. El backend valida la información obtenida de la conversación.
6. Si el usuario acepta realizar un pago, se registra un compromiso de pago.
7. La conversación y su resultado quedan almacenados para seguimiento y trazabilidad.

El objetivo de esta versión es demostrar el flujo completo, no construir todavía un modelo predictivo bancario de producción.

---

## 2. Principio de arquitectura

El sistema separa las responsabilidades entre el LLM y el backend.

### LLM

El LLM se encarga de:

- comprender lenguaje natural;
- mantener el contexto de la conversación;
- generar respuestas;
- identificar la intención del usuario;
- extraer datos relevantes de las respuestas;
- generar un resumen estructurado de la conversación.

### Backend

El backend se encarga de:

- consultar usuarios y créditos;
- calcular el riesgo;
- aplicar reglas de negocio;
- determinar cuándo corresponde contactar al usuario;
- validar los datos producidos por el LLM;
- registrar compromisos de pago;
- almacenar la conversación;
- mantener la integridad de los datos.

El LLM no tiene autoridad directa para modificar información crítica de la base de datos.

---

## 3. Entidades principales

### Usuario

Representa a la persona que posee un crédito.

Datos principales:

- identificador;
- nombre;
- teléfono;
- correo electrónico;
- fecha de registro.

El teléfono debe ser único porque constituye el dato utilizado para relacionar la comunicación de WhatsApp con el usuario.

---

### Crédito

Representa una obligación financiera asociada a un usuario.

Datos principales:

- monto original;
- saldo pendiente;
- fecha de inicio;
- fecha de vencimiento;
- estado.

Un usuario puede poseer uno o varios créditos.

Los días restantes para el vencimiento no se almacenan como dato permanente. Se calculan a partir de la fecha actual y la fecha de vencimiento.

---

### Pago

Representa un pago programado o realizado asociado a un crédito.

Permite reconstruir el comportamiento histórico del usuario.

A partir de los pagos pueden obtenerse variables como:

- cantidad de pagos;
- cantidad de pagos tardíos;
- tasa de retraso;
- promedio de días de retraso;
- comportamiento reciente.

Estas variables son utilizadas por el motor de riesgo.

---

## 4. Evaluación de riesgo

Una evaluación de riesgo representa el resultado del motor de riesgo en un momento determinado.

No se almacena solamente el riesgo actual del crédito.

Se almacenan evaluaciones sucesivas:

```text
12/09 → 42%
14/09 → 57%
15/09 → 71%
16/09 → 84%
```

Esto permite observar la evolución del riesgo.

La evaluación contiene:

- score de 0 a 100;
- probabilidad estimada de mora;
- nivel de riesgo;
- días restantes;
- tasa histórica de retraso;
- promedio de días de retraso;
- cantidad de pagos tardíos recientes;
- tendencia;
- versión del modelo utilizado;
- fecha de cálculo.

La versión del modelo permite distinguir resultados generados por diferentes versiones del motor en el futuro.

---

## 5. Regla de contacto preventivo

La primera versión utilizará el resultado de la evaluación de riesgo para determinar si un usuario debe entrar al flujo de contacto.

Conceptualmente:

```text
Evaluación de riesgo
        |
        v
¿Riesgo suficientemente alto?
        |
      Sí
        |
        v
¿Crédito activo y pendiente?
        |
      Sí
        |
        v
¿Usuario puede ser contactado?
        |
      Sí
        |
        v
Iniciar conversación
```

Los umbrales exactos se definirán posteriormente.

La decisión de iniciar una conversación pertenece al backend y no al LLM.

---

## 6. Conversación

Una conversación representa una interacción completa con un usuario mediante WhatsApp.

Una conversación puede estar asociada a un crédito específico, ya que el motivo principal del contacto es prevenir la mora de dicha obligación.

Estados posibles:

- INICIADA
- EN_CURSO
- COMPLETADA
- CANCELADA
- FALLIDA

Una misma persona puede tener múltiples conversaciones a lo largo del tiempo.

---

## 7. Mensajes

Cada conversación conserva sus mensajes.

Cada mensaje registra:

- remitente;
- tipo;
- contenido;
- identificador externo de WhatsApp, cuando exista;
- fecha y hora.

Los remitentes posibles son:

- `USUARIO`
- `ASISTENTE`
- `SISTEMA`

En la primera versión se priorizan mensajes de texto, pero el modelo permite representar posteriormente audio e imágenes.

### Motivo de conservar los mensajes

No se recomienda almacenar únicamente el resultado final generado por el LLM.

El historial permite:

- reconstruir la conversación;
- auditar qué ocurrió;
- verificar la interpretación del LLM;
- mejorar futuros prompts;
- analizar errores;
- generar nuevas métricas.

---

## 8. Resumen de conversación

Al finalizar una conversación, el LLM puede generar una salida estructurada.

Ejemplo conceptual:

```json
{
  "intencion": "COMPROMISO_PAGO",
  "compromiso_pago": true,
  "fecha_compromiso": "2026-09-17",
  "resumen": "El usuario indicó que realizará el pago el jueves.",
  "resultado": "COMPROMISO_OBTENIDO"
}
```

Esta información se almacena en `resumen_conversacion`.

El resumen no sustituye a los mensajes originales.

El LLM puede proponer estos datos, pero el backend debe validarlos antes de utilizarlos como información operativa.

---

## 9. Compromiso de pago

Un compromiso de pago representa una acción operativa que el sistema reconoce como válida.

Flujo:

```text
Usuario
   |
   v
Mensaje de WhatsApp
   |
   v
LLM interpreta
   |
   v
Salida estructurada
   |
   v
Backend valida
   |
   v
Compromiso de pago
```

Por ejemplo, si el usuario dice:

> "Sí, puedo pagarlo el jueves."

El LLM puede identificar:

```json
{
  "intencion": "COMPROMISO_PAGO",
  "fecha_compromiso": "2026-09-17"
}
```

Pero el backend debe comprobar:

- que la fecha sea válida;
- que corresponda con el contexto del crédito;
- que el crédito continúe activo;
- que el compromiso cumpla las reglas de negocio.

Solo después de esa validación se registra el compromiso.

---

## 10. Estados del compromiso

Un compromiso puede pasar por diferentes estados:

```text
PENDIENTE
   |
   +----> CUMPLIDO
   |
   +----> INCUMPLIDO
   |
   +----> CANCELADO
```

Esto permite posteriormente medir si la intervención conversacional consiguió el resultado esperado.

---

## 11. Ejemplo completo del flujo

Supongamos:

```text
Usuario:
Carlos

Crédito:
Saldo pendiente: $850
Vencimiento: 17/09

Riesgo:
84%
Nivel: ALTO
Tendencia: AUMENTANDO
```

El backend determina que debe realizarse contacto preventivo.

Se crea:

```text
Conversation #9281
```

El asistente inicia la conversación.

```text
ASISTENTE:
Hola Carlos. Te contactamos porque tu próximo pago
se encuentra próximo a su fecha de vencimiento.
¿Podrías indicarnos cuándo estimas realizarlo?
```

El usuario responde:

```text
USUARIO:
El jueves puedo hacerlo.
```

El LLM interpreta:

```json
{
  "intencion": "COMPROMISO_PAGO",
  "compromiso_pago": true,
  "fecha_compromiso": "2026-09-17"
}
```

El backend valida la información.

Si cumple las reglas:

```text
Compromiso de pago
Fecha: 17/09
Estado: PENDIENTE
```

La conversación se cierra como:

```text
COMPLETADA
```

y su resultado:

```text
COMPROMISO_OBTENIDO
```

---

## 12. Información que NO debe controlar directamente el LLM

El LLM no debería poder decidir directamente:

- modificar el saldo del crédito;
- marcar un crédito como pagado;
- cambiar el estado de un crédito;
- modificar el score de riesgo;
- crear un pago real;
- cambiar información financiera;
- eliminar conversaciones;
- crear compromisos sin validación del backend.

El LLM produce una interpretación.

El backend convierte esa interpretación en una acción válida.

---

## 13. Flujo general de la V1

```text
                 ┌─────────────┐
                 │   Usuario   │
                 └──────┬──────┘
                        │
                     WhatsApp
                        │
                        v
              ┌──────────────────┐
              │ Python Backend   │
              └────────┬─────────┘
                       │
              ┌────────┴─────────┐
              │                  │
              v                  v
       Motor de riesgo      Conversación
              │                  │
              │                  v
              │                 LLM
              │                  │
              │           Salida estructurada
              │                  │
              │                  v
              │          Reglas de negocio
              │                  │
              │                  v
              │          Compromiso de pago
              │
              v
       Nivel de riesgo
```

---

## 14. Alcance de la primera demo

La V1 debe concentrarse en demostrar:

1. Datos simulados de usuarios y créditos.
2. Historial de pagos.
3. Cálculo de riesgo preventivo.
4. Identificación de usuarios de riesgo elevado.
5. Inicio de una conversación por WhatsApp.
6. Persistencia de todos los mensajes.
7. Interpretación de la conversación mediante un LLM.
8. Generación de un resumen estructurado.
9. Validación del resultado por el backend.
10. Registro de un compromiso de pago.
11. Seguimiento del estado del compromiso.

No se considera parte de la primera versión:

- modelo de Machine Learning entrenado con datos bancarios reales;
- scoring crediticio de producción;
- ejecución real de transacciones;
- decisiones automatizadas de crédito;
- infraestructura bancaria productiva;
- integración completa con sistemas core bancarios.

La finalidad de la V1 es demostrar la viabilidad del flujo preventivo:

**detectar → contactar → conversar → obtener compromiso → registrar → dar seguimiento.**
