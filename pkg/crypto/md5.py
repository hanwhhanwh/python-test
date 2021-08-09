import hashlib

text = 'asdf'
enc = hashlib.md5()
# enc.update(text) # TypeError: Unicode-objects must be encoded before hashing
enc.update(text.encode('utf-8'))
encText = enc.hexdigest()

print(encText)

# result
# 912ec803b2ce49e4a541068d495ab570