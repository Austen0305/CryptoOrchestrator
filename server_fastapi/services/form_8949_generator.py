"""
Form 8949 Generator
Generates IRS Form 8949 for cryptocurrency capital gains and losses
"""

import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from .tax_calculation_service import TaxableEvent, TaxCalculationService

logger = logging.getLogger(__name__)


@dataclass
class Form8949Row:
    """A single row on Form 8949 (Extended for 1099-DA)"""

    # Part I: Short-term transactions
    # Part II: Long-term transactions

    description: str  # Description of property (e.g., "Bitcoin")
    date_acquired: str  # Date acquired (MM/DD/YYYY)
    date_sold: str  # Date sold (MM/DD/YYYY)
    proceeds: float  # Sales proceeds
    cost_basis: float  # Cost or other basis
    code: str  # Adjustment code (if applicable)
    adjustment_amount: float  # Amount of adjustment
    gain_loss: float  # Gain or (loss)
    is_long_term: bool  # True for Part II, False for Part I
    # IRS 1099-DA Extensions
    transaction_hash: str = ""
    digital_asset_address: str = ""


class Form8949Generator:
    """
    Generator for IRS Form 8949 (with 1099-DA support)

    Form 8949 is used to report sales and exchanges of capital assets.
    This generator creates the form data structure that can be exported
    to PDF or imported into tax software.
    """

    def __init__(self, tax_service: TaxCalculationService):
        self.tax_service = tax_service

    def generate_form_8949(
        self,
        user_id: int,
        tax_year: int,
        method: str = "fifo",
    ) -> dict:
        """
        Generate Form 8949 data structure

        Args:
            user_id: User ID
            tax_year: Tax year (e.g., 2024)
            method: Cost basis method (fifo, lifo, average)

        Returns:
            Dictionary with Form 8949 data
        """
        start_date = datetime(tax_year, 1, 1)
        end_date = datetime(tax_year, 12, 31, 23, 59, 59)

        # Get all taxable events for the year
        summary = self.tax_service.get_tax_summary(
            start_date=start_date,
            end_date=end_date,
        )

        # Get all events (would need to be stored/retrieved from database)
        # For now, using the service's internal events
        all_events = []
        for symbol_events in self.tax_service.taxable_events.values():
            year_events = [
                e for e in symbol_events if start_date <= e.sale_date <= end_date
            ]
            all_events.extend(year_events)

        # Separate short-term and long-term
        short_term_events = [e for e in all_events if not e.is_long_term]
        long_term_events = [e for e in all_events if e.is_long_term]

        # Generate rows
        short_term_rows = [self._event_to_row(e) for e in short_term_events]
        long_term_rows = [self._event_to_row(e) for e in long_term_events]

        # Calculate totals
        short_term_totals = self._calculate_totals(short_term_rows)
        long_term_totals = self._calculate_totals(long_term_rows)

        return {
            "tax_year": tax_year,
            "user_id": user_id,
            "part_i": {
                "title": "Part I - Short-Term Capital Gains and Losses",
                "rows": short_term_rows,
                "totals": short_term_totals,
            },
            "part_ii": {
                "title": "Part II - Long-Term Capital Gains and Losses",
                "rows": long_term_rows,
                "totals": long_term_totals,
            },
            "summary": summary,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def _event_to_row(self, event: TaxableEvent) -> Form8949Row:
        """Convert a TaxableEvent to a Form 8949 row"""
        # Get symbol from lots (simplified - would need better tracking)
        symbol = "Cryptocurrency"
        if event.lots_used:
            # Try to extract symbol from trade_id or other metadata
            symbol = "Cryptocurrency"  # Would need to look up actual symbol

        # Format dates
        date_acquired = (
            event.lots_used[0].purchase_date.strftime("%m/%d/%Y")
            if event.lots_used
            else ""
        )
        date_sold = event.sale_date.strftime("%m/%d/%Y")

        # Determine adjustment code
        code = ""
        adjustment_amount = 0.0

        if event.is_wash_sale:
            code = "W"  # Wash sale
            adjustment_amount = event.wash_sale_adjustment

        # 1099-DA Enrichment
        # If we have the address, append it to description (common practice)
        if event.digital_asset_address:
            symbol = f"{symbol} ({event.digital_asset_address[:8]}...)"

        return Form8949Row(
            description=symbol,
            date_acquired=date_acquired,
            date_sold=date_sold,
            proceeds=event.proceeds,
            cost_basis=event.cost_basis,
            code=code,
            adjustment_amount=adjustment_amount,
            gain_loss=event.gain_loss,
            is_long_term=event.is_long_term,
            transaction_hash=event.transaction_hash or "",
            digital_asset_address=event.digital_asset_address or "",
        )

    def _calculate_totals(self, rows: list[Form8949Row]) -> dict:
        """Calculate totals for a section"""
        total_proceeds = sum(row.proceeds for row in rows)
        total_cost_basis = sum(row.cost_basis for row in rows)
        total_adjustments = sum(row.adjustment_amount for row in rows)
        total_gain_loss = sum(row.gain_loss for row in rows)

        return {
            "total_proceeds": total_proceeds,
            "total_cost_basis": total_cost_basis,
            "total_adjustments": total_adjustments,
            "total_gain_loss": total_gain_loss,
            "row_count": len(rows),
        }

    def export_to_csv(self, form_data: dict) -> str:
        """
        Export Form 8949 to CSV format (Extended with 1099-DA columns)

        Returns:
            CSV string
        """
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Form 8949", f"Tax Year: {form_data['tax_year']}"])
        writer.writerow([])

        # Part I - Short-term
        writer.writerow([form_data["part_i"]["title"]])
        writer.writerow(
            [
                "Description",
                "Date Acquired",
                "Date Sold",
                "Proceeds",
                "Cost Basis",
                "Code",
                "Adjustment",
                "Gain/(Loss)",
                "Tx Hash (1099-DA)",
                "Wallet Addr (1099-DA)",
            ]
        )

        for row in form_data["part_i"]["rows"]:
            writer.writerow(
                [
                    row.description,
                    row.date_acquired,
                    row.date_sold,
                    f"{row.proceeds:.2f}",
                    f"{row.cost_basis:.2f}",
                    row.code,
                    f"{row.adjustment_amount:.2f}",
                    f"{row.gain_loss:.2f}",
                    row.transaction_hash,
                    row.digital_asset_address,
                ]
            )

        # Part I totals
        totals = form_data["part_i"]["totals"]
        writer.writerow(
            [
                "TOTALS",
                "",
                "",
                f"{totals['total_proceeds']:.2f}",
                f"{totals['total_cost_basis']:.2f}",
                "",
                f"{totals['total_adjustments']:.2f}",
                f"{totals['total_gain_loss']:.2f}",
                "",
                "",
            ]
        )

        writer.writerow([])

        # Part II - Long-term
        writer.writerow([form_data["part_ii"]["title"]])
        writer.writerow(
            [
                "Description",
                "Date Acquired",
                "Date Sold",
                "Proceeds",
                "Cost Basis",
                "Code",
                "Adjustment",
                "Gain/(Loss)",
                "Tx Hash (1099-DA)",
                "Wallet Addr (1099-DA)",
            ]
        )

        for row in form_data["part_ii"]["rows"]:
            writer.writerow(
                [
                    row.description,
                    row.date_acquired,
                    row.date_sold,
                    f"{row.proceeds:.2f}",
                    f"{row.cost_basis:.2f}",
                    row.code,
                    f"{row.adjustment_amount:.2f}",
                    f"{row.gain_loss:.2f}",
                    row.transaction_hash,
                    row.digital_asset_address,
                ]
            )

        # Part II totals
        totals = form_data["part_ii"]["totals"]
        writer.writerow(
            [
                "TOTALS",
                "",
                "",
                f"{totals['total_proceeds']:.2f}",
                f"{totals['total_cost_basis']:.2f}",
                "",
                f"{totals['total_adjustments']:.2f}",
                f"{totals['total_gain_loss']:.2f}",
                "",
                "",
            ]
        )

        return output.getvalue()

    def export_to_json(self, form_data: dict) -> dict:
        """Export Form 8949 to JSON format"""
        # Convert dataclasses to dicts
        part_i_rows = [asdict(row) for row in form_data["part_i"]["rows"]]
        part_ii_rows = [asdict(row) for row in form_data["part_ii"]["rows"]]

        return {
            "tax_year": form_data["tax_year"],
            "user_id": form_data["user_id"],
            "part_i": {
                "title": form_data["part_i"]["title"],
                "rows": part_i_rows,
                "totals": form_data["part_i"]["totals"],
            },
            "part_ii": {
                "title": form_data["part_ii"]["title"],
                "rows": part_ii_rows,
                "totals": form_data["part_ii"]["totals"],
            },
            "summary": form_data["summary"],
            "generated_at": form_data["generated_at"],
        }
