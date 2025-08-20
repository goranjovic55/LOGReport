import sys
sys.path.insert(0, 'src')
from commander.utils.token_utils import is_fbc_token

print('Testing invalid FBC tokens:')
invalid_tokens = ['12', '1234567', '!@#', 'abc-123']
for token in invalid_tokens:
    result = is_fbc_token(token)
    print('  {}: {} (should be False)'.format(token, result))
    if result:
        print('  ERROR: Invalid token {} was validated as True!'.format(token))