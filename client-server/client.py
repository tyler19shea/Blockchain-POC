import xmlrpc.client
import sys
import os
import time

# --- Helper Functions ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("="*70)
    print("      BLOCKCHAIN INTERFACE      ")
    print("="*70)

def connect_server(host='localhost', port=8000):
    try:
        server = xmlrpc.client.ServerProxy(f'http://{host}:{port}')
        server.system.listMethods() # Test connection
        return server
    except ConnectionRefusedError:
        return None

# --- Menus ---

def wallet_dashboard(server, account_name):
    """Dashboard for a Standard Wallet User"""
    while True:
        # Refresh account data
        account = server.get_account_by_name(account_name)
        if not account:
            print(f"❌ Error: Account {account_name} not found.")
            time.sleep(2)
            return

        clear_screen()
        print_header()
        print(f"👤 USER: {account['name']}")
        print(f"📍 ADDR: {account['address']}")
        print(f"💰 BAL : {account['balance']:.4f} SHEA")
        print("-" * 70)
        print("1. Send Transaction")
        print("2. Refresh Balance")
        print("3. View Latest Blocks")
        print("4. Logout")
        print("-" * 70)

        choice = input("Select Option: ")

        if choice == '1':
            receiver = input("\nEnter receiver address: ")
            try:
                amount = float(input("Enter amount to send: "))
                if server.add_transaction(account['address'], receiver, amount):
                    print("✓ Transaction sent to mempool!")
                else:
                    print("❌ Transaction failed (Insufficient funds or invalid address).")
            except ValueError:
                print("❌ Invalid amount.")
            input("\nPress Enter to continue...")

        elif choice == '2':
            print("Refreshing...")
            time.sleep(0.5)

        elif choice == '3':
            stats = server.get_stats()
            total_blocks = stats['total_blocks']
            start = max(0, total_blocks - 5)
            print(f"\nLast 5 Blocks:")
            for i in range(start, total_blocks):
                b = server.get_block(i)
                print(f"[{i}] Hash: {b['hash'][:10]}... | Tx: {len(b['transactions'])}")
            input("\nPress Enter to continue...")

        elif choice == '4':
            return # Back to main menu

def validator_dashboard(server, validator_name):
    """Dashboard for a Validator"""
    while True:
        # Refresh validator data
        val = server.get_validator_by_name(validator_name)
        if not val:
            print(f"❌ Error: Validator {validator_name} not found.")
            time.sleep(2)
            return

        clear_screen()
        print_header()
        print(f"🛡️ VALIDATOR: {val['name']}")
        print(f"📍 ADDR     : {val['address']}")
        print(f"⚖️ STAKE    : {val['stake']:.2f} SHEA")
        print(f"🏆 REWARDS  : {val['total_rewards']:.6f} SHEA")
        print(f"🧱 BLOCKS   : {val['blocks_proposed']}")
        print("-" * 70)
        print("1. Mine Block (Propose)")
        print("2. Stake More SHEA")
        print("3. Network Stats")
        print("4. Logout")
        print("-" * 70)

        choice = input("Select Option: ")

        if choice == '1':
            print("\nAttempting to mine block...")
            # In a real system, the protocol selects the validator.
            # Here, we trigger the mining process on the server.
            # If this validator is selected by the random algorithm, they get the reward.
            block = server.mine_block()
            
            if block:
                print(f"\n✓ New Block Mined! (Block #{block['number']})")
                print(f"  Validator: {block['validator']}")
                if block['validator'] == validator_name:
                    print("  🎉 YOU were selected to propose this block! Reward received.")
                else:
                    print(f"  (Validator '{block['validator']}' was selected this time)")
            else:
                print("❌ Mining failed (No transactions pending or network error).")
            input("\nPress Enter to continue...")

        elif choice == '2':
            print("\nTo add stake, you would typically send a transaction to the staking contract.")
            print("(Feature simplified for this demo: contact admin/server console)")
            input("\nPress Enter to continue...")

        elif choice == '3':
            stats = server.get_stats()
            print(f"\nNetwork Status:")
            print(f"  Pending Txs: {stats['pending_txs']}")
            print(f"  Active Validators: {stats['active_validators']}")
            print(f"  Total Blocks: {stats['total_blocks']}")
            input("\nPress Enter to continue...")

        elif choice == '4':
            return # Back to main menu


# --- Main Entry Point ---

def main():
    server = connect_server()
    if not server:
        print("❌ Could not connect to Blockchain Node (localhost:8000).")
        print("   Please ensure 'server.py' is running in another terminal.")
        return

    while True:
        clear_screen()
        print_header()
        print("1. 🆕 Create New Wallet")
        print("2. 🛡️ Create New Validator")
        print("3. 🔑 Login to Wallet")
        print("4. 🔐 Login as Validator")
        print("5. ❌ Exit")
        print("-" * 70)
        
        choice = input("Select Option: ")

        if choice == '1':
            name = input("\nEnter unique username: ")
            try:
                bal = float(input("Enter initial balance (e.g. 100): "))
                acc = server.create_account(name, bal)
                print(f"\n✓ Wallet created for {name}!")
                print(f"  Address: {acc['address']}")
                input("Press Enter to login...")
                wallet_dashboard(server, name)
            except ValueError:
                print("Invalid input.")
                time.sleep(1)

        elif choice == '2':
            name = input("\nEnter unique validator name: ")
            try:
                stake = float(input("Enter stake amount (min 32 SHEA): "))
                val = server.add_validator(name, stake)
                if val:
                    print(f"\n✓ Validator node initialized for {name}!")
                    input("Press Enter to login...")
                    validator_dashboard(server, name)
                else:
                    print("\n❌ Failed to create validator (Check minimum stake).")
                    time.sleep(2)
            except ValueError:
                print("Invalid input.")
                time.sleep(1)

        elif choice == '3':
            name = input("\nEnter wallet username: ")
            acc = server.get_account_by_name(name)
            if acc:
                wallet_dashboard(server, name)
            else:
                print("❌ Account not found.")
                time.sleep(1.5)

        elif choice == '4':
            name = input("\nEnter validator name: ")
            val = server.get_validator_by_name(name)
            if val:
                validator_dashboard(server, name)
            else:
                print("❌ Validator not found.")
                time.sleep(1.5)

        elif choice == '5':
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()