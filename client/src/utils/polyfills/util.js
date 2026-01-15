/**
 * Node.js util polyfill for browser compatibility
 * Provides stub implementations for util methods used by libraries
 */

export const debuglog = () => () => {};

export const inspect = (obj) => {
  try {
    return JSON.stringify(obj, null, 2);
  } catch {
    return String(obj);
  }
};

export const deprecate = (fn, msg) => {
  let warned = false;
  return function (...args) {
    if (!warned) {
      console.warn(`Deprecated: ${msg}`);
      warned = true;
    }
    return fn.apply(this, args);
  };
};

export const format = (...args) => {
  if (args.length === 0) return '';
  const str = String(args[0]);
  if (args.length === 1) return str;
  
  let i = 1;
  return str.replace(/%[sdj%]/g, (match) => {
    if (match === '%%') return '%';
    if (i >= args.length) return match;
    const val = args[i++];
    switch (match) {
      case '%s': return String(val);
      case '%d': return Number(val);
      case '%j': return JSON.stringify(val);
      default: return match;
    }
  });
};

export const inherits = (ctor, superCtor) => {
  Object.setPrototypeOf(ctor.prototype, superCtor.prototype);
};

export default {
  debuglog,
  inspect,
  deprecate,
  format,
  inherits,
};
