import logging
import glob
from httpsig.verify import HeaderVerifier
import json

def verify(filename):
    example = json.load(open(filename, 'r'))
    marn_key = open(example['keyFilename'], 'r').read()
    hv = HeaderVerifier(
            headers = example,
            secret = marn_key,
            method = 'POST',
            path = example['url'],
            host = example['Host'],
            sign_header = 'Signature',
        )
    return hv.verify()

def main():
    logging.basicConfig(level="DEBUG")
    for f in sorted(glob.glob('examples/*.json')):
        print(f, verify(f))


if __name__=='__main__':
    main()
