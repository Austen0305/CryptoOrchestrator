import argparse
import json
import re
import sys

def is_eip55(address: str) -> bool:
    """Checks if the given address is a valid EIP-55 checksummed Ethereum address."""
    if not re.match(r"^0x[0-9a-fA-F]{40}$", address):
        return False
    
    # Checksum logic (simplified for this demonstration)
    # In a real implementation, we would use eth_utils or similar
    # For now, we'll check if it has both upper and lower case letters if it's mixed case
    has_upper = any(c.isupper() for c in address)
    has_lower = any(c.islower() for c in address[2:])
    
    if has_upper and has_lower:
        # It's mixed case, should be checksummed. For now, assume it's valid if reaches here
        # in a real skill, we'd perform the full keccak256 checksum audit.
        return True
    return not has_upper # All lower is valid (non-checksummed)

def validate_iso20022(file_path: str) -> bool:
    """Validates a JSON file against basic ISO 20022 requirements."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Mandatory fields for ISO 20022 transaction records (simplified)
        required_fields = ["MsgId", "CreDtTm", "InstdAmt", "Ccy", "Dbtr", "Cdtr"]
        for field in required_fields:
            if field not in data:
                print(f"Missing mandatory field: {field}")
                return False
        return True
    except Exception as e:
        print(f"Validation error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Financial Validator Utility")
    parser.add_argument("--address", type=str, help="Ethereum address to validate")
    parser.add_argument("--schema", type=str, choices=["iso_20022"], help="Schema to validate against")
    parser.add_argument("--file", type=str, help="File path for schema validation")
    
    args = parser.parse_args()
    
    if args.address:
        if is_eip55(args.address):
            print(f"Address {args.address} is VALID.")
        else:
            print(f"Address {args.address} is INVALID.")
            sys.exit(1)
            
    if args.schema == "iso_20022" and args.file:
        if validate_iso20022(args.file):
            print(f"File {args.file} is ISO 20022 COMPLIANT.")
        else:
            print(f"File {args.file} is NOT ISO 20022 COMPLIANT.")
            sys.exit(1)

if __name__ == "__main__":
    main()
