import hashlib
import ecdsa
import base64

# --- ECDSA Implementation using SECP256k1 ---

def generate_keys():
    """
    Generate a new SECP256k1 key pair.
    Returns:
        (public_key_hex, private_key_hex)
    """
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    return (vk.to_string().hex(), sk.to_string().hex())

def serialize_key(key):
    """
    Convert key to string format. 
    In this implementation, keys are already hex strings.
    """
    return key

def deserialize_key(key_str):
    """
    Convert string key back to key object/format.
    In this implementation, keys are managed as hex strings.
    """
    return key_str

def sign_data(private_key_hex, data):
    """
    Sign string data using private key hex string.
    Returns signature as hex string.
    """
    try:
        sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key_hex), curve=ecdsa.SECP256k1)
        signature = sk.sign(data.encode())
        return signature.hex()
    except Exception as e:
        print(f"Signing error: {e}")
        return None

def verify_signature(public_key_hex, data, signature_hex):
    """
    Verify signature using public key hex string.
    """
    try:
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=ecdsa.SECP256k1)
        return vk.verify(bytes.fromhex(signature_hex), data.encode())
    except:
        return False

def generate_address(public_key_hex):
    """
    Generate wallet address from public key hex string.
    """
    # Address is Hash(Public Key String)
    return f"0x{hashlib.sha256(public_key_hex.encode()).hexdigest()[:40]}"
