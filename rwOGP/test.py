import os, yaml, sys, json

pjoin = os.path.join

file_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = pjoin(file_dir, 'rwOGP')
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.parse_data import DataParser

if __name__ == '__main__':
    parser = DataParser(pjoin('rwOGP', 'templates', 'dummy6.txt'), 'templates')
    parser()
