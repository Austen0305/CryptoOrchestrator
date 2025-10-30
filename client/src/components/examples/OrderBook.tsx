import { OrderBook } from "../OrderBook";

const mockBids = [
  { price: 47340, amount: 0.5234, total: 24765 },
  { price: 47335, amount: 1.2341, total: 58405 },
  { price: 47330, amount: 0.8921, total: 42207 },
  { price: 47325, amount: 2.1234, total: 100489 },
  { price: 47320, amount: 0.4567, total: 21608 },
  { price: 47315, amount: 1.7892, total: 84639 },
  { price: 47310, amount: 0.9234, total: 43682 },
];

const mockAsks = [
  { price: 47355, amount: 0.6234, total: 29521 },
  { price: 47360, amount: 1.4321, total: 67828 },
  { price: 47365, amount: 0.7821, total: 37039 },
  { price: 47370, amount: 2.3421, total: 110952 },
  { price: 47375, amount: 0.5421, total: 25682 },
  { price: 47380, amount: 1.8921, total: 89636 },
  { price: 47385, amount: 0.8234, total: 39015 },
];

export default function OrderBookExample() {
  return (
    <div className="max-w-md p-4">
      <OrderBook bids={mockBids} asks={mockAsks} spread={15} />
    </div>
  );
}
