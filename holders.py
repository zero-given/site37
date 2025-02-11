from web3 import Web3
import requests
from bs4 import BeautifulSoup

w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))

def get_holders_etherscan(token_address):
    """Direct holder count from Etherscan with corrected selector"""
    try:
        url = f"https://etherscan.io/token/{token_address}"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Target the correct anchor element for holders
        holder_element = soup.select_one('a[href*="token-holders"]')
        if holder_element:
            holders = holder_element.text.strip().replace(',', '')
            return int(holders)
        else:
            print("Etherscan Error: Holder element not found")
            return None
    except Exception as e:
        print(f"Etherscan Error: {str(e)[:80]}")
        return None

def get_holders_onchain(token_address):
    """On-chain interaction with corrected ABI and example address"""
    try:
        erc20_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"name": "", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=erc20_abi
        )
        
        total_supply = contract.functions.totalSupply().call()
        # Use a dummy address (e.g., zero address)
        dummy_address = '0x0000000000000000000000000000000000000000'
        balance = contract.functions.balanceOf(dummy_address).call()
        
        # Example estimation logic (for demonstration only)
        if balance > 0:
            return total_supply // balance
        else:
            return 0  # Avoid division by zero
    except Exception as e:
        print(f"Blockchain Error: {str(e)[:80]}")
        return None

def main():
    token_address = input("Enter ERC20 token address: ").strip().lower()
    
    print("\n=== Ethereum Holder Verification ===")
    print("Method 1: Etherscan Atomic Scrape...")
    print(f"Holders: {get_holders_etherscan(token_address) or 'N/A'}")
    
    print("\nMethod 2: On-Chain Estimation...")
    print(f"Estimated Holders: {get_holders_onchain(token_address) or 'N/A'}")

if __name__ == "__main__":
    main()