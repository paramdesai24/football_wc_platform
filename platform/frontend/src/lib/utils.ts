import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatNumber(value: number, decimals: number = 0): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `€${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `€${(value / 1_000).toFixed(0)}K`;
  return `€${value}`;
}

export function formatPercentage(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function getFormColor(score: number): string {
  if (score >= 85) return "text-green-600";
  if (score >= 70) return "text-lime-600";
  if (score >= 50) return "text-amber-600";
  if (score >= 30) return "text-orange-600";
  return "text-red-600";
}

export function getFormLabel(score: number): string {
  if (score >= 85) return "Excellent";
  if (score >= 70) return "Good";
  if (score >= 50) return "Average";
  if (score >= 30) return "Poor";
  return "Critical";
}

export function getFormBgColor(score: number): string {
  if (score >= 85) return "bg-green-50 text-green-700";
  if (score >= 70) return "bg-lime-50 text-lime-700";
  if (score >= 50) return "bg-amber-50 text-amber-700";
  if (score >= 30) return "bg-orange-50 text-orange-700";
  return "bg-red-50 text-red-700";
}

export function getPositionColor(position: string): string {
  switch (position) {
    case "GK": return "bg-amber-100 text-amber-800";
    case "DEF": return "bg-blue-100 text-blue-800";
    case "MID": return "bg-emerald-100 text-emerald-800";
    case "FWD": return "bg-red-100 text-red-800";
    default: return "bg-gray-100 text-gray-800";
  }
}

export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}
