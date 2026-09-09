declare module "react" {
  export function useState<T>(initial: T): [T, (v: T) => void];
}
