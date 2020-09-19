import json

data = json.load(open('alicebobcarol.json', 'r'))

result = []
count = 0

for person in data:
    fields = person['fields']

    if 'public_key' in fields and 'private_key' in fields:
        result = {
                'public': fields['public_key'],
                'private': fields['private_key'],
                }
        json.dump(result,
                open('keys-%04d.json' % (count,), 'w'),
                sort_keys=True, indent=4)
        count += 1
