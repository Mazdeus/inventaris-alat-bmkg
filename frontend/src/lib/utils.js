import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Menggabungkan class Tailwind dengan aman.
 * Menghilangkan konflik dan duplikasi class Tailwind.
 * @param  {...string} inputs - Class-class yang mau digabung
 * @returns {string} Class hasil merge
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
