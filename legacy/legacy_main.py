import random
import time
import hashlib
from datetime import datetime

class Transaction:
    """Represents a transaction in the blockchain"""
    
    def __init__(self, sender, receiver, amount, gas_fee=0.001):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.gas_fee = gas_fee
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.tx_hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate transaction hash"""
        tx_string = f"{self.sender}{self.receiver}{self.amount}{self.timestamp}"
        return hashlib.sha256(tx_string.encode()).hexdigest()[:16]
    
    def __repr__(self):
        return (f"TX[{self.tx_hash}]: {self.sender} → {self.receiver} | "
                f"{self.amount} SHEA (fee: {self.gas_fee} SHEA)")


class Block:
    """Represents a block in the blockchain"""
    
    def __init__(self, number, transactions, validator_name, previous_hash):
        self.number = number
        self.transactions = transactions
        self.validator = validator_name
        self.previous_hash = previous_hash
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.nonce = random.randint(1000, 9999)  # Random nonce for uniqueness
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate block hash based on its contents"""
        tx_hashes = ''.join([tx.tx_hash for tx in self.transactions])
        block_string = f"{self.number}{tx_hashes}{self.validator}{self.previous_hash}{self.nonce}"
        # print(block_string)
        # print(hashlib.sha256(block_string.encode()).hexdigest())
        return hashlib.sha256(block_string.encode()).hexdigest()[:16]
    
    def get_total_fees(self):
        """Calculate total gas fees in the block"""
        return sum(tx.gas_fee for tx in self.transactions)
    
    def get_total_volume(self):
        """Calculate total transaction volume"""
        return sum(tx.amount for tx in self.transactions)
    
    def __repr__(self):
        return (f"\n{'='*70}\n"
                f"Block #{self.number} | Hash: {self.hash}\n"
                f"Previous Hash: {self.previous_hash}\n"
                f"Validator: {self.validator} | Time: {self.timestamp}\n"
                f"Transactions: {len(self.transactions)} | Volume: {self.get_total_volume():.4f} SHEA\n"
                f"{'='*70}")


class Validator:
    """Represents a validator in the Proof of Stake network"""
    
    def __init__(self, name, stake, address):
        self.name = name
        self.stake = stake
        self.address = address
        self.blocks_proposed = 0
        self.total_rewards = 0.0
        self.is_active = True
    
    def propose_block(self, block_number, transactions, previous_hash, base_reward=0.01):
        """Validator proposes a new block and earns rewards"""
        block = Block(block_number, transactions, self.name, previous_hash)
        
        # Calculate rewards: base reward + gas fees
        gas_fees = block.get_total_fees()
        total_reward = base_reward + gas_fees
        
        self.blocks_proposed += 1
        self.total_rewards += total_reward
        
        return block, total_reward
    
    def add_stake(self, amount):
        """Add more stake"""
        self.stake += amount
        print(f"✓ {self.name} added {amount} SHEA to stake. New total: {self.stake} SHEA")
    
    def __repr__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} [{status}] (Stake: {self.stake} SHEA, Address: {self.address})"


class Account:
    """Represents a user account"""
    
    def __init__(self, name, address, balance=100.0):
        self.name = name
        self.address = address
        self.balance = balance
    
    def send(self, receiver_address, amount, gas_fee=0.001):
        """Create a transaction"""
        if self.balance >= amount + gas_fee:
            self.balance -= (amount + gas_fee)
            return Transaction(self.address, receiver_address, amount, gas_fee)
        else:
            print(f"❌ Insufficient funds! Balance: {self.balance} SHEA")
            return None
    
    def receive(self, amount):
        """Receive funds"""
        self.balance += amount
    
    def __repr__(self):
        return f"Account({self.name} | {self.address}): {self.balance:.4f} SHEA"


