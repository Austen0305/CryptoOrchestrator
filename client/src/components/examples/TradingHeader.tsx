import { TradingHeader } from "../TradingHeader";
import { ThemeProvider } from "../ThemeProvider";

export default function TradingHeaderExample() {
  return (
    <ThemeProvider>
      <TradingHeader balance={125430} connected={true} />
    </ThemeProvider>
  );
}
