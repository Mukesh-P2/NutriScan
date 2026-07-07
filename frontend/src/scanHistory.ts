// Local (pre-login) scan history, persisted in localStorage so past scans survive reloads and
// can be reopened or compared. Best-effort: any storage error degrades to "no history".
import type { AnalysisResult } from "./types";

const KEY = "nutriscan_scan_history";
const MAX = 20;

export interface ScanHistoryItem {
  id: string;
  at: number; // epoch ms
  result: AnalysisResult;
}

export function getScanHistory(): ScanHistoryItem[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const items = JSON.parse(raw);
    return Array.isArray(items) ? (items as ScanHistoryItem[]) : [];
  } catch {
    return [];
  }
}

function save(items: ScanHistoryItem[]): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(items.slice(0, MAX)));
  } catch {
    /* storage full or disabled — history is best-effort */
  }
}

export function addScan(result: AnalysisResult): ScanHistoryItem[] {
  const item: ScanHistoryItem = {
    id: `${Date.now()}-${Math.round(Math.random() * 1e6)}`,
    at: Date.now(),
    result,
  };
  const items = [item, ...getScanHistory()].slice(0, MAX);
  save(items);
  return items;
}

export function removeScan(id: string): ScanHistoryItem[] {
  const items = getScanHistory().filter((i) => i.id !== id);
  save(items);
  return items;
}

export function clearScanHistory(): ScanHistoryItem[] {
  save([]);
  return [];
}
