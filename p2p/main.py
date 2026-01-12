import sys
import time
import argparse
import json
import os
from node import Node
import utils

# Wallet file path
WALLET_FILE = "my_wallet.json"

def print_header():
    print("\n" + "="*60)
    print("      P2P PoS BLOCKCHAIN NODE      ")
    print("="*60)

def save_wallet(name, address, public_key, private_key):
    data = {
        "name": name,
        "address": address,
        "public_key": utils.serialize_key(public_key),
        "private_key": utils.serialize_key(private_key)
    }
    with open(f"{name}_wallet.json", "w") as f:
        json.dump(data, f)
    print(f"✓ Wallet saved to {name}_wallet.json")

def load_wallet(name):
    filename = f"{name}_wallet.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
            data['public_key'] = utils.deserialize_key(data['public_key'])
            data['private_key'] = utils.deserialize_key(data['private_key'])
            return data
    return None

def main():
    parser = argparse.ArgumentParser(description="P2P Blockchain Node")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--peer", help="Bootstrap peer (host:port) to connect to")
    
    args = parser.parse_args()
    
    bootstrap_node = None
    if args.peer:
        try:
            phost, pport = args.peer.split(":")
            bootstrap_node = (phost, int(pport))
        except:
            print("Invalid peer format. Use host:port")
            return

    # Real-time event handler
    def on_node_event(event_type, data):
        if event_type == "CHAIN_SYNC":
            print(f"\n\n[⚡] Chain Synchronized! (Total Blocks: {data['blocks']})")
            print("Select Option: ", end="", flush=True)

    node = Node(args.host, args.port, bootstrap_node, on_event=on_node_event)
    
    current_wallet = None

    while True:
        try:
            print_header()
            info = node.get_info()
            print(f"Node: {node.node_id}")
            print(f"Blocks: {info['blocks']} | Peers: {info['peers']} | Pending Tx: {info['pending_txs']}")
            print("-" * 60)
            
            if current_wallet:
                print(f"🔓 Logged in as: {current_wallet['name']} ({current_wallet['address'][:10]}...)")
            else:
                print("🔒 Not Logged In")
            
            print("-" * 60)
            print("1. Create New Wallet (Generate Keys)")
            print("2. Login (Load Wallet File)")
            print("3. Create/Manage Validator")
            print("4. Wallet Dashboard (Send/Receive)")
            print("5. View Blockchain")
            print("6. Connect to Peer")
            print("7. Exit")
            print("-" * 60)
            
            choice = input("Select Option: ")
            
            if choice == '1':
                name = input("Enter Wallet Name: ")
                print("Generating SECP256k1 Keypair (this might take a second)...")
                pub, priv = utils.generate_keys()
                # Create account on blockchain
                # Default balance is 0. We will request Faucet.
                acc = node.blockchain.create_account(name, public_key=pub)
                
                # Save keys locally
                save_wallet(name, acc.address, pub, priv)
                current_wallet = {
                    "name": name, 
                    "address": acc.address, 
                    "public_key": pub, 
                    "private_key": priv
                }
                print(f"\n✓ Wallet Created!")
                print(f"  Address: {acc.address}")
                
                # Trigger Faucet Transaction
                print("💧 Requesting 100 SHEA from Faucet...")
                node.request_faucet(acc.address)
                print("  (Wait for next block to see balance)")
                
                input("Press Enter...")

            elif choice == '2':
                name = input("Enter Wallet Name to load: ")
                w_data = load_wallet(name)
                if w_data:
                    current_wallet = w_data
                    # Ensure account exists in local state (it might be new to this node if just loaded file)
                    if current_wallet['address'] not in node.blockchain.accounts:
                        # Create generic account entry if not found, but preserve keys
                        node.blockchain.create_account(
                            current_wallet['name'], 
                            address=current_wallet['address'],
                            public_key=current_wallet['public_key']
                        )
                    print(f"✓ Loaded wallet {name}")
                else:
                    print(f"❌ Wallet file {name}_wallet.json not found.")
                time.sleep(1)

            elif choice == '3':
                name = input("Enter Validator Name: ")
                val = None
                for v in node.blockchain.validators:
                    if v.name == name:
                        val = v
                        break
                
                if val:
                    print(f"Welcome back, Validator {val.name}")
                else:
                    try:
                        stake = float(input("Initial Stake (min 32): "))
                        
                        print("\n--- Attach Reward Wallet ---")
                        print("1. Use Current Logged In Wallet")
                        print("2. Paste Address")
                        w_choice = input("Choice: ")
                        
                        reward_addr = None
                        if w_choice == '1' and current_wallet:
                            reward_addr = current_wallet['address']
                        elif w_choice == '2':
                            reward_addr = input("Enter Wallet Address: ")
                        else:
                            print("Invalid choice or not logged in.")
                            continue
                        
                        val = node.create_validator(name, stake, reward_addr)
                        if val:
                            print(f"Validator {name} created!")
                        else:
                            print("❌ Failed to create validator.")
                            continue
                    except ValueError:
                        print("Invalid input")
                        continue

                while True:
                    print(f"\n--- Validator: {val.name} (Stake: {val.stake}) ---")
                    print(f"Reward Address: {val.reward_address}")
                    print("1. Try to Mine Block")
                    print("2. Back")
                    sub = input("Select: ")
                    
                    if sub == '1':
                        block = node.mine()
                        if block:
                            if block.validator == val.name:
                                print(f"🎉 You mined Block #{block.number}!")
                                print(f"   Rewards sent to {val.reward_address}")
                            else:
                                print(f"Block mined by {block.validator}")
                        else:
                            print("Mining returned no block (no txs or not selected).")
                    elif sub == '2':
                        break

            elif choice == '4':
                if not current_wallet:
                    print("❌ Please Login First (Option 2)")
                    time.sleep(1)
                    continue
                
                # Fetch fresh balance
                addr = current_wallet['address']
                if addr in node.blockchain.accounts:
                    bal = node.blockchain.accounts[addr].balance
                else:
                    bal = 0.0

                while True:
                    print(f"\n--- Wallet: {current_wallet['name']} ---")
                    print(f"Address: {addr}")
                    print(f"Balance: {bal:.4f} SHEA")
                    print("-" * 30)
                    print("1. Send Transaction")
                    print("2. Refresh")
                    print("3. Back")
                    sub = input("Select: ")
                    
                    if sub == '1':
                        recv = input("Receiver Addr: ")
                        try:
                            amt = float(input("Amount: "))
                            # Pass private key for signing
                            if node.send_transaction(addr, recv, amt, current_wallet['private_key']):
                                print("✓ Transaction Signed & Broadcasted!")
                            else:
                                print("❌ Transaction failed (Insufficient funds or Invalid Signature).")
                        except ValueError:
                            print("Invalid amount")
                    elif sub == '2':
                        if addr in node.blockchain.accounts:
                            bal = node.blockchain.accounts[addr].balance
                    elif sub == '3':
                        break

            elif choice == '5':
                for b in node.blockchain.blockchain[-5:]:
                    print(b)
                input("\nPress Enter...")

            elif choice == '6':
                p = input("Enter peer host:port : ")
                try:
                    h, po = p.split(":")
                    node.connect_to_peer(h, int(po))
                except:
                    print("Invalid format")

            elif choice == '7':
                node.running = False
                print("Shutting down...")
                sys.exit()

        except KeyboardInterrupt:
            node.running = False
            print("\nShutting down...")
            sys.exit()

if __name__ == "__main__":
    main()