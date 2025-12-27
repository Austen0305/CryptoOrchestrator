/**
 * Deposit Modal Component
 * Shows deposit address with QR code and copy functionality
 */
import { useEffect, useRef, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Copy, Check, QrCode as QrCodeIcon, ExternalLink } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info } from "lucide-react";
import logger from "@/lib/logger";

interface DepositModalProps {
  walletId: number;
  address: string;
  chainId: number;
  chainName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DepositModal({
  walletId,
  address,
  chainId,
  chainName,
  open,
  onOpenChange,
}: DepositModalProps) {
  const { toast } = useToast();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (canvasRef.current && address && open) {
      // Dynamically import qrcode to avoid SSR issues
      import("qrcode").then((QRCode) => {
        if (!canvasRef.current) return;
        QRCode.default.toCanvas(canvasRef.current, address, {
          width: 256,
          margin: 2,
          color: {
            dark: "#000000",
            light: "#FFFFFF",
          },
        });
      }).catch((error) => {
        logger.error("Failed to generate QR code", { error });
      });
    }
  }, [address, open]);

  const handleCopy = () => {
    navigator.clipboard.writeText(address);
    setCopied(true);
    toast({
      title: "Copied",
      description: "Address copied to clipboard",
    });
    setTimeout(() => setCopied(false), 2000);
  };

  const getExplorerUrl = () => {
    const explorerUrls: Record<number, string> = {
      1: `https://etherscan.io/address/${address}`,
      8453: `https://basescan.org/address/${address}`,
      42161: `https://arbiscan.io/address/${address}`,
      137: `https://polygonscan.com/address/${address}`,
      10: `https://optimistic.etherscan.io/address/${address}`,
      43114: `https://snowtrace.io/address/${address}`,
      56: `https://bscscan.com/address/${address}`,
    };
    return explorerUrls[chainId] || `https://etherscan.io/address/${address}`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Deposit to {chainName} Wallet</DialogTitle>
          <DialogDescription>
            Send funds to this address. Only send {chainName} native tokens or supported ERC-20 tokens to this address.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* QR Code */}
          <div className="flex justify-center p-4 bg-muted rounded-lg">
            <canvas ref={canvasRef} className="max-w-full h-auto" />
          </div>

          {/* Address */}
          <div>
            <Label>Deposit Address</Label>
            <div className="flex items-center gap-2 mt-2">
              <Input
                value={address}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={handleCopy}
              >
                {copied ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          {/* Warning */}
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>Only send {chainName} native tokens or supported ERC-20 tokens</li>
                <li>Do not send tokens from other blockchains to this address</li>
                <li>Double-check the address before sending</li>
                <li>Minimum deposit amounts may apply</li>
              </ul>
            </AlertDescription>
          </Alert>

          {/* Actions */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => window.open(getExplorerUrl(), "_blank")}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              View on Explorer
            </Button>
            <Button
              className="flex-1"
              onClick={() => onOpenChange(false)}
            >
              Done
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
