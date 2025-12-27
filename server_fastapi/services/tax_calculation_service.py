"""
Tax Calculation Service
Handles FIFO, LIFO, and Average cost basis tracking for tax reporting
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)


class CostBasisMethod(str, Enum):
    """Cost basis calculation methods"""
    FIFO = "fifo"  # First In, First Out
    LIFO = "lifo"  # Last In, First Out
    AVERAGE = "average"  # Average cost basis
    SPECIFIC_ID = "specific_id"  # Specific identification (user selects)


@dataclass
class CostBasisLot:
    """Represents a lot of assets with cost basis"""
    purchase_date: datetime
    purchase_price: float
    quantity: float
    cost_basis: float  # purchase_price * quantity
    trade_id: Optional[int] = None
    remaining_quantity: Optional[float] = None  # For partial sales
    
    def __post_init__(self):
        if self.remaining_quantity is None:
            self.remaining_quantity = self.quantity


@dataclass
class TaxableEvent:
    """A taxable event (sale/disposal)"""
    sale_date: datetime
    sale_price: float
    quantity: float
    proceeds: float  # sale_price * quantity
    cost_basis: float
    gain_loss: float  # proceeds - cost_basis
    holding_period_days: int
    is_long_term: bool  # > 1 year
    is_wash_sale: bool = False
    wash_sale_adjustment: float = 0.0
    trade_id: Optional[int] = None
    lots_used: List[CostBasisLot] = None
    
    def __post_init__(self):
        if self.lots_used is None:
            self.lots_used = []


class TaxCalculationService:
    """
    Service for calculating tax obligations using different cost basis methods
    
    Supports:
    - FIFO (First In, First Out)
    - LIFO (Last In, First Out)
    - Average cost basis
    - Specific identification
    - Wash sale detection
    - Long-term vs short-term capital gains
    """
    
    def __init__(self):
        self.lots: Dict[str, List[CostBasisLot]] = {}  # Lots per symbol
        self.taxable_events: Dict[str, List[TaxableEvent]] = {}  # Events per symbol
    
    def add_purchase(
        self,
        symbol: str,
        purchase_date: datetime,
        purchase_price: float,
        quantity: float,
        trade_id: Optional[int] = None,
    ):
        """
        Add a purchase to cost basis tracking
        
        Args:
            symbol: Asset symbol (e.g., "BTC")
            purchase_date: Date of purchase
            purchase_price: Price per unit
            quantity: Quantity purchased
            trade_id: Optional trade ID reference
        """
        if symbol not in self.lots:
            self.lots[symbol] = []
        
        lot = CostBasisLot(
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            quantity=quantity,
            cost_basis=purchase_price * quantity,
            trade_id=trade_id,
        )
        
        self.lots[symbol].append(lot)
        logger.debug(f"Added purchase: {symbol} {quantity} @ {purchase_price}")
    
    def calculate_sale(
        self,
        symbol: str,
        sale_date: datetime,
        sale_price: float,
        quantity: float,
        method: CostBasisMethod = CostBasisMethod.FIFO,
        trade_id: Optional[int] = None,
    ) -> TaxableEvent:
        """
        Calculate taxable gain/loss for a sale
        
        Args:
            symbol: Asset symbol
            sale_date: Date of sale
            sale_price: Price per unit
            quantity: Quantity sold
            method: Cost basis method (FIFO, LIFO, AVERAGE)
            trade_id: Optional trade ID reference
        
        Returns:
            TaxableEvent with calculated gain/loss
        """
        if symbol not in self.lots or not self.lots[symbol]:
            raise ValueError(f"No cost basis lots found for {symbol}")
        
        proceeds = sale_price * quantity
        remaining_quantity = quantity
        lots_used = []
        total_cost_basis = 0.0
        
        # Get available lots
        available_lots = [lot for lot in self.lots[symbol] if lot.remaining_quantity > 0]
        
        if method == CostBasisMethod.FIFO:
            # First In, First Out - oldest lots first
            available_lots.sort(key=lambda x: x.purchase_date)
        elif method == CostBasisMethod.LIFO:
            # Last In, First Out - newest lots first
            available_lots.sort(key=lambda x: x.purchase_date, reverse=True)
        elif method == CostBasisMethod.AVERAGE:
            # Average cost basis - calculate weighted average
            total_cost = sum(lot.cost_basis for lot in available_lots)
            total_qty = sum(lot.remaining_quantity for lot in available_lots)
            if total_qty > 0:
                avg_cost = total_cost / total_qty
                total_cost_basis = avg_cost * quantity
                # Create a synthetic lot for average method
                lots_used = [CostBasisLot(
                    purchase_date=available_lots[0].purchase_date if available_lots else sale_date,
                    purchase_price=avg_cost,
                    quantity=quantity,
                    cost_basis=total_cost_basis,
                )]
                remaining_quantity = 0
        
        # For FIFO and LIFO, consume lots until quantity is satisfied
        if method in [CostBasisMethod.FIFO, CostBasisMethod.LIFO]:
            for lot in available_lots:
                if remaining_quantity <= 0:
                    break
                
                qty_to_use = min(remaining_quantity, lot.remaining_quantity)
                cost_basis_used = (lot.cost_basis / lot.quantity) * qty_to_use
                
                total_cost_basis += cost_basis_used
                lot.remaining_quantity -= qty_to_use
                remaining_quantity -= qty_to_use
                
                # Create a copy for tracking
                used_lot = CostBasisLot(
                    purchase_date=lot.purchase_date,
                    purchase_price=lot.purchase_price,
                    quantity=qty_to_use,
                    cost_basis=cost_basis_used,
                    trade_id=lot.trade_id,
                )
                lots_used.append(used_lot)
        
        if remaining_quantity > 0:
            raise ValueError(f"Insufficient cost basis lots for sale: {symbol} {quantity}")
        
        # Calculate holding period (use oldest lot for mixed lots)
        oldest_lot = min(lots_used, key=lambda x: x.purchase_date)
        holding_period = (sale_date - oldest_lot.purchase_date).days
        is_long_term = holding_period > 365
        
        # Calculate gain/loss
        gain_loss = proceeds - total_cost_basis
        
        # Check for wash sale (simplified - would need more sophisticated detection)
        is_wash_sale = self._check_wash_sale(symbol, sale_date, lots_used)
        wash_sale_adjustment = 0.0
        
        if is_wash_sale:
            # Wash sale rules: disallow loss deduction, add to cost basis of replacement
            if gain_loss < 0:  # Loss
                wash_sale_adjustment = abs(gain_loss)
                gain_loss = 0.0  # Disallow loss
        
        event = TaxableEvent(
            sale_date=sale_date,
            sale_price=sale_price,
            quantity=quantity,
            proceeds=proceeds,
            cost_basis=total_cost_basis,
            gain_loss=gain_loss,
            holding_period_days=holding_period,
            is_long_term=is_long_term,
            is_wash_sale=is_wash_sale,
            wash_sale_adjustment=wash_sale_adjustment,
            trade_id=trade_id,
            lots_used=lots_used,
        )
        
        # Store event
        if symbol not in self.taxable_events:
            self.taxable_events[symbol] = []
        self.taxable_events[symbol].append(event)
        
        return event
    
    def _check_wash_sale(
        self,
        symbol: str,
        sale_date: datetime,
        lots_used: List[CostBasisLot],
    ) -> bool:
        """
        Check if sale qualifies as wash sale
        
        Wash sale: Selling at a loss and repurchasing within 30 days
        """
        # Simplified wash sale detection
        # In production, would check for repurchases within 30 days
        window_start = sale_date - timedelta(days=30)
        window_end = sale_date + timedelta(days=30)
        
        # Check if any lots were purchased within wash sale window
        for lot in lots_used:
            if window_start <= lot.purchase_date <= window_end:
                # Check if this was a loss
                # Would need sale price vs purchase price comparison
                return True
        
        return False
    
    def get_tax_summary(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Get tax summary for reporting
        
        Returns:
            Dictionary with short-term/long-term gains, total proceeds, etc.
        """
        events = []
        
        if symbol:
            events = self.taxable_events.get(symbol, [])
        else:
            # All symbols
            for sym_events in self.taxable_events.values():
                events.extend(sym_events)
        
        # Filter by date range
        if start_date:
            events = [e for e in events if e.sale_date >= start_date]
        if end_date:
            events = [e for e in events if e.sale_date <= end_date]
        
        # Calculate totals
        short_term_gains = sum(
            e.gain_loss for e in events
            if not e.is_long_term and e.gain_loss > 0
        )
        short_term_losses = sum(
            abs(e.gain_loss) for e in events
            if not e.is_long_term and e.gain_loss < 0
        )
        long_term_gains = sum(
            e.gain_loss for e in events
            if e.is_long_term and e.gain_loss > 0
        )
        long_term_losses = sum(
            abs(e.gain_loss) for e in events
            if e.is_long_term and e.gain_loss < 0
        )
        
        total_proceeds = sum(e.proceeds for e in events)
        total_cost_basis = sum(e.cost_basis for e in events)
        net_gain_loss = total_proceeds - total_cost_basis
        
        wash_sale_count = sum(1 for e in events if e.is_wash_sale)
        wash_sale_adjustment = sum(e.wash_sale_adjustment for e in events)
        
        return {
            "symbol": symbol,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "total_events": len(events),
            "short_term": {
                "gains": short_term_gains,
                "losses": short_term_losses,
                "net": short_term_gains - short_term_losses,
            },
            "long_term": {
                "gains": long_term_gains,
                "losses": long_term_losses,
                "net": long_term_gains - long_term_losses,
            },
            "total_proceeds": total_proceeds,
            "total_cost_basis": total_cost_basis,
            "net_gain_loss": net_gain_loss,
            "wash_sales": {
                "count": wash_sale_count,
                "total_adjustment": wash_sale_adjustment,
            },
        }
    
    def get_tax_loss_harvesting_opportunities(
        self,
        symbol: str,
        current_price: float,
        threshold_percent: float = 0.1,  # 10% loss threshold
    ) -> List[Dict]:
        """
        Identify tax-loss harvesting opportunities
        
        Finds lots that are at a loss and could be sold to realize losses
        for tax purposes.
        """
        if symbol not in self.lots:
            return []
        
        opportunities = []
        
        for lot in self.lots[symbol]:
            if lot.remaining_quantity <= 0:
                continue
            
            current_value = current_price * lot.remaining_quantity
            cost_basis = (lot.cost_basis / lot.quantity) * lot.remaining_quantity
            unrealized_loss = current_value - cost_basis
            loss_percent = (unrealized_loss / cost_basis) * 100 if cost_basis > 0 else 0
            
            if unrealized_loss < 0 and abs(loss_percent) >= threshold_percent:
                opportunities.append({
                    "lot": lot,
                    "current_price": current_price,
                    "current_value": current_value,
                    "cost_basis": cost_basis,
                    "unrealized_loss": unrealized_loss,
                    "loss_percent": loss_percent,
                    "holding_period_days": (datetime.utcnow() - lot.purchase_date).days,
                })
        
        # Sort by loss amount (most negative first)
        opportunities.sort(key=lambda x: x["unrealized_loss"])
        
        return opportunities


# Global instance
tax_calculation_service = TaxCalculationService()
