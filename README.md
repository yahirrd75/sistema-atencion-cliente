# Sistema de Atención al Cliente con 4 Mesas

Aplicación web para generar turnos consecutivos, asignarlos a cuatro mesas y mantener una fila FIFO. Los cambios se transmiten en tiempo real a todos los navegadores conectados.

## Funcionalidades

- Generación automática de turnos consecutivos, desde el número 1.
- Asignación del turno a una mesa disponible; cada mesa puede atender un solo turno.
- Fila de espera FIFO cuando las cuatro mesas están ocupadas.
- Al finalizar una atención, el primer turno en espera pasa directamente a la mesa que acaba de liberarse.
- Actualización simultánea de varios clientes mediante WebSocket.
- Panel con turno actual, siguiente turno, total generado, estado de las mesas y fila.
- Diseño adaptable a computadora, laptop y pantallas medianas.
- API documentada automáticamente por FastAPI en `/docs`.

## Tecnologías y arquitectura

- **Backend:** Python, FastAPI, Pydantic y Uvicorn.
- **Tiempo real:** WebSocket de FastAPI en `/ws`.
- **Frontend:** Angular 20 creado con Angular CLI, TypeScript y RxJS.
- **Persistencia:** ninguna. El estado vive en memoria dentro del proceso del backend.

El frontend envía las acciones a la API REST. Un servicio de turnos serializa las operaciones concurrentes, modifica el estado en memoria y publica una instantánea a cada conexión WebSocket. Al conectarse, un navegador recibe primero el estado vigente. Si pierde la conexión, intenta reconectarse automáticamente.

## Reglas de turnos y mesas

El primer turno recibe la primera mesa disponible (al inicio, Mesa 1), y así se ocupan las cuatro mesas. Cuando todas están ocupadas, los nuevos turnos se agregan al final de la fila. La fila conserva el orden de llegada.

Al finalizar una mesa, si hay alguien esperando, esa persona recibe inmediatamente la mesa recién liberada. Por ejemplo, si la Mesa 2 termina y el Turno 5 está al frente de la fila, la Mesa 2 comienza a atender el Turno 5. La asignación consulta el estado real de las mesas y no supone que se liberan en orden.

El campo “turno actual” muestra el turno activo más antiguo. “Siguiente turno” muestra el próximo número que se generará.

## Estructura

```text
backend/
  app/
    main.py                 # FastAPI, CORS y endpoint WebSocket
    models/                 # Modelos Pydantic de turno, mesa y estado
    routers/state.py        # API REST
    services/ticketing.py   # Estado en memoria y reglas de asignación
    websocket/manager.py    # Difusión a clientes conectados
  tests/test_ticketing.py   # Pruebas funcionales de la lógica
  requirements.txt
frontend/
  angular.json              # Proyecto generado por Angular CLI
  package.json
  src/app/
    app.component.*         # Panel de atención
    models/                 # Tipos de estado y turno
    services/                # API REST y conexión WebSocket
```

## Requisitos

- Python 3.11 o posterior.
- Node.js 20.19 o posterior y npm.
- Acceso a Internet durante la primera instalación de dependencias.

## Instalación y ejecución en Windows

Abre dos terminales en la carpeta del proyecto.

### 1. Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

La API queda en `http://localhost:8000`; su documentación está en `http://localhost:8000/docs`.

### 2. Frontend

```powershell
cd frontend
npm install
npm start -- --host 0.0.0.0 --port 4200
```

Abre `http://localhost:4200`. Angular CLI sirve la aplicación en modo de desarrollo.

## Uso en una red local

El backend escucha en `0.0.0.0`, por lo que acepta conexiones de la red local. Inicia el frontend también con `--host 0.0.0.0` y permite el tráfico entrante de Windows Firewall en los puertos **4200** (interfaz) y **8000** (API/WebSocket) en una red de confianza. Consulta la dirección IPv4 del equipo servidor con `ipconfig`; desde otro equipo abre `http://DIRECCION-IP:4200`.

El navegador toma el nombre o IP del equipo de la dirección abierta y lo usa para conectarse a la API en el puerto 8000 y al WebSocket `/ws`. Así todas las computadoras que abran el mismo servidor comparten el estado. La aplicación de desarrollo usa HTTP; para exponerla fuera de una red local, configura HTTPS/WSS y controles de acceso en un proxy inverso.

## API

| Método | Ruta | Resultado |
|---|---|---|
| `GET` | `/api/estado` | Estado, contadores, cuatro mesas y fila |
| `POST` | `/api/turnos` | Genera un turno y lo asigna o lo pone en espera |
| `POST` | `/api/mesas/{id}/finalizar` | Finaliza la atención y asigna el siguiente turno en espera |
| `GET` | `/api/mesas` | Estado de las cuatro mesas |
| `GET` | `/api/fila` | Turnos que esperan, en orden FIFO |
| `GET` | `/health` | Comprobación del backend |
| `WebSocket` | `/ws` | Instantánea inicial y cambios de estado en tiempo real |

Finalizar una mesa disponible devuelve HTTP `409`; solicitar una mesa inexistente devuelve HTTP `404`.

## Pruebas

Desde la carpeta `backend` ejecuta:

```powershell
python -m unittest discover -s tests -v
```

Las pruebas cubren la asignación inicial a las cuatro mesas, la reutilización de una mesa liberada, la fila FIFO y el traspaso automático, liberaciones en orden aleatorio, errores al finalizar una mesa disponible o inexistente y consistencia de contadores y estados.

Para compilar Angular desde `frontend`:

```powershell
npm run build
```

Con el backend en ejecución, la prueba de integración de REST y WebSocket se puede ejecutar desde `backend`:

```powershell
python tests/realtime_smoke.py
```

Esta prueba verifica dos clientes conectados, la sincronización de cada evento, la reasignación FIFO, la liberación en orden aleatorio, errores HTTP y la reconexión WebSocket.

## Limitación de almacenamiento

No se utiliza ninguna base de datos ni almacenamiento persistente. Turnos, mesas y fila existen solamente en la memoria del proceso FastAPI; al detener o reiniciar el backend, el contador vuelve a 1 y el sistema comienza con las cuatro mesas disponibles. Mantén una sola instancia del backend: iniciar varias instancias crea estados independientes.
