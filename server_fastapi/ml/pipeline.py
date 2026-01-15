from datetime import UTC, datetime

import polars as pl
import torch
import torch.nn as nn

from server_fastapi.services.market_data_service import MarketDataService


# Simple Transformer Model for Price Prediction
class PriceTransformer(nn.Module):
    def __init__(self, input_dim=10, d_model=64, nhead=4, num_layers=2):
        super().__init__()
        self.embedding = nn.Linear(input_dim, d_model)
        self.transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead),
            num_layers=num_layers,
        )
        self.fc = nn.Linear(d_model, 1)

    def forward(self, x):
        # x shape: (batch, seq_len, input_dim)
        x = self.embedding(x)
        x = x.permute(1, 0, 2)  # Transformer expects (seq_len, batch, feature)
        out = self.transformer(x)
        return self.fc(out[-1, :, :])


class TrainingPipeline:
    def __init__(self, market_service: MarketDataService):
        self.market_service = market_service
        self.model = PriceTransformer()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()

    async def train_epoch(self, symbol: str):
        # 1. Fetch Data (Polars)
        df = await self.market_service.get_historical_prices(symbol)

        # 2. Preprocess (Polars -> Torch)
        # Assuming df has 'price' and we use lag features
        if df.height < 50:
            return {"status": "insufficient_data"}

        prices = df.select(pl.col("price")).to_numpy()
        data_tensor = torch.tensor(prices, dtype=torch.float32)

        # 3. Forward Pass (Mock)
        # In real impl, we'd batch this.
        # This acts as a smoke test for the integration.
        output = self.model(data_tensor.unsqueeze(0).unsqueeze(0))  # Dummy dimensions
        loss = self.criterion(output, torch.tensor([[0.0]]))  # Dummy target

        # 4. Backward
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return {"loss": loss.item(), "timestamp": datetime.now(UTC).isoformat()}


# Usage Example:
# pipeline = TrainingPipeline(MarketDataService(...))
# result = await pipeline.train_epoch("BTC-USD")
