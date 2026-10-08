import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { TicketingService } from './services/ticketing.service';
import { SystemState } from './models/system-state.model';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  private readonly ticketing = inject(TicketingService);
  readonly state$ = this.ticketing.state$;
  readonly connected$ = this.ticketing.connected$;
  busy = false;
  errorMessage = '';
  successMessage = '';

  takeTicket(): void {
    this.runAction(() => this.ticketing.takeTicket(), (ticket) => {
      this.successMessage = `Turno ${ticket.number} generado.`;
    });
  }

  finishDesk(deskId: number): void {
    this.runAction(() => this.ticketing.finishDesk(deskId), (ticket) => {
      this.successMessage = `La Mesa ${deskId} finalizó el Turno ${ticket.number}.`;
    });
  }

  trackDesk(_index: number, desk: { id: number }): number {
    return desk.id;
  }

  trackTicket(_index: number, ticket: { number: number }): number {
    return ticket.number;
  }

  private runAction<T>(request: () => import('rxjs').Observable<T>, onSuccess: (result: T) => void): void {
    this.busy = true;
    this.errorMessage = '';
    this.successMessage = '';
    request().subscribe({
      next: (result) => {
        onSuccess(result);
        this.busy = false;
      },
      error: (error: { error?: { detail?: string }; message?: string }) => {
        this.errorMessage = error.error?.detail ?? error.message ?? 'No se pudo completar la operación.';
        this.busy = false;
      },
    });
  }
}
