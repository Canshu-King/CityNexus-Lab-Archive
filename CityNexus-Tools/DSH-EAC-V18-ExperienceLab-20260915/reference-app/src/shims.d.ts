/**
 * Minimal ambient shims for environments that do not ship @types/react.
 * They are only used by `npm run typecheck`; Vite/esbuild does not need them.
 */
declare namespace JSX {
  interface Element {}
  interface ElementClass {}
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}

declare module "react" {
  export type ReactNode = any;
  export type FormEvent = any;
  export type ChangeEvent<T = Element> = any;
  export type KeyboardEvent<T = Element> = any;
  export type PointerEvent<T = Element> = any;
  export type CSSProperties = any;
  export const StrictMode: any;
  export function useState<T>(initial: T | (() => T)): [T, (value: T | ((prev: T) => T)) => void];
  export function useEffect(effect: () => void | (() => void), deps?: readonly unknown[]): void;
  export function useMemo<T>(factory: () => T, deps: readonly unknown[]): T;
  export function useCallback<T extends (...args: any[]) => any>(fn: T, deps: readonly unknown[]): T;
  export function useContext<T = any>(context: any): T;
  export function useRef<T>(initial: T): { current: T };
  export function createContext<T>(defaultValue: T): any;
}

declare module "react/jsx-runtime" {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
}

declare module "react-dom/client" {
  export function createRoot(container: Element | DocumentFragment): { render(node: any): void };
}

declare module "maplibre-gl" {
  const maplibregl: any;
  export default maplibregl;
  export type Map = any;
  export type FlyToOptions = any;
  export type StyleSpecification = any;
}
