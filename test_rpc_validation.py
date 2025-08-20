import sys
sys.path.insert(0, 'src')
from commander.utils.token_utils import is_rpc_token

print('Testing RPC token validation:')
# Test some valid RPC tokens
valid_rpc_tokens = ['abc123', 'xyz', 'test']
for token in valid_rpc_tokens:
    result = is_rpc_token(token)
    print('  {}: {} (RPC token)'.format(token, result))

print('\nTesting FBC tokens as RPC (should be False):')
# Test FBC tokens (should return False for RPC validation)
fbc_tokens = ['162', 'abc', '1234']
for token in fbc_tokens:
    result = is_rpc_token(token)
    print('  {}: {} (should be False for RPC)'.format(token, result))