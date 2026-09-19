export interface ReplanDiffView {
  kept: string[];
  moved: Array<{
    semanticKey: string;
    oldStartAt: string;
    newStartAt: string;
    deltaMinutes: number;
  }>;
  removed: string[];
  added: string[];
  preservedProtected: string[];
  costDeltaMinor: number;
  travelDeltaMinutes?: number;
  endDeltaMinutes?: number;
  reasonCodes: string[];
}
