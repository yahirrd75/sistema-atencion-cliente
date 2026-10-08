export type TicketStatus = 'waiting' | 'serving';

export interface Ticket {
  number: number;
  status: TicketStatus;
  desk_id: number | null;
}

export interface Desk {
  id: number;
  ticket: Ticket | null;
}

export interface SystemState {
  total_generated: number;
  current_turn: number | null;
  next_turn: number;
  occupied_desks: number;
  available_desks: number;
  desks: Desk[];
  waiting_queue: Ticket[];
}
