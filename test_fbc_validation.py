import sys
sys.path.insert(0, 'src')
from commander.utils.token_utils import is_fbc_token

print('Testing FBC token validation:')
test_tokens = ['162', '163', '164', 'abc', 'XYZ', '1234', 'abcd12', 'AB1234']
for token in test_tokens:
    print('  {}: {}'.format(token, is_fbc_token(token)))