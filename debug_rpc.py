import sys
sys.path.insert(0, 'src')
from commander.utils.token_utils import token_validator

token = "rpc123"
print(f"Token: {token}")
print(f"Valid token: {token_validator.validate_token(token)}")
print(f"Is FBC token: {token_validator.is_fbc_token(token)}")
print(f"Matches [a-z]+[0-9]+: {bool(__import__('re').match(r'^[a-z]+[0-9]+$', token))}")
print(f"Is RPC token: {token_validator.is_rpc_token(token)}")