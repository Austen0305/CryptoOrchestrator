"""
Multi-Jurisdiction Tax Support
Tax calculation and reporting for different countries
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Jurisdiction(str, Enum):
    """Supported tax jurisdictions"""

    US = "US"  # United States
    UK = "UK"  # United Kingdom
    CA = "CA"  # Canada
    AU = "AU"  # Australia
    DE = "DE"  # Germany
    FR = "FR"  # France
    JP = "JP"  # Japan
    SG = "SG"  # Singapore
    CH = "CH"  # Switzerland
    NL = "NL"  # Netherlands


@dataclass
class TaxRule:
    """Tax rules for a jurisdiction"""

    jurisdiction: Jurisdiction
    long_term_threshold_days: int  # Days for long-term classification
    short_term_rate: float  # Short-term capital gains tax rate (%)
    long_term_rate: float  # Long-term capital gains tax rate (%)
    tax_free_threshold: float  # Tax-free threshold (in local currency)
    wash_sale_period_days: int  # Wash sale detection period
    supports_loss_carryforward: bool  # Can losses be carried forward
    loss_carryforward_years: int  # Years losses can be carried forward
    currency: str  # Local currency code
    tax_year_start: str  # Tax year start date (MM-DD format)
    tax_year_end: str  # Tax year end date (MM-DD format)


class MultiJurisdictionTaxService:
    """
    Multi-jurisdiction tax calculation service

    Features:
    - Country-specific tax rules
    - Different holding period thresholds
    - Jurisdiction-specific tax rates
    - Tax year calculations
    - Loss carryforward rules
    """

    def __init__(self):
        self.tax_rules: dict[Jurisdiction, TaxRule] = {
            Jurisdiction.US: TaxRule(
                jurisdiction=Jurisdiction.US,
                long_term_threshold_days=365,
                short_term_rate=37.0,  # Top marginal rate
                long_term_rate=20.0,  # Top long-term rate
                tax_free_threshold=0.0,
                wash_sale_period_days=30,
                supports_loss_carryforward=True,
                loss_carryforward_years=3,
                currency="USD",
                tax_year_start="01-01",
                tax_year_end="12-31",
            ),
            Jurisdiction.UK: TaxRule(
                jurisdiction=Jurisdiction.UK,
                long_term_threshold_days=365,
                short_term_rate=20.0,  # Capital gains tax rate
                long_term_rate=20.0,
                tax_free_threshold=12300.0,  # Annual CGT allowance (GBP)
                wash_sale_period_days=30,
                supports_loss_carryforward=True,
                loss_carryforward_years=4,
                currency="GBP",
                tax_year_start="04-06",  # UK tax year starts April 6
                tax_year_end="04-05",
            ),
            Jurisdiction.CA: TaxRule(
                jurisdiction=Jurisdiction.CA,
                long_term_threshold_days=365,
                short_term_rate=50.0,  # 50% of gain is taxable at marginal rate
                long_term_rate=50.0,
                tax_free_threshold=0.0,
                wash_sale_period_days=30,
                supports_loss_carryforward=True,
                loss_carryforward_years=3,
                currency="CAD",
                tax_year_start="01-01",
                tax_year_end="12-31",
            ),
            Jurisdiction.AU: TaxRule(
                jurisdiction=Jurisdiction.AU,
                long_term_threshold_days=365,
                short_term_rate=45.0,  # Top marginal rate
                long_term_rate=45.0,
                tax_free_threshold=0.0,
                wash_sale_period_days=30,
                supports_loss_carryforward=True,
                loss_carryforward_years=5,
                currency="AUD",
                tax_year_start="07-01",  # Australian tax year starts July 1
                tax_year_end="06-30",
            ),
            Jurisdiction.DE: TaxRule(
                jurisdiction=Jurisdiction.DE,
                long_term_threshold_days=365,
                short_term_rate=26.375,  # Abgeltungssteuer (flat tax)
                long_term_rate=26.375,
                tax_free_threshold=801.0,  # Sparer-Pauschbetrag (EUR)
                wash_sale_period_days=0,  # No wash sale rules in Germany
                supports_loss_carryforward=True,
                loss_carryforward_years=2,
                currency="EUR",
                tax_year_start="01-01",
                tax_year_end="12-31",
            ),
            Jurisdiction.SG: TaxRule(
                jurisdiction=Jurisdiction.SG,
                long_term_threshold_days=0,  # No capital gains tax in Singapore
                short_term_rate=0.0,
                long_term_rate=0.0,
                tax_free_threshold=0.0,
                wash_sale_period_days=0,
                supports_loss_carryforward=False,
                loss_carryforward_years=0,
                currency="SGD",
                tax_year_start="01-01",
                tax_year_end="12-31",
            ),
        }

    def get_tax_rule(self, jurisdiction: Jurisdiction) -> TaxRule:
        """Get tax rules for a jurisdiction"""
        if jurisdiction not in self.tax_rules:
            raise ValueError(f"Unsupported jurisdiction: {jurisdiction}")
        return self.tax_rules[jurisdiction]

    def calculate_tax_year(self, date: datetime, jurisdiction: Jurisdiction) -> int:
        """
        Calculate tax year for a given date and jurisdiction

        Args:
            date: Date to calculate tax year for
            jurisdiction: Tax jurisdiction

        Returns:
            Tax year (e.g., 2024)
        """
        rule = self.get_tax_rule(jurisdiction)

        # Parse tax year start (MM-DD)
        start_month, start_day = map(int, rule.tax_year_start.split("-"))

        # Create tax year start date for current year
        tax_year_start = datetime(date.year, start_month, start_day)

        # If date is before tax year start, use previous year
        if date < tax_year_start:
            return date.year - 1

        return date.year

    def is_long_term(
        self,
        purchase_date: datetime,
        sale_date: datetime,
        jurisdiction: Jurisdiction,
    ) -> bool:
        """
        Determine if a holding is long-term based on jurisdiction rules

        Args:
            purchase_date: Purchase date
            sale_date: Sale date
            jurisdiction: Tax jurisdiction

        Returns:
            True if long-term, False otherwise
        """
        rule = self.get_tax_rule(jurisdiction)
        holding_days = (sale_date - purchase_date).days
        return holding_days >= rule.long_term_threshold_days

    def calculate_tax_liability(
        self,
        gain_loss: float,
        is_long_term: bool,
        jurisdiction: Jurisdiction,
        tax_year: int | None = None,
    ) -> dict[str, Any]:
        """
        Calculate tax liability for a gain/loss

        Args:
            gain_loss: Gain or loss amount
            is_long_term: Whether it's a long-term holding
            jurisdiction: Tax jurisdiction
            tax_year: Optional tax year for calculations

        Returns:
            Dictionary with tax calculation details
        """
        rule = self.get_tax_rule(jurisdiction)

        # Apply tax-free threshold
        taxable_amount = gain_loss
        if gain_loss > 0 and rule.tax_free_threshold > 0:
            taxable_amount = max(0, gain_loss - rule.tax_free_threshold)

        # Select tax rate
        if is_long_term:
            tax_rate = rule.long_term_rate
        else:
            tax_rate = rule.short_term_rate

        # Calculate tax (only on gains)
        if taxable_amount > 0:
            tax_amount = taxable_amount * (tax_rate / 100.0)
        else:
            tax_amount = 0.0

        return {
            "jurisdiction": jurisdiction.value,
            "gain_loss": gain_loss,
            "taxable_amount": taxable_amount,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "is_long_term": is_long_term,
            "tax_free_threshold": rule.tax_free_threshold,
            "currency": rule.currency,
            "tax_year": tax_year,
        }

    def get_tax_year_range(
        self,
        tax_year: int,
        jurisdiction: Jurisdiction,
    ) -> tuple[datetime, datetime]:
        """
        Get tax year date range

        Args:
            tax_year: Tax year
            jurisdiction: Tax jurisdiction

        Returns:
            Tuple of (start_date, end_date)
        """
        rule = self.get_tax_rule(jurisdiction)

        # Parse tax year start and end
        start_month, start_day = map(int, rule.tax_year_start.split("-"))
        end_month, end_day = map(int, rule.tax_year_end.split("-"))

        # Calculate dates
        if start_month > end_month or (
            start_month == end_month and start_day > end_day
        ):
            # Tax year spans two calendar years (e.g., UK: Apr 6 - Apr 5)
            start_date = datetime(tax_year, start_month, start_day)
            end_date = datetime(tax_year + 1, end_month, end_day)
        else:
            # Tax year within one calendar year
            start_date = datetime(tax_year, start_month, start_day)
            end_date = datetime(tax_year, end_month, end_day)

        return (start_date, end_date)

    def get_supported_jurisdictions(self) -> list[dict[str, Any]]:
        """Get list of supported jurisdictions with their tax rules"""
        jurisdictions = []
        for jurisdiction, rule in self.tax_rules.items():
            jurisdictions.append(
                {
                    "code": jurisdiction.value,
                    "name": jurisdiction.name,
                    "currency": rule.currency,
                    "long_term_threshold_days": rule.long_term_threshold_days,
                    "short_term_rate": rule.short_term_rate,
                    "long_term_rate": rule.long_term_rate,
                    "tax_free_threshold": rule.tax_free_threshold,
                    "tax_year_start": rule.tax_year_start,
                    "tax_year_end": rule.tax_year_end,
                }
            )
        return jurisdictions


# Global instance
multi_jurisdiction_tax_service = MultiJurisdictionTaxService()
