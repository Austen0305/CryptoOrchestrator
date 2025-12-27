// Type declarations for qrcode
declare module 'qrcode' {
  export function toDataURL(
    text: string,
    options?: {
      errorCorrectionLevel?: 'L' | 'M' | 'Q' | 'H';
      type?: 'image/png' | 'image/jpeg' | 'image/webp';
      quality?: number;
      margin?: number;
      color?: {
        dark?: string;
        light?: string;
      };
      width?: number;
    }
  ): Promise<string>;

  export function toCanvas(
    canvas: HTMLCanvasElement,
    text: string,
    options?: any
  ): Promise<void>;

  export function toString(
    text: string,
    options?: any
  ): Promise<string>;
}