class ProofOfStakeBlockchain:
    """Full Proof of Stake blockchain implementation"""
    
    def __init__(self, genesis_validator="Genesis"):
        self.validators = []
        self.blockchain = []
        self.pending_transactions = []
        self.accounts = {}
        self.current_block_number = 0
        
        # Create genesis block
        genesis_block = Block(0, [], genesis_validator, "0" * 16)
        self.blockchain.append(genesis_block)
        print(f"🌟 Genesis block created: {genesis_block.hash}")
    
    def create_account(self, name, initial_balance=100.0, address=None):
        """Create a new account"""
        if address is None:
            address = f"0x{hashlib.sha256(name.encode()).hexdigest()[:8]}"
            
        if address not in self.accounts:
            self.accounts[address] = Account(name, address, initial_balance)
            print(f"✓ Created account {name} ({address}) with {initial_balance} SHEA")
            return self.accounts[address]
        return self.accounts[address]
    
    def add_validator(self, name, stake, address=None):
        """Add a new validator to the network"""
        if stake < 32:
            print(f"❌ Error: Minimum stake is 32 SHEA. {name} has {stake} SHEA.")
            return None
        
        if address is None:
            address = f"0x{hashlib.sha256(name.encode()).hexdigest()[:8]}"
        
        validator = Validator(name, stake, address)
        self.validators.append(validator)
        print(f"✓ {name} joined as validator with {stake} SHEA staked")
        return validator
    
    def add_transaction(self, sender_address, receiver_address, amount, gas_fee=0.001):
        """Add a transaction to the pending pool"""
        if sender_address not in self.accounts:
            print(f"❌ Sender account {sender_address} does not exist")
            return False
        
        # Create receiver account if doesn't exist
        if receiver_address not in self.accounts:
             # Just create a placeholder account if unknown address receives funds
            self.create_account("Unknown", 0, address=receiver_address)
        
        sender = self.accounts[sender_address]
        tx = sender.send(receiver_address, amount, gas_fee)
        
        if tx:
            self.pending_transactions.append(tx)
            print(f"✓ Transaction added to mempool: {tx}")
            return True
        return False
    
    def get_total_stake(self):
        """Calculate total stake in the network"""
        return sum(v.stake for v in self.validators if v.is_active)
    
    def select_validator(self):
        """Select validator using weighted random selection"""
        active_validators = [v for v in self.validators if v.is_active]
        
        if not active_validators:
            return None
        
        total_stake = sum(v.stake for v in active_validators)
        random_value = random.uniform(0, total_stake)
        
        cumulative_stake = 0
        for validator in active_validators:
            cumulative_stake += validator.stake
            if random_value <= cumulative_stake:
                return validator
        
        return active_validators[0]
    
    def mine_block(self, max_transactions=10):
        """Select validator and create a new block with pending transactions"""
        if not self.validators:
            print("❌ No validators in the network!")
            return None
        
        if not self.pending_transactions:
            print("⚠️  No pending transactions to include in block")
            return None
        
        # Select validator
        selected_validator = self.select_validator()
        if not selected_validator:
            print("❌ No active validators available")
            return None
        
        # Get transactions for this block
        transactions_to_include = self.pending_transactions[:max_transactions]
        self.pending_transactions = self.pending_transactions[max_transactions:]
        
        # Get previous block hash
        previous_hash = self.blockchain[-1].hash
        
        # Validator proposes block
        self.current_block_number += 1
        new_block, reward = selected_validator.propose_block(
            self.current_block_number, 
            transactions_to_include, 
            previous_hash
        )
        
        # Process transactions (update account balances)
        for tx in transactions_to_include:
            if tx.receiver in self.accounts:
                self.accounts[tx.receiver].receive(tx.amount)
        
        # Add validator reward to their account
        if selected_validator.address not in self.accounts:
            self.create_account(selected_validator.name, 0, address=selected_validator.address)
        self.accounts[selected_validator.address].receive(reward)
        
        # Add block to blockchain
        self.blockchain.append(new_block)
        
        print(f"\n🎯 {selected_validator.name} selected to propose block!")
        print(new_block)
        print(f"💰 Validator reward: {reward:.6f} SHEA (base + gas fees)")
        
        # Show transactions in block
        print(f"\n📝 Transactions in this block:")
        for tx in transactions_to_include:
            print(f"  {tx}")
        
        return new_block
    
    def get_balance(self, address):
        """Get account balance"""
        if address in self.accounts:
            return self.accounts[address].balance
        return 0
    
    def verify_chain(self):
        """Verify blockchain integrity"""
        print("\n🔍 Verifying blockchain integrity...")
        
        for i in range(1, len(self.blockchain)):
            current_block = self.blockchain[i]
            previous_block = self.blockchain[i-1]
            
            # Check if previous hash matches
            if current_block.previous_hash != previous_block.hash:
                print(f"❌ Block {i} has invalid previous hash!")
                return False
            
            # Verify block hash
            if current_block.hash != current_block.calculate_hash():
                print(f"❌ Block {i} has invalid hash!")
                return False
        
        print("✅ Blockchain is valid!")
        return True
    
    def show_statistics(self):
        """Display comprehensive statistics"""
        print("\n" + "="*70)
        print("📊 BLOCKCHAIN STATISTICS")
        print("="*70)
        print(f"Total Blocks: {len(self.blockchain)}")
        print(f"Pending Transactions: {len(self.pending_transactions)}")
        print(f"Active Validators: {len([v for v in self.validators if v.is_active])}")
        print(f"Total Accounts: {len(self.accounts)}")
        
        # Calculate total volume
        total_volume = sum(block.get_total_volume() for block in self.blockchain[1:])
        print(f"Total Transaction Volume: {total_volume:.4f} SHEA")
        
        print("\n📈 VALIDATOR PERFORMANCE")
        print("-"*70)
        print(f"{'Validator':<20} {'Stake':<10} {'Blocks':<10} {'Rewards':<15}")
        print("-"*70)
        
        for validator in self.validators:
            print(f"{validator.name:<20} {validator.stake:<10} "
                  f"{validator.blocks_proposed:<10} {validator.total_rewards:<15.6f}")
        
        print("\n💼 ACCOUNT BALANCES")
        print("-"*70)
        for address, account in list(self.accounts.items())[:10]:  # Show first 10
            print(f"{account.name:<15} {address}: {account.balance:.4f} SHEA")
    
    def show_block_details(self, block_number):
        """Show detailed information about a specific block"""
        if 0 <= block_number < len(self.blockchain):
            block = self.blockchain[block_number]
            print(block)
            print(f"\n📝 Transactions ({len(block.transactions)}):")
            for tx in block.transactions:
                print(f"  {tx}")
        else:
            print(f"❌ Block {block_number} does not exist")
    
    def show_recent_blocks(self, n=5):
        """Show recent blocks"""
        print(f"\n📚 LAST {min(n, len(self.blockchain)-1)} BLOCKS")
        print("="*70)
        for block in self.blockchain[-(n+1):-1]:
            print(f"Block #{block.number} | Hash: {block.hash} | "
                  f"Validator: {block.validator} | TXs: {len(block.transactions)}")


