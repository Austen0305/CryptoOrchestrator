import { PriceChart } from "../PriceChart";

const mockData = [
  { time: "00:00", price: 45200 },
  { time: "04:00", price: 45800 },
  { time: "08:00", price: 45300 },
  { time: "12:00", price: 46200 },
  { time: "16:00", price: 46800 },
  { time: "20:00", price: 47100 },
  { time: "24:00", price: 47350 },
];

export default function PriceChartExample() {
  return (
    <div className="h-[600px] p-4">
      <PriceChart
        pair="BTC/USD"
        currentPrice={47350}
        change24h={4.76}
        data={mockData}
      />
    </div>
  );
}
