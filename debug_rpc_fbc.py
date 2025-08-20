import sys
sys.path.insert(0, 'src')
import re
from commander.utils.token_utils import token_validator

token = "rpc123"
print(f"Token: {token}")
print(f"Valid token: {token_validator.validate_token(token)}")
print(f"Matches [a-zA-Z0-9]{{3,6}}: {bool(re.match(r'^[a-zA-Z0-9]{3,6}$', token))}")
print(f"Matches [a-zA-Z]+[0-9]+: {bool(re.match(r'^[a-zA-Z]+[0-9]+$', token))}")
if re.match(r'^[a-zA-Z]+[0-9]+$', token):
    letter_part = re.match(r'^[a-zA-Z]+', token).group()
    print(f"Letter part: '{letter_part}', length: {len(letter_part)}")
    print(f"Total length: {len(token)}")
    print(f"Length == 6: {len(token) == 6}")
    print(f"Letter part length >= 4: {len(letter_part) >= 4}")
print(f"Is FBC token: {token_validator.is_fbc_token(token)}")