def interactive_cli():
    """Run an interactive CLI for the blockchain"""
    print("="*70)
    print("INTERACTIVE PROOF OF STAKE BLOCKCHAIN CLI")
    print("="*70)
    
    blockchain = ProofOfStakeBlockchain()
    
    # Add some initial setup so it's not empty
    print("Initializing with Genesis Validator and Treasury...")
    blockchain.add_validator("Genesis_Validator", 32)
    blockchain.create_account("Treasury", 1000)
    
    while True:
        print("\n" + "-"*30)
        print("MAIN MENU")
        print("-" * 30)
        print("1. Create Account")
        print("2. Add Validator")
        print("3. Add Transaction")
        print("4. Mine Block")
        print("5. Show Statistics")
        print("6. Show Block Details")
        print("7. Exit")
        
        choice = input("\nEnter choice (1-7): ")
        
        if choice == '1':
            name = input("Enter account name: ")
            try:
                balance = float(input("Enter initial balance: "))
                blockchain.create_account(name, balance)
            except ValueError:
                print("❌ Invalid balance amount.")
            
        elif choice == '2':
            name = input("Enter validator name: ")
            try:
                stake = float(input("Enter stake amount (min 32): "))
                blockchain.add_validator(name, stake)
            except ValueError:
                print("❌ Invalid stake amount.")
            
        elif choice == '3':
            sender = input("Enter sender address: ")
            receiver = input("Enter receiver address: ")
            try:
                amount = float(input("Enter amount: "))
                blockchain.add_transaction(sender, receiver, amount)
            except ValueError:
                print("❌ Invalid amount.")
            
        elif choice == '4':
            blockchain.mine_block()
            
        elif choice == '5':
            blockchain.show_statistics()
            
        elif choice == '6':
            try:
                block_num = int(input("Enter block number: "))
                blockchain.show_block_details(block_num)
            except ValueError:
                print("❌ Invalid block number.")

        elif choice == '7':
            print("Exiting...")
            break
        else:
            print("❌ Invalid choice, please try again.")


if __name__ == "__main__":
    interactive_cli()