import socket
import threading
import json
import time
from blockchain import ProofOfStakeBlockchain, Block, Transaction

class Node:
    def __init__(self, host, port, bootstrap_node=None, on_event=None):
        self.host = host
        self.port = port
        self.peers = set() # Set of (host, port) tuples
        self.active_connections = [] # List of active socket objects for broadcasting
        self.blockchain = ProofOfStakeBlockchain()
        self.node_id = f"{host}:{port}"
        self.running = True
        self.on_event = on_event # Callback for UI updates
        
        # Initialize basic state
        self.blockchain.add_validator("Genesis_Validator", 32)
        self.blockchain.create_account("Treasury", 1000)

        # Networking setup
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        
        # Start listener
        self.listen_thread = threading.Thread(target=self.start_server)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        
        # Connect to bootstrap if provided
        if bootstrap_node:
            self.connect_to_peer(bootstrap_node[0], bootstrap_node[1])

        print(f"[*] Node started on {self.host}:{self.port}")
    
    def trigger_event(self, event_type, data):
        """Trigger UI update callback if registered"""
        if self.on_event:
            self.on_event(event_type, data)

    def start_server(self):
        self.server_socket.listen(5)
        while self.running:
            try:
                client_sock, address = self.server_socket.accept()
                # Track incoming connection
                self.active_connections.append(client_sock)
                threading.Thread(target=self.handle_client, args=(client_sock,), daemon=True).start()
            except OSError:
                break

    def connect_to_peer(self, host, port):
        if (host, port) == (self.host, self.port):
            return 
            
        if (host, port) in self.peers:
            return 

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            self.peers.add((host, port))
            self.active_connections.append(sock)
            print(f"[+] Connected to peer {host}:{port}")
            
            # Send handshake
            self.send_message(sock, {"type": "HANDSHAKE", "node_id": self.node_id})
            
            # Request chain
            self.send_message(sock, {"type": "GET_CHAIN"})
            
            # Start listener for this connection
            threading.Thread(target=self.handle_client, args=(sock,), daemon=True).start()
            
        except Exception as e:
            print(f"[-] Could not connect to {host}:{port} - {e}")

    def handle_client(self, conn):
        # Use makefile for line-based reading
        # 'r' mode, utf-8 encoding
        try:
            stream = conn.makefile('r', encoding='utf-8')
            for line in stream:
                if not self.running:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    self.handle_message(msg, conn)
                except json.JSONDecodeError:
                    print(f"[!] Invalid JSON received: {line[:50]}...")
        except Exception as e:
            # print(f"[!] Connection error/closed: {e}")
            pass
        finally:
            try:
                conn.close()
            except:
                pass
            if conn in self.active_connections:
                self.active_connections.remove(conn)

    def send_message(self, conn, msg_dict):
        try:
            # Append newline for protocol delimiter
            data = json.dumps(msg_dict) + "\n"
            conn.sendall(data.encode('utf-8'))
        except Exception as e:
            # print(f"[!] Send error: {e}")
            if conn in self.active_connections:
                self.active_connections.remove(conn)

    def broadcast(self, msg_dict):
        """Send message to all known peers"""
        # print(f"[>] Broadcasting {msg_dict['type']} to {len(self.active_connections)} peers")
        for conn in list(self.active_connections): 
            self.send_message(conn, msg_dict)

    def handle_message(self, msg, conn):
        msg_type = msg.get('type')
        
        if msg_type == 'HANDSHAKE':
            pass

        elif msg_type == 'GET_CHAIN':
            chain_data = self.blockchain.to_dict()
            response = {
                "type": "CHAIN_RESPONSE",
                "data": chain_data
            }
            self.send_message(conn, response)

        elif msg_type == 'CHAIN_RESPONSE':
            remote_chain_data = msg.get('data')
            if remote_chain_data:
                chain = remote_chain_data.get('chain')
                
                # Check Chain Length
                if chain and len(chain) > len(self.blockchain.blockchain):
                    print(f"[!] Received longer chain ({len(chain)} blocks). Replacing local chain...")
                    self.blockchain = ProofOfStakeBlockchain.from_dict(remote_chain_data)
                    print("[✓] Chain synchronized.")
                    self.trigger_event("CHAIN_SYNC", {"blocks": len(self.blockchain.blockchain)})
                
                # Also sync pending transactions (Mempool Sync)
                pending_txs = remote_chain_data.get('pending_txs', [])
                for tx_data in pending_txs:
                    try:
                        tx = Transaction.from_dict(tx_data)
                        if not any(t.tx_hash == tx.tx_hash for t in self.blockchain.pending_transactions):
                            self.blockchain.pending_transactions.append(tx)
                    except:
                        pass

        elif msg_type == 'NEW_BLOCK':
            block_data = msg.get('block')
            if block_data:
                if self.blockchain.add_block_from_network(block_data):
                    print(f"[✓] Received and added Block #{block_data['number']}")
                    self.trigger_event("CHAIN_SYNC", {"blocks": len(self.blockchain.blockchain)})
                else:
                    if block_data['number'] > self.blockchain.current_block_number + 1:
                        self.send_message(conn, {"type": "GET_CHAIN"})

        elif msg_type == 'NEW_TX':
            tx_data = msg.get('tx')
            if tx_data:
                try:
                    tx = Transaction.from_dict(tx_data)
                    # Use proper handler to update state
                    if self.blockchain.add_remote_transaction(tx):
                        print(f"[+] Received TX: {tx.amount} SHEA from {tx.sender[:8]}...")
                except Exception as e:
                    print(f"Error processing TX: {e}")

        elif msg_type == 'NEW_VALIDATOR':
            val_data = msg.get('data')
            if val_data:
                if self.blockchain.add_validator_from_network(val_data):
                    print(f"[+] New Validator Discovered: {val_data.get('name')}")

    # --- CLI Interaction Methods ---
    
    def create_wallet(self, name):
        acc = self.blockchain.create_account(name)
        return acc

    def create_validator(self, name, stake, reward_address):
        val = self.blockchain.add_validator(name, stake, reward_address)
        if val:
            # Broadcast existence to peers
            self.broadcast({
                "type": "NEW_VALIDATOR",
                "data": val.to_dict()
            })
        return val

    def request_faucet(self, receiver_addr):
        """Send 100 SHEA from Treasury to receiver"""
        # Reliable lookup using stored address
        treasury_addr = getattr(self.blockchain, 'treasury_address', None)
        
        # Fallback if attribute missing (backward compat or error)
        if not treasury_addr:
             for acc in self.blockchain.accounts.values():
                if acc.name == "Treasury":
                    treasury_addr = acc.address
                    break
        
        if treasury_addr and treasury_addr in self.blockchain.accounts:
            # We use the hardcoded private key from blockchain instance
            priv = self.blockchain.treasury_priv
            if self.send_transaction(treasury_addr, receiver_addr, 100.0, priv):
                print(f"[✓] Faucet request broadcasted for {receiver_addr[:8]}...")
                return True
        return False

    def send_transaction(self, sender_addr, receiver_addr, amount, private_key=None):
        if self.blockchain.add_transaction(sender_addr, receiver_addr, amount, private_key):
            # Broadcast TX
            tx = self.blockchain.pending_transactions[-1]
            self.broadcast({
                "type": "NEW_TX",
                "tx": tx.to_dict()
            })
            return True
        return False

    def mine(self):
        block = self.blockchain.mine_block()
        if block:
            # Broadcast block
            self.broadcast({
                "type": "NEW_BLOCK",
                "block": block.to_dict()
            })
            return block
        return None

    def get_info(self):
        return {
            "peers": len(self.active_connections),
            "blocks": len(self.blockchain.blockchain),
            "validators": len(self.blockchain.validators),
            "pending_txs": len(self.blockchain.pending_transactions)
        }
