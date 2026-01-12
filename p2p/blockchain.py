import random
import time
import hashlib
import json
import utils
from datetime import datetime

class Transaction:
    """Represents a transaction in the blockchain"""
    
    def __init__(self, sender, receiver, amount, gas_fee=0.001, timestamp=None, tx_hash=None, signature=None):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.gas_fee = gas_fee
        self.timestamp = timestamp if timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.tx_hash = tx_hash if tx_hash else self.calculate_hash()
        self.signature = signature
    
    def calculate_hash(self):
        """Calculate transaction hash"""
        tx_string = f"{self.sender}{self.receiver}{self.amount}{self.timestamp}"
        return hashlib.sha256(tx_string.encode()).hexdigest()[:16]
    
    def sign_transaction(self, private_key):
        """Sign the transaction hash"""
        self.signature = utils.sign_data(private_key, self.tx_hash)
        
    def verify_transaction(self, public_key):
        """Verify the transaction signature"""
        if not self.signature:
            return False
        return utils.verify_signature(public_key, self.tx_hash, self.signature)
    
    def to_dict(self):
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "gas_fee": self.gas_fee,
            "timestamp": self.timestamp,
            "tx_hash": self.tx_hash,
            "signature": self.signature
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            sender=data['sender'],
            receiver=data['receiver'],
            amount=data['amount'],
            gas_fee=data['gas_fee'],
            timestamp=data['timestamp'],
            tx_hash=data['tx_hash'],
            signature=data.get('signature')
        )

    def __repr__(self):
        sig_stat = "Signed" if self.signature else "Unsigned"
        return (
                f"TX[{self.tx_hash}]: {self.sender[:8]}... → {self.receiver[:8]}... | "
                f"{self.amount} SHEA [{sig_stat}]")


