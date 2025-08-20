import sys
sys.path.insert(0, 'src')
import re
from commander.utils.token_utils import token_validator

token = "rpc123"
print(f"Token: {token}")
print(f"Valid token: {token_validator.validate_token(token)}")
print(f"Matches [a-zA-Z0-9]{{3,6}}: {bool(re.match(r'^[a-zA-Z0-9]{3,6}$', token))}")
print(f"Matches [a-zA-Z]+[0-9]+: {bool(re.match(r'^[a-zA-Z]+[0-9]+$', token))}")
print(f"Matches [0-9]{{3}}: {bool(re.match(r'^[0-9]{3}$', token))}")
print(f"Matches [0-9]{{3}}[a-zA-Z]+: {bool(re.match(r'^[0-9]{3}[a-zA-Z]+$', token))}")
print(f"Length: {len(token)}")
print(f"Is FBC token: {token_validator.is_fbc_token(token)}")