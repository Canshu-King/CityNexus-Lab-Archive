// Typecheck-only ambient shims. The copied CityNexus frontend snapshot used for
// this isolated lab does not ship @types/react, so this file gives tsc enough
// surface to validate the capability package without changing product code.
declare namespace JSX {
  interface IntrinsicAttributes {
    key?: string | number | null;
  }
  interface IntrinsicClassAttributes<T> extends IntrinsicAttributes {
    ref?: unknown;
  }
  interface Element extends IntrinsicAttributes {}
  interface ElementClass {
    render: unknown;
  }
  interface IntrinsicElements {
    [elementName: string]: any;
  }
}

declare module "react" {
  export type ReactNode = unknown;
  export type ChangeEvent<T = Element> = { target: T & { value: string; checked: boolean } };
  export type FormEvent<T = Element> = { preventDefault(): void; currentTarget: T };
  export function useState<T>(initial: T | (() => T)): [T, (value: T | ((previous: T) => T)) => void];
  export function useId(): string;
  export function useMemo<T>(factory: () => T, dependencies: unknown[]): T;
  export function useEffect(effect: () => void | (() => void), dependencies?: unknown[]): void;
  export function useRef<T>(initial: T | null): { current: T | null };
  export function useCallback<T extends (...args: never[]) => unknown>(callback: T, dependencies: unknown[]): T;
}

declare module "react/jsx-runtime" {
  export const Fragment: unknown;
  export function jsx(type: unknown, props: unknown, key?: unknown): unknown;
  export function jsxs(type: unknown, props: unknown, key?: unknown): unknown;
}
