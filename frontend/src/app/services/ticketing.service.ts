import { Injectable, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { Desk, SystemState, Ticket } from '../models/system-state.model';

@Injectable({ providedIn: 'root' })
export class TicketingService implements OnDestroy {
  private readonly host = window.location.hostname || 'localhost';
  private readonly apiUrl = `http://${this.host}:8000/api`;
  private readonly websocketUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${this.host}:8000/ws`;
  private readonly stateSubject = new BehaviorSubject<SystemState | null>(null);
  private readonly connectedSubject = new BehaviorSubject(false);
  private socket?: WebSocket;
  private reconnectTimer?: number;
  private destroyed = false;

  readonly state$ = this.stateSubject.asObservable();
  readonly connected$ = this.connectedSubject.asObservable();

  constructor(private readonly http: HttpClient) {
    this.loadState().subscribe({
      next: (state) => this.stateSubject.next(state),
      error: () => undefined,
    });
    this.connect();
  }

  loadState(): Observable<SystemState> {
    return this.http.get<SystemState>(`${this.apiUrl}/estado`);
  }

  takeTicket(): Observable<Ticket> {
    return this.http.post<Ticket>(`${this.apiUrl}/turnos`, {});
  }

  finishDesk(deskId: number): Observable<Ticket> {
    return this.http.post<Ticket>(`${this.apiUrl}/mesas/${deskId}/finalizar`, {});
  }

  getDesks(): Observable<Desk[]> {
    return this.http.get<Desk[]>(`${this.apiUrl}/mesas`);
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    if (this.reconnectTimer !== undefined) {
      window.clearTimeout(this.reconnectTimer);
    }
    this.socket?.close();
  }

  private connect(): void {
    if (this.destroyed) return;
    const socket = new WebSocket(this.websocketUrl);
    this.socket = socket;
    socket.onopen = () => this.connectedSubject.next(true);
    socket.onmessage = (message: MessageEvent<string>) => {
      try {
        this.stateSubject.next(JSON.parse(message.data) as SystemState);
      } catch {
        // Ignore malformed messages and keep the latest valid system state.
      }
    };
    socket.onclose = () => {
      this.connectedSubject.next(false);
      if (this.socket === socket) this.socket = undefined;
      if (!this.destroyed) {
        this.reconnectTimer = window.setTimeout(() => this.connect(), 2000);
      }
    };
    socket.onerror = () => socket.close();
  }
}
