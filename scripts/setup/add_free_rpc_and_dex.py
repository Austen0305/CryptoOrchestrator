#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add Free Blockchain RPC URLs and DEX Aggregator Configuration to .env file
Uses only free public resources - no API keys required
"""

import os
import sys
from pathlib import Path

# Free public RPC endpoints (no API key required)
FREE_RPC_ENDPOINTS = {
    "ETHEREUM_RPC_URL": [
        "https://eth.llamarpc.com",  # LlamaNodes (free, reliable)
        "https://rpc.ankr.com/eth",  # Ankr (free tier)
        "https://ethereum.publicnode.com",  # PublicNode (free)
        "https://eth-mainnet.public.blastapi.io",  # BlastAPI (free tier)
    ],
    "BASE_RPC_URL": [
        "https://mainnet.base.org",  # Base official (free)
        "https://base.publicnode.com",  # PublicNode (free)
        "https://base-rpc.publicnode.com",  # PublicNode alternative
    ],
    "ARBITRUM_RPC_URL": [
        "https://arb1.arbitrum.io/rpc",  # Arbitrum official (free)
        "https://arbitrum.publicnode.com",  # PublicNode (free)
        "https://arbitrum-one.public.blastapi.io",  # BlastAPI (free tier)
    ],
    "POLYGON_RPC_URL": [
        "https://polygon-rpc.com",  # Polygon official (free, rate-limited)
        "https://polygon.publicnode.com",  # PublicNode (free)
        "https://polygon-rpc.publicnode.com",  # PublicNode alternative
        "https://polygon-mainnet.public.blastapi.io",  # BlastAPI (free tier)
    ],
    "OPTIMISM_RPC_URL": [
        "https://mainnet.optimism.io",  # Optimism official (free)
        "https://optimism.publicnode.com",  # PublicNode (free)
        "https://optimism-rpc.publicnode.com",  # PublicNode alternative
    ],
    "AVALANCHE_RPC_URL": [
        "https://api.avax.network/ext/bc/C/rpc",  # Avalanche official (free)
        "https://avalanche.publicnode.com",  # PublicNode (free)
        "https://avalanche-c-chain-rpc.publicnode.com",  # PublicNode alternative
    ],
    "BNB_CHAIN_RPC_URL": [
        "https://bsc-dataseed.binance.org",  # Binance official (free, rate-limited)
        "https://bsc-dataseed1.defibit.io",  # Defibit (free)
        "https://bsc.publicnode.com",  # PublicNode (free)
        "https://bsc-rpc.publicnode.com",  # PublicNode alternative
    ],
}

# Free DEX Aggregator options (no API key required for basic usage)
FREE_DEX_AGGREGATORS = {
    # 0x Protocol - Free tier available, but can work without API key for basic usage
    "ZEROX_API_KEY": "",  # Leave empty - will use public endpoints
    
    # 1inch - Free tier, but can work without API key for basic usage
    "ONEINCH_API_KEY": "",  # Leave empty - will use public endpoints
    
    # Paraswap - Free tier, but can work without API key for basic usage
    "PARASWAP_API_KEY": "",  # Leave empty - will use public endpoints
}

def read_env_file(env_path: Path) -> list:
    """Read existing .env file and return lines"""
    if not env_path.exists():
        return []
    
    with open(env_path, "r", encoding="utf-8") as f:
        return f.readlines()

def write_env_file(env_path: Path, lines: list):
    """Write lines to .env file"""
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def add_rpc_urls_to_env(env_path: Path):
    """Add free RPC URLs to .env file"""
    lines = read_env_file(env_path)
    
    # Find where to insert RPC URLs (after Blockchain RPC URLs comment)
    insert_index = -1
    for i, line in enumerate(lines):
        if "# Blockchain RPC URLs" in line or "# Blockchain RPC" in line:
            insert_index = i
            break
    
    # If comment not found, find end of file
    if insert_index == -1:
        insert_index = len(lines)
        # Add comment section
        lines.append("\n")
        lines.append("# ==========================================\n")
        lines.append("# Blockchain RPC URLs (Free Public Endpoints)\n")
        lines.append("# ==========================================\n")
        insert_index = len(lines)
    
    # Check which RPC URLs are already set
    existing_rpc = {}
    for i, line in enumerate(lines):
        for key in FREE_RPC_ENDPOINTS.keys():
            if line.strip().startswith(f"{key}="):
                existing_rpc[key] = i
                break
    
    # Add or update RPC URLs
    new_lines = []
    for key, urls in FREE_RPC_ENDPOINTS.items():
        if key in existing_rpc:
            # Update existing line
            lines[existing_rpc[key]] = f"{key}={urls[0]}\n"
        else:
            # Add new line (use first URL as primary)
            new_lines.append(f"{key}={urls[0]}\n")
            # Add comment with alternatives
            if len(urls) > 1:
                new_lines.append(f"# Alternative: {key}_ALT={urls[1]}\n")
    
    # Insert new lines after the comment section
    if new_lines:
        # Find the end of the RPC section
        rpc_section_end = insert_index
        for i in range(insert_index, len(lines)):
            if lines[i].strip() and not lines[i].strip().startswith("#") and "RPC_URL" not in lines[i]:
                rpc_section_end = i
                break
        else:
            rpc_section_end = len(lines)
        
        # Insert new lines
        lines[rpc_section_end:rpc_section_end] = new_lines
    
    # Add RPC provider type
    if not any("RPC_PROVIDER_TYPE" in line for line in lines):
        lines.append("RPC_PROVIDER_TYPE=public\n")
    
    write_env_file(env_path, lines)
    print("[OK] Added free blockchain RPC URLs to .env file")

def add_dex_aggregators_to_env(env_path: Path):
    """Add DEX aggregator configuration to .env file"""
    lines = read_env_file(env_path)
    
    # Find where to insert DEX config (after DEX Trading Configuration comment)
    insert_index = -1
    for i, line in enumerate(lines):
        if "# DEX Trading Configuration" in line or "# DEX Trading" in line:
            insert_index = i
            break
    
    # If comment not found, find end of file
    if insert_index == -1:
        insert_index = len(lines)
        # Add comment section
        lines.append("\n")
        lines.append("# ==========================================\n")
        lines.append("# DEX Trading Configuration (Free Public Endpoints)\n")
        lines.append("# ==========================================\n")
        insert_index = len(lines)
    
    # Check which DEX configs are already set
    existing_dex = {}
    for i, line in enumerate(lines):
        for key in FREE_DEX_AGGREGATORS.keys():
            if line.strip().startswith(f"{key}="):
                existing_dex[key] = i
                break
    
    # Add or update DEX aggregator configs
    new_lines = []
    for key, value in FREE_DEX_AGGREGATORS.items():
        if key in existing_dex:
            # Keep existing if set, otherwise update to empty
            if not lines[existing_dex[key]].split("=", 1)[1].strip():
                lines[existing_dex[key]] = f"{key}={value}\n"
        else:
            # Add new line
            new_lines.append(f"{key}={value}\n")
    
    # Insert new lines after the comment section
    if new_lines:
        # Find the end of the DEX section
        dex_section_end = insert_index
        for i in range(insert_index, len(lines)):
            if lines[i].strip() and not lines[i].strip().startswith("#") and not any(k in lines[i] for k in FREE_DEX_AGGREGATORS.keys()):
                if "RPC_URL" not in lines[i] or i > insert_index + 20:  # Don't go too far
                    dex_section_end = i
                    break
        else:
            dex_section_end = len(lines)
        
        # Insert new lines
        lines[dex_section_end:dex_section_end] = new_lines
    
    # Add comment about free usage
    if not any("# Free DEX aggregators work without API keys" in line for line in lines):
        comment_index = insert_index + 1
        lines.insert(comment_index, "# Free DEX aggregators work without API keys for basic usage\n")
        lines.insert(comment_index + 1, "# For higher rate limits, sign up for free API keys at:\n")
        lines.insert(comment_index + 2, "# - 0x: https://0x.org/docs/api\n")
        lines.insert(comment_index + 3, "# - 1inch: https://1inch.dev/\n")
        lines.insert(comment_index + 4, "# - Paraswap: https://developers.paraswap.network/\n")
    
    write_env_file(env_path, lines)
    print("[OK] Added free DEX aggregator configuration to .env file")

def main():
    """Main entry point"""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("[ERROR] .env file not found. Please run 'python scripts/setup/create_env_file.py' first.")
        sys.exit(1)
    
    print("Adding free blockchain RPC URLs and DEX aggregator configuration...")
    print("Using only free public resources (no API keys required)")
    
    add_rpc_urls_to_env(env_path)
    add_dex_aggregators_to_env(env_path)
    
    print("\n[OK] Configuration complete!")
    print("\nAdded RPC URLs for:")
    for chain in FREE_RPC_ENDPOINTS.keys():
        print(f"   - {chain.replace('_RPC_URL', '').title()}")
    
    print("\nDEX Aggregators configured:")
    print("   - 0x Protocol (public endpoints)")
    print("   - 1inch (public endpoints)")
    print("   - Paraswap (public endpoints)")
    
    print("\nNote: These are free public endpoints with rate limits.")
    print("   For production use, consider getting free API keys for higher limits:")
    print("   - 0x: https://0x.org/docs/api")
    print("   - 1inch: https://1inch.dev/")
    print("   - Paraswap: https://developers.paraswap.network/")
    
    print("\n[OK] Your .env file has been updated with free RPC URLs and DEX aggregator config!")

if __name__ == "__main__":
    main()

