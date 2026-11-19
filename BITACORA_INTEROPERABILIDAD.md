### 1. Objetivo
 
Documentar la configuración, pruebas de integración, validación del contrato de federación, incidentes detectados y evidencias de interoperabilidad del nodo `g1` dentro del ecosistema distribuido **Tick-Chat**, asegurando la sincronización causal mediante relojes lógicos de Lamport y la diferenciación visual de usuarios pertenecientes a grupos externos (Requisito 10).
 
---
 
### 2. Contrato de Federación y Arquitectura
 
El nodo `g1` está desarrollado con **FastAPI** (backend), **SQLite** (persistencia local), **React + Vite + Tailwind CSS** (frontend) y contenedorizado con **Docker**. Para garantizar la interoperabilidad con nodos de otros grupos (`g2`, `g3`, etc.), se respeta estrictamente el esquema `FederatedMessage`:
 
#### Esquema de Mensaje (`FederatedMessage`)
 
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "from": "carlos@g2",
  "origin": "g2",
  "lamport": 99,
  "sent_at": "2026-11-18T16:00:00Z",
  "body": "Hola desde el nodo externo G2!"
}
```
 
#### Endpoints de Interoperabilidad y API Local
 
| Método | Ruta | Propósito | Estado |
|--------|------|-----------|--------|
| GET | `/fed/health` | Verificación de estado y disponibilidad del nodo (Online/Offline). | Verificado |
| POST | `/fed/messages` | Recepción e inserción de mensajes federados provenientes de otros grupos. | Verificado |
| POST | `/users` | Registro y validación de usuarios locales con formato `usuario@grupo`. | Verificado |
| GET | `/users` | Listado de usuarios locales activos en el nodo. | Verificado |
| POST | `/messages` | Envío de mensajes locales a la sala global `#general` incrementando el reloj de Lamport. | Verificado |
| GET | `/history` | Consulta del historial global ordenado causalmente por `(lamport, origin)`. Soporta `?since=<lamport>`. | Verificado |
 
---
 
### 3. Registro de Pruebas de Interoperabilidad
 
| Fecha / Hora | Nodo Origen | Nodo Destino | Escenario Probado | Reloj Lamport | Resultado | Observaciones |
|--------------|-------------|--------------|-------------------|---------------|-----------|---------------|
| 2026-11-18 10:50 | g1 (Local) | g1 (Local) | Conexión inicial y sincronización de historial en cliente web. | L24 – L36 | Fallido (inicial) | Mensajes mostraban remitente "Desconocido" y burbujas vacías por desajuste de claves en el frontend. |
| 2026-11-18 10:55 | g1 (Local) | g1 (Local) | Registro e inicio de sesión de múltiples clientes (`jaime@g1`, `isabel@g1`, `jhon@g1`). | L34 – L37 | Exitoso | Normalización de identidad `usuario@g1` y envío bidireccional sincronizado cada 2 segundos. |
| 2026-11-18 11:01 | g2 (Externo) | g1 (Local) | Inyección de mensaje federado (`carlos@g2`) hacia el nodo g1 vía `/fed/messages`. | L99 | Exitoso | El nodo g1 validó el esquema `FederatedMessage`, persistió el mensaje y preservó el orden causal. |
| 2026-11-18 11:01 | g2 → g1 | Frontend Web | Validación de distinción visual entre usuarios locales y externos (Requisito 10). | L34 – L99 | Exitoso | Mensajes propios en índigo (derecha), grupo local `@G1` en gris (izquierda) y grupo externo `@G2` en ámbar (izquierda). |
 
---
 
### 4. Incidentes Detectados y Resoluciones
 
#### Incidente 1: Error 400 Bad Request en `POST /users`
 
**Causa:** `LoginModal.jsx` recortaba el sufijo `@g1` antes de registrar el usuario (`username.split('@')[0]`), enviando únicamente el nombre base al backend, mientras que `routes_local.py` exige el formato `usuario@grupo` y rechaza re-registros duplicados.
 
**Resolución:** Se normalizó el identificador en `LoginModal.jsx` y `App.jsx` para garantizar el formato `usuario@g1` y se ajustó `api.js` / `routes_local.py` para permitir el reingreso de usuarios existentes sin error.
 
#### Incidente 2: Renderizado de mensajes como "Desconocido" y burbujas vacías
 
**Causa:** El componente `ChatWindow.jsx` intentaba leer las propiedades `msg.sender` y `msg.text`, mientras que el contrato `FederatedMessage` del backend serializa `from`, `origin` y `body`.
 
**Resolución:** Se actualizó `ChatWindow.jsx` para leer directamente `msg.from`, `msg.origin`, `msg.body` y `msg.lamport`, implementando además el resaltado condicional en ámbar cuando `origin !== myGroup`.
 
#### Incidente 3: Errores de construcción en Docker
 
**Causa:** El contexto de build incluía entornos virtuales (`.venv`), cachés y `node_modules`, generando errores de tubería durante `docker compose build`.
 
**Resolución:** Se creó y ajustó `.dockerignore` (y `app/.dockerignore`) para excluir archivos temporales y dependencias locales.
 
---
 
### 5. Conclusiones
 
- El nodo `g1` cumple con el contrato de federación `FederatedMessage` y mantiene el ordenamiento causal consistente entre múltiples sesiones concurrentes mediante relojes lógicos de Lamport.
- La interfaz web diferencia visualmente de forma clara los tres tipos de origen de mensajes (propios, locales de `@g1` y federados externos como `@g2`), cumpliendo con el Requisito 10.
- Los comandos interactivos de diagnóstico (`/history`, `/users`, `/clear`, `/help`) permiten inspeccionar en tiempo real el estado del nodo y los relojes de Lamport directamente desde el cliente.
 