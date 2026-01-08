"""
Accounting System Export Adapters
Export tax data to QuickBooks, Xero, and other accounting systems
"""

import csv
import io
import logging
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AccountingSystem(str, Enum):
    """Supported accounting systems"""

    QUICKBOOKS = "quickbooks"
    XERO = "xero"
    SAGE = "sage"
    WAVE = "wave"
    FRESHBOOKS = "freshbooks"
    CSV_GENERIC = "csv_generic"  # Generic CSV format


@dataclass
class AccountingTransaction:
    """Accounting transaction record"""

    date: datetime
    description: str
    account: str
    debit: float
    credit: float
    reference: str | None = None
    category: str | None = None
    tax_code: str | None = None


class AccountingExportService:
    """
    Service for exporting tax data to accounting systems

    Features:
    - QuickBooks export (IIF format)
    - Xero export (CSV format)
    - Generic CSV export
    - Transaction mapping
    - Account code mapping
    """

    def __init__(self):
        # Account code mappings for different systems
        self.account_codes = {
            AccountingSystem.QUICKBOOKS: {
                "crypto_asset": "12000",  # Current Assets - Crypto Assets
                "capital_gains": "42000",  # Income - Capital Gains
                "capital_losses": "52000",  # Expenses - Capital Losses
                "trading_fees": "53000",  # Expenses - Trading Fees
            },
            AccountingSystem.XERO: {
                "crypto_asset": "200",  # Assets - Crypto
                "capital_gains": "400",  # Revenue - Capital Gains
                "capital_losses": "500",  # Expenses - Capital Losses
                "trading_fees": "510",  # Expenses - Trading Fees
            },
        }

    def export_to_quickbooks(
        self,
        transactions: list[dict[str, Any]],
        tax_year: int,
    ) -> str:
        """
        Export transactions to QuickBooks IIF format

        Args:
            transactions: List of transaction dictionaries
            tax_year: Tax year

        Returns:
            IIF format string
        """
        lines = []

        # IIF Header
        lines.append(
            "!TRNS\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tDOCNUM\tCLEAR\tTOPRINT\tDUEDATE\tTERMS\tPAID\tSHIPVIA\tSHIPDATE\tSUBTOTAL\tPONUM\tINVTITLE\tINVNUM\tINVDATE\tSADDR1\tSADDR2\tSADDR3\tSADDR4\tSADDR5\tSADDR6\tSCITY\tSSTATE\tSPOSTALCODE\tSCOUNTRY\tSNAME\tBADDR1\tBADDR2\tBADDR3\tBADDR4\tBADDR5\tBADDR6\tBCITY\tBSTATE\tBPOSTALCODE\tBCOUNTRY\tBNAME\tDUEDATE\tTERMS\tPAID\tSHIPVIA\tSHIPDATE\tSUBTOTAL\tPONUM\tINVTITLE\tINVNUM\tINVDATE"
        )
        lines.append(
            "!SPL\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tDOCNUM\tCLEAR\tQNTY\tPRICE\tINVITEM\tPAYMETH\tTAXABLE\tREIMBEXP\tEXTRA\tVENDOR\tNAMEISTAXKEY\tAMOUNT\tAMOUNT\t"
        )
        lines.append("!ENDTRNS")

        # Process transactions
        for tx in transactions:
            date = datetime.fromisoformat(tx.get("date", datetime.utcnow().isoformat()))
            description = tx.get("description", "Crypto Transaction")
            amount = tx.get("amount", 0.0)
            account = tx.get("account", "crypto_asset")
            account_code = self.account_codes[AccountingSystem.QUICKBOOKS].get(
                account, "12000"
            )

            # Main transaction line
            lines.append(
                f"TRNS\t\t{date.strftime('%m/%d/%Y')}\t{account_code}\t{description}\t{amount:.2f}\t\tN\tN\t\t\tN\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t"
            )

            # Split line (offsetting entry)
            offset_account = "10000"  # Cash/Bank account
            lines.append(
                f"SPL\t\t{date.strftime('%m/%d/%Y')}\t{offset_account}\t{description}\t{-amount:.2f}\t\tN\t\t\t\tN\tN\t\t\t\t\t\t\t\t"
            )

            lines.append("ENDTRNS")

        return "\n".join(lines)

    def export_to_xero(
        self,
        transactions: list[dict[str, Any]],
        tax_year: int,
    ) -> str:
        """
        Export transactions to Xero CSV format

        Args:
            transactions: List of transaction dictionaries
            tax_year: Tax year

        Returns:
            CSV format string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Xero CSV Header
        writer.writerow(
            [
                "*ContactName",
                "*InvoiceNumber",
                "*InvoiceDate",
                "*DueDate",
                "InventoryItemCode",
                "Description",
                "Quantity",
                "UnitAmount",
                "Discount",
                "AccountCode",
                "TaxType",
                "TaxAmount",
                "TrackingName1",
                "TrackingOption1",
                "TrackingName2",
                "TrackingOption2",
                "Currency",
                "Reference",
                "BrandingTheme",
            ]
        )

        # Process transactions
        for tx in transactions:
            date = datetime.fromisoformat(tx.get("date", datetime.utcnow().isoformat()))
            description = tx.get("description", "Crypto Transaction")
            amount = tx.get("amount", 0.0)
            account = tx.get("account", "crypto_asset")
            account_code = self.account_codes[AccountingSystem.XERO].get(account, "200")

            writer.writerow(
                [
                    "",  # ContactName
                    f"CRYPTO-{tx.get('id', '')}",  # InvoiceNumber
                    date.strftime("%d/%m/%Y"),  # InvoiceDate
                    date.strftime("%d/%m/%Y"),  # DueDate
                    "",  # InventoryItemCode
                    description,  # Description
                    "1",  # Quantity
                    abs(amount),  # UnitAmount
                    "0",  # Discount
                    account_code,  # AccountCode
                    "NONE",  # TaxType
                    "0",  # TaxAmount
                    "",  # TrackingName1
                    "",  # TrackingOption1
                    "",  # TrackingName2
                    "",  # TrackingOption2
                    "USD",  # Currency
                    tx.get("reference", ""),  # Reference
                    "",  # BrandingTheme
                ]
            )

        return output.getvalue()

    def export_to_csv_generic(
        self,
        transactions: list[dict[str, Any]],
        tax_year: int,
    ) -> str:
        """
        Export transactions to generic CSV format

        Args:
            transactions: List of transaction dictionaries
            tax_year: Tax year

        Returns:
            CSV format string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Generic CSV Header
        writer.writerow(
            [
                "Date",
                "Description",
                "Account",
                "Debit",
                "Credit",
                "Reference",
                "Category",
                "Tax Code",
            ]
        )

        # Process transactions
        for tx in transactions:
            date = datetime.fromisoformat(tx.get("date", datetime.utcnow().isoformat()))
            description = tx.get("description", "Crypto Transaction")
            account = tx.get("account", "crypto_asset")
            amount = tx.get("amount", 0.0)

            debit = abs(amount) if amount > 0 else 0.0
            credit = abs(amount) if amount < 0 else 0.0

            writer.writerow(
                [
                    date.strftime("%Y-%m-%d"),
                    description,
                    account,
                    f"{debit:.2f}",
                    f"{credit:.2f}",
                    tx.get("reference", ""),
                    tx.get("category", ""),
                    tx.get("tax_code", ""),
                ]
            )

        return output.getvalue()

    def convert_tax_events_to_transactions(
        self,
        tax_events: list[dict[str, Any]],
        system: AccountingSystem,
    ) -> list[dict[str, Any]]:
        """
        Convert tax events to accounting transactions

        Args:
            tax_events: List of tax event dictionaries
            system: Target accounting system

        Returns:
            List of transaction dictionaries
        """
        transactions = []

        for event in tax_events:
            sale_date = datetime.fromisoformat(
                event.get("sale_date", datetime.utcnow().isoformat())
            )
            symbol = event.get("symbol", "CRYPTO")
            quantity = event.get("quantity", 0.0)
            proceeds = event.get("proceeds", 0.0)
            cost_basis = event.get("cost_basis", 0.0)
            gain_loss = event.get("gain_loss", 0.0)

            # Sale transaction (credit proceeds)
            transactions.append(
                {
                    "date": sale_date.isoformat(),
                    "description": f"Sale of {quantity} {symbol}",
                    "account": "crypto_asset",
                    "amount": -proceeds,  # Credit (negative)
                    "reference": f"TX-{event.get('trade_id', '')}",
                    "category": "Sale",
                }
            )

            # Cost basis transaction (debit cost basis)
            transactions.append(
                {
                    "date": sale_date.isoformat(),
                    "description": f"Cost basis for {symbol} sale",
                    "account": "crypto_asset",
                    "amount": cost_basis,  # Debit (positive)
                    "reference": f"TX-{event.get('trade_id', '')}",
                    "category": "Cost Basis",
                }
            )

            # Gain/Loss transaction
            if gain_loss > 0:
                transactions.append(
                    {
                        "date": sale_date.isoformat(),
                        "description": f"Capital gain on {symbol}",
                        "account": "capital_gains",
                        "amount": -gain_loss,  # Credit (negative)
                        "reference": f"TX-{event.get('trade_id', '')}",
                        "category": "Capital Gain",
                    }
                )
            elif gain_loss < 0:
                transactions.append(
                    {
                        "date": sale_date.isoformat(),
                        "description": f"Capital loss on {symbol}",
                        "account": "capital_losses",
                        "amount": abs(gain_loss),  # Debit (positive)
                        "reference": f"TX-{event.get('trade_id', '')}",
                        "category": "Capital Loss",
                    }
                )

        return transactions

    def export(
        self,
        tax_events: list[dict[str, Any]],
        system: AccountingSystem,
        tax_year: int,
    ) -> str:
        """
        Export tax events to accounting system format

        Args:
            tax_events: List of tax event dictionaries
            system: Target accounting system
            tax_year: Tax year

        Returns:
            Exported data as string
        """
        # Convert tax events to transactions
        transactions = self.convert_tax_events_to_transactions(tax_events, system)

        # Export based on system
        if system == AccountingSystem.QUICKBOOKS:
            return self.export_to_quickbooks(transactions, tax_year)
        elif system == AccountingSystem.XERO:
            return self.export_to_xero(transactions, tax_year)
        elif system == AccountingSystem.CSV_GENERIC:
            return self.export_to_csv_generic(transactions, tax_year)
        else:
            raise ValueError(f"Unsupported accounting system: {system}")


# Global instance
accounting_export_service = AccountingExportService()