class Block:
    """Represents a block in the blockchain"""
    
    def __init__(self, number, transactions, validator_name, previous_hash, timestamp=None, nonce=None, block_hash=None):
        self.number = number
        self.transactions = transactions
        self.validator = validator_name
        self.previous_hash = previous_hash
        self.timestamp = timestamp if timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.nonce = nonce if nonce is not None else random.randint(1000, 9999)
        self.hash = block_hash if block_hash else self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate block hash based on its contents"""
        tx_hashes = ''.join([tx.tx_hash for tx in self.transactions])
        block_string = f"{self.number}{tx_hashes}{self.validator}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()[:16]
    
    def get_total_fees(self):
        """Calculate total gas fees in the block"""
        return sum(tx.gas_fee for tx in self.transactions)
    
    def get_total_volume(self):
        """Calculate total transaction volume"""
        return sum(tx.amount for tx in self.transactions)
    
    def to_dict(self):
        return {
            "number": self.number,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "validator": self.validator,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, data):
        transactions = [Transaction.from_dict(tx) for tx in data['transactions']]
        return cls(
            number=data['number'],
            transactions=transactions,
            validator_name=data['validator'],
            previous_hash=data['previous_hash'],
            timestamp=data['timestamp'],
            nonce=data['nonce'],
            block_hash=data['hash']
        )

    def __repr__(self):
        return (
                f"\n{ '='*70}\n"
                f"Block #{self.number} | Hash: {self.hash}\n"
                f"Previous Hash: {self.previous_hash}\n"
                f"Validator: {self.validator} | Time: {self.timestamp}\n"
                f"Transactions: {len(self.transactions)} | Volume: {self.get_total_volume():.4f} SHEA\n"
                f"{ '='*70}")


class Validator:
    """Represents a validator in the Proof of Stake network"""
    
    def __init__(self, name, stake, reward_address, blocks_proposed=0, total_rewards=0.0, is_active=True):
        self.name = name
        self.stake = stake
        self.reward_address = reward_address
        self.blocks_proposed = blocks_proposed
        self.total_rewards = total_rewards
        self.is_active = is_active
    
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
    
    def to_dict(self):
        return {
            "name": self.name,
            "stake": self.stake,
            "reward_address": self.reward_address,
            "blocks_proposed": self.blocks_proposed,
            "total_rewards": self.total_rewards,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data):
        reward_addr = data.get('reward_address', data.get('address')) 
        return cls(
            name=data['name'],
            stake=data['stake'],
            reward_address=reward_addr,
            blocks_proposed=data['blocks_proposed'],
            total_rewards=data['total_rewards'],
            is_active=data['is_active']
        )

    def __repr__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} [{status}] (Stake: {self.stake} SHEA, Reward Addr: {self.reward_address})"


class Account:
    """Represents a user account with Crypto Keys"""
    
    def __init__(self, name, address, public_key=None, balance=100.0):
        self.name = name
        self.address = address
        self.public_key = public_key # Tuple (e, n)
        self.balance = balance
    
    def send(self, receiver_address, amount, private_key=None, gas_fee=0.001):
        """Create a signed transaction"""
        if self.balance >= amount + gas_fee:
            self.balance -= (amount + gas_fee)
            tx = Transaction(self.address, receiver_address, amount, gas_fee)
            if private_key:
                tx.sign_transaction(private_key)
            return tx
        else:
            return None
    
    def receive(self, amount):
        """Receive funds"""
        self.balance += amount
    
    def to_dict(self):
        return {
            "name": self.name,
            "address": self.address,
            "public_key": utils.serialize_key(self.public_key) if self.public_key else None,
            "balance": self.balance
        }
    
    @classmethod
    def from_dict(cls, data):
        pk = None
        if data.get('public_key'):
             pk = utils.deserialize_key(data['public_key'])
             
        return cls(
            name=data['name'],
            address=data['address'],
            public_key=pk,
            balance=data['balance']
        )

    def __repr__(self):
        return f"Account({self.name} | {self.address[:10]}...): {self.balance:.4f} SHEA"


class ProofOfStakeBlockchain:
    """Full Proof of Stake blockchain implementation"""
    
    def __init__(self, genesis_validator="Genesis"):
        self.validators = []
        self.blockchain = []
        self.pending_transactions = []
        self.accounts = {}
        self.current_block_number = 0
        
        # Hardcoded Treasury Keys (DevNet)
        self.treasury_pub = "cc70e61235e2f9a1282667df6f04b0b6e32d0ca56360be7c19521e3ec675e3c9b8008df6532c2777f6d1728f8681169efbde78785ce53118a6181f7d122ae4f8"
        self.treasury_priv = "7ff3f24856009368c98eaea433849f80f63bf06ca799e4945b3d81f2c43dbcc2"
        
        # Create genesis block
        genesis_block = Block(
            number=0, 
            transactions=[], 
            validator_name=genesis_validator, 
            previous_hash="0" * 16, 
            timestamp="2024-01-01 00:00:00", 
            nonce=0
        )
        self.blockchain.append(genesis_block)
        
        # Initialize Treasury
        treasury_addr = utils.generate_address(self.treasury_pub)
        self.treasury_address = treasury_addr # Store for lookup
        self.accounts[treasury_addr] = Account("Treasury", treasury_addr, self.treasury_pub, 1000000.0)
    
    def create_account(self, name, initial_balance=0.0, address=None, public_key=None):
        """Create a new account"""
        if address is None:
            if public_key:
                address = utils.generate_address(public_key)
            else:
                # Fallback to random if no keys
                random_part = str(random.randint(0, 1000000))
                address = f"0x{hashlib.sha256((name + random_part).encode()).hexdigest()[:40]}"
            
        if address not in self.accounts:
            self.accounts[address] = Account(name, address, public_key, initial_balance)
            return self.accounts[address]
        return self.accounts[address]
    
    def add_validator(self, name, stake, reward_address=None):
        """Add a new validator to the network"""
        if stake < 32:
            return None
        
        # Check if validator name already exists to prevent duplicates
        if any(v.name == name for v in self.validators):
            print(f"Validator {name} already exists.")
            return None
        
        if reward_address is None:
            acc = self.create_account(f"{name}_Wallet", 0)
            reward_address = acc.address
        
        validator = Validator(name, stake, reward_address)
        self.validators.append(validator)
        return validator

    def add_validator_from_network(self, val_data):
        """Add a validator received from the network"""
        try:
            # Check for duplicates
            name = val_data.get('name')
            if any(v.name == name for v in self.validators):
                return False
            
            validator = Validator.from_dict(val_data)
            self.validators.append(validator)
            return True
        except Exception as e:
            print(f"Error adding network validator: {e}")
            return False
    
    def add_transaction(self, sender_address, receiver_address, amount, private_key=None, gas_fee=0.001):
        """Add a transaction to the pending pool"""
        if sender_address not in self.accounts:
            return False
        
        # Check receiver exists (create stub if not)
        if receiver_address not in self.accounts:
            # New accounts discovered on network start with 0 balance
            self.create_account("Unknown", 0, address=receiver_address)
        
        sender = self.accounts[sender_address]
        
        # Verify Key ownership if keys exist
        if sender.public_key and private_key:
            pass
            
        tx = sender.send(receiver_address, amount, private_key, gas_fee)
        
        if tx:
            # Verify Signature if sender has public key
            if sender.public_key:
                if not tx.verify_transaction(sender.public_key):
                    print("❌ Transaction Signature Invalid!")
                    sender.balance += (amount + gas_fee)
                    return False
            
            self.pending_transactions.append(tx)
            return True
        return False
    
    def add_remote_transaction(self, tx):
        """Process a transaction received from the network"""
        # 1. Check/Create Sender
        if tx.sender not in self.accounts:
            # We don't know the balance, so we assume valid for mempool propagation 
            # (or we could start at 0 and let it go negative to track debt)
            self.create_account("UnknownSender", 0, address=tx.sender)
        
        sender = self.accounts[tx.sender]
        
        # 2. Check Duplicate
        if any(t.tx_hash == tx.tx_hash for t in self.pending_transactions):
            return False

        # 3. Deduct Balance (Speculative State Update)
        # This keeps the local view of the sender's balance in sync with the sender's view
        if sender.balance >= (tx.amount + tx.gas_fee):
            sender.balance -= (tx.amount + tx.gas_fee)
        else:
            # If we think they don't have funds, we still add it if it's signed?
            # For this simple system, we assume the sender knows truth. 
            # We deduct anyway (going negative) to show the spending.
            sender.balance -= (tx.amount + tx.gas_fee)
            
        # 4. Add to Pending
        self.pending_transactions.append(tx)
        return True

    def get_total_stake(self):
        """Calculate total stake in the network"""
        return sum(v.stake for v in self.validators if v.is_active)
    
    def select_validator(self):
        """Select validator using weighted random selection"""
        active_validators = [v for v in self.validators if v.is_active]
        
        if not active_validators:
            return None
        
        total_stake = sum(v.stake for v in active_validators)
        if total_stake == 0:
            return active_validators[0]
            
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
            return None
        
        selected_validator = self.select_validator()
        if not selected_validator:
            return None
        
        transactions_to_include = self.pending_transactions[:max_transactions]
        self.pending_transactions = self.pending_transactions[max_transactions:]
        
        previous_hash = self.blockchain[-1].hash
        
        self.current_block_number += 1
        new_block, reward = selected_validator.propose_block(
            self.current_block_number, 
            transactions_to_include, 
            previous_hash
        )
        
        # Update accounts
        for tx in transactions_to_include:
            # Ensure receiver exists locally even if we are the miner
            if tx.receiver not in self.accounts:
                self.create_account("Unknown", 0, address=tx.receiver)
            self.accounts[tx.receiver].receive(tx.amount)
        
        if selected_validator.reward_address not in self.accounts:
            self.create_account(f"{selected_validator.name}_Wallet", 0, address=selected_validator.reward_address)
        self.accounts[selected_validator.reward_address].receive(reward)
        
        self.blockchain.append(new_block)
        return new_block

    def rebuild_state(self):
        """Replay the entire blockchain to calculate current state"""
        print("Rebuilding state from genesis...")
        # Reset Accounts to Initial State (Treasury only)
        self.accounts = {}
        self.pending_transactions = [] # Clear pending as they might be in the chain now
        
        # Re-initialize Treasury
        treasury_addr = self.treasury_address
        self.accounts[treasury_addr] = Account("Treasury", treasury_addr, self.treasury_pub, 1000000.0)
        
        # Replay Blocks (Skip Genesis as it's empty/handled)
        for block in self.blockchain[1:]:
            self._apply_block_state(block)
            
    def _apply_block_state(self, block):
        """Helper to apply a block's transactions to the state"""
        # 1. Process Transactions
        for tx in block.transactions:
            # Ensure accounts exist
            if tx.sender not in self.accounts:
                 self.create_account("UnknownSender", 0.0, address=tx.sender)
            if tx.receiver not in self.accounts:
                 self.create_account("UnknownReceiver", 0.0, address=tx.receiver)
            
            # Execute Transfer
            sender = self.accounts[tx.sender]
            receiver = self.accounts[tx.receiver]
            
            # We blindly debit/credit here because this is the Canonical Chain Truth
            sender.balance -= (tx.amount + tx.gas_fee)
            receiver.balance += tx.amount

        # 2. Process Rewards
        if block.validator:
            # Find validator to get reward address
            # Note: In a rebuild, we might need to look up validator from a list? 
            # Or just trust the block's validator name if we aren't tracking validator set changes history.
            # For this simple model, we assume validators exist in self.validators list (which is not state-rebuilt yet).
            # Limitation: If validators were dynamic (added via TX), we'd need to replay that too.
            # Assuming static validator set for now or they are added manually.
            
            val = next((v for v in self.validators if v.name == block.validator), None)
            if val:
                if val.reward_address not in self.accounts:
                     self.create_account(f"{val.name}_Wallet", 0, address=val.reward_address)
                
                reward = 0.01 + block.get_total_fees()
                self.accounts[val.reward_address].receive(reward)

    def add_block_from_network(self, block_data):
        """Add a block received from the network if valid"""
        try:
            block = Block.from_dict(block_data)
            last_block = self.blockchain[-1]
            
            # Simple Validation
            if block.number != last_block.number + 1:
                return False
            
            if block.previous_hash != last_block.hash:
                print(f"Block hash mismatch: Expected {last_block.hash}, Got {block.previous_hash}")
                return False
            
            # Detect Local Pending Transactions (Speculative State)
            # If a TX in this block corresponds to a local pending one, 
            # it means we already deducted the balance in 'send()'. 
            # To avoid double counting, we REVERT that deduction first, then apply the block fully.
            
            local_pending_hashes = {t.tx_hash for t in self.pending_transactions}
            
            for tx in block.transactions:
                if tx.tx_hash in local_pending_hashes:
                    # Revert the speculative deduction for the sender
                    if tx.sender in self.accounts:
                        self.accounts[tx.sender].balance += (tx.amount + tx.gas_fee)
            
            # Now Apply the Block State (Canonical Truth)
            self._apply_block_state(block)

            self.blockchain.append(block)
            self.current_block_number = block.number
            
            # Remove transactions in this block from our local pending pool
            new_tx_hashes = {tx.tx_hash for tx in block.transactions}
            self.pending_transactions = [
                t for t in self.pending_transactions 
                if t.tx_hash not in new_tx_hashes
            ]
            
            return True
        except Exception as e:
            print(f"Error adding network block: {e}")
            import traceback
            traceback.print_exc()
            return False

    def is_chain_valid(self, chain):
        """Verify a provided chain's integrity"""
        for i in range(1, len(chain)):
            current = chain[i]
            prev = chain[i-1]
            if current.previous_hash != prev.hash:
                return False
            if current.hash != current.calculate_hash():
                return False
        return True

    def replace_chain(self, new_chain_data):
        """Replace local chain with new chain if it's longer and valid"""
        try:
            new_chain = [Block.from_dict(b) for b in new_chain_data]
            if len(new_chain) > len(self.blockchain) and self.is_chain_valid(new_chain):
                print(f"Replacing chain with {len(new_chain)} blocks...")
                self.blockchain = new_chain
                self.current_block_number = len(self.blockchain) - 1
                
                # CRITICAL: Rebuild Account State from the new history
                self.rebuild_state()
                
                return True
        except Exception as e:
            print(f"Error replacing chain: {e}")
        return False

    def to_dict(self):
        """Serialize entire blockchain state"""
        return {
            "chain": [b.to_dict() for b in self.blockchain],
            "validators": [v.to_dict() for v in self.validators],
            "accounts": [a.to_dict() for a in self.accounts.values()],
            "pending_txs": [tx.to_dict() for tx in self.pending_transactions]
        }
    
    @classmethod
    def from_dict(cls, data):
        """Deserialize blockchain state"""
        bc = cls()
        bc.blockchain = [Block.from_dict(b) for b in data['chain']]
        bc.validators = [Validator.from_dict(v) for v in data['validators']]
        
        bc.accounts = {}
        for a in data['accounts']:
            acc = Account.from_dict(a)
            bc.accounts[acc.address] = acc
            
        bc.pending_transactions = [Transaction.from_dict(t) for t in data['pending_txs']]
        bc.current_block_number = len(bc.blockchain) - 1
        return bc
