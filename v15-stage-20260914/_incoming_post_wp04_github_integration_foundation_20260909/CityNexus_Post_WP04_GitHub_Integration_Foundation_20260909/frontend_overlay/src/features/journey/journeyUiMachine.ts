import { setup } from 'xstate';

export type JourneyUiEvent =
  | { type: 'LOAD' }
  | { type: 'LOADED' }
  | { type: 'DISRUPTION_DETECTED' }
  | { type: 'OPEN_REPLAN' }
  | { type: 'ACCEPT' }
  | { type: 'ACCEPTED' }
  | { type: 'FAILED' }
  | { type: 'RESET' };

export const journeyUiMachine = setup({
  types: {
    events: {} as JourneyUiEvent,
  },
}).createMachine({
  id: 'journeyUi',
  initial: 'idle',
  states: {
    idle: { on: { LOAD: 'loading' } },
    loading: { on: { LOADED: 'executing', FAILED: 'error' } },
    executing: { on: { DISRUPTION_DETECTED: 'disrupted' } },
    disrupted: { on: { OPEN_REPLAN: 'comparingReplan' } },
    comparingReplan: { on: { ACCEPT: 'accepting', RESET: 'executing' } },
    accepting: { on: { ACCEPTED: 'executing', FAILED: 'error' } },
    error: { on: { RESET: 'idle' } },
  },
});
