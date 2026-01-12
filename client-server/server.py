from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import blockchain

class BlockchainServer:
    def __init__(self):
        self.blockchain = blockchain.ProofOfStakeBlockchain()
        # Initialize with some defaults
        self.blockchain.add_validator("Genesis_Validator", 32)
        self.blockchain.create_account("Treasury", 1000)
        print("Blockchain initialized with Genesis Validator and Treasury.")

    def create_account(self, name, initial_balance):
        account = self.blockchain.create_account(name, float(initial_balance))
        return account.to_dict()

    def add_validator(self, name, stake):
        validator = self.blockchain.add_validator(name, float(stake))
        if validator:
            return validator.to_dict()
        return False

    def add_transaction(self, sender, receiver, amount):
        return self.blockchain.add_transaction(sender, receiver, float(amount))

    def mine_block(self):
        block = self.blockchain.mine_block()
        if block:
            return block.to_dict()
        return None

    def get_balance(self, address):
        return self.blockchain.get_balance(address)

    def get_stats(self):
        # Gather stats
        total_volume = sum(b.get_total_volume() for b in self.blockchain.blockchain[1:])
        return {
            "total_blocks": len(self.blockchain.blockchain),
            "pending_txs": len(self.blockchain.pending_transactions),
            "active_validators": len([v for v in self.blockchain.validators if v.is_active]),
            "total_accounts": len(self.blockchain.accounts),
            "total_volume": total_volume,
            "validators": [v.to_dict() for v in self.blockchain.validators],
            "accounts": [a.to_dict() for a in self.blockchain.accounts.values()]
        }

    def get_block(self, block_number):
        if 0 <= block_number < len(self.blockchain.blockchain):
            return self.blockchain.blockchain[block_number].to_dict()
        return None

    def verify_chain(self):
        return self.blockchain.verify_chain()

    def get_account_by_name(self, name):
        # Re-create the deterministic address generation logic from blockchain.py
        import hashlib
        address = f"0x{hashlib.sha256(name.encode()).hexdigest()[:8]}"
        if address in self.blockchain.accounts:
            return self.blockchain.accounts[address].to_dict()
        return None

    def get_validator_by_name(self, name):
        # Search the validator list
        for v in self.blockchain.validators:
            if v.name == name:
                return v.to_dict()
        return None

def run_server(host='localhost', port=8000):
    # Create server
    with SimpleXMLRPCServer((host, port), requestHandler=SimpleXMLRPCRequestHandler, allow_none=True) as server:
        server.register_introspection_functions()
        
        # Register the blockchain instance wrapper
        blockchain_service = BlockchainServer()
        server.register_instance(blockchain_service)
        
        print(f"Blockchain Node running on {host}:{port}...")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...")

if __name__ == "__main__":
    run_server()
