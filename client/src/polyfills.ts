import { Buffer } from 'buffer';

// @ts-ignore
window.global = window;
// @ts-ignore
window.Buffer = Buffer;
// @ts-ignore
window.process = {
  env: { DEBUG: undefined },
  version: '',
  nextTick: (fn: Function) => setTimeout(fn, 0),
} as any;
