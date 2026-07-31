import re

wallet_patterns = {
    "Bitcoin": r"\b(?:bc1[a-zA-HJ-NP-Z0-9]{25,87}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b",
    "Ethereum": r"\b0x[a-fA-F0-9]{40}\b",
    "Tron": r"\bT[A-Za-z0-9]{33}\b",
    "Litecoin": r"\b(?:ltc1[a-z0-9]{39,59}|[LM3][a-km-zA-HJ-NP-Z1-9]{26,33})\b",
    "Dogecoin": r"\bD[5-9A-HJ-NP-Ua-km-z]{33}\b",
    "Ripple": r"\br[1-9A-HJ-NP-Za-km-z]{24,34}\b",
    "Solana": r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b",
}

upi_pattern = r"\b[a-zA-Z0-9._-]{2,256}@[a-zA-Z]{2,64}\b"

tx_patterns = {
    "Crypto_TX": r"\b0x[a-fA-F0-9]{64}\b",
    "UPI_Ref": r"\b\d{12}\b",
}

text = """
Send payment to

bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh

0x742d35Cc6634C0532925a3b844Bc454e4438f44e

TQn9Y2khEsLJW1ChVWFMS8K4nA4tW9B9K2

abc@ybl

UPI Ref : 123456789012
"""

print("Wallet Addresses")
for coin, pattern in wallet_patterns.items():
    result = re.findall(pattern, text)
    if result:
        print(f"{coin}: {result}")

upi = re.findall(upi_pattern, text)
print("\nUPI IDs:", upi)

print("\nTransaction IDs")
for name, pattern in tx_patterns.items():
    result = re.findall(pattern, text)
    if result:
        print(f"{name}: {result}")