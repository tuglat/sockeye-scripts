#!/usr/bin/env python3
# *-* coding: utf-8 *-*

"""
Takes tokenized input and computes the subword representation, as well as any requested
factors, which are broadcast across the subwords.
"""
import argparse
import json
import sys

from typing import Iterable, List, Generator

from .factors import *
from .broadcast import broadcast

def main(args):

    factor_list = []
    for factor in args.factors:
        if factor == 'case':
            factor_list.append(CaseFactor())
        elif factor == 'subword':
            factor_list.append(SubwordFactor())
        elif factor == 'mask':
            factor_list.append(MaskFactor())
        elif factor == 'number':
            factor_list.append(NumberFactor())
        else:
            raise Exception('No such factor "{}"'.format(factor))

    factor_names = args.factors

    for lineno, line in enumerate(args.input, 1):
        if args.json:
            """
            This mode is used at inference time.
            Each factor knows the field it wants and picks it out of the JSON object.
            """
            jobj = json.loads(line)

            jobj['factor_names'] = factor_names
            factor_results = dict(zip(factor_names, [f.compute_json(jobj) for f in factor_list]))

            if 'subword' in factor_names:
                factors_to_broadcast = [factor_results[f] for f in factor_names if f != 'subword']
                jobj['factors'] = broadcast(factor_results['subword'], factors_to_broadcast)
            else:
                jobj['factors'] = factor_results

            print(json.dumps(jobj, ensure_ascii=False), file=args.output, flush=True)
        else:
            """
            Used at training time.
            This script is called once for each feature, with the information it needs as raw text.
            """
            factor_str = factor_list[0].compute(line)
            print(factor_str, file=args.output)


if __name__ == '__main__':
    params = argparse.ArgumentParser(description='Compute factors over a token stream, then applies optional casing and subword processing.')
    params.add_argument('--input', '-i',
                        default=sys.stdin,
                        type=argparse.FileType('r'),
                        help='File stream to read tokenized data from. Default: STDIN.')
    params.add_argument('--output', '-o',
                        type=argparse.FileType('w'),
                        default=sys.stdout,
                        help='Output file to write to. Default: STDOUT.')
    params.add_argument('factors',
                        nargs='+',
                        default=[],
                        help="List of factors to compute.")
    params.add_argument('--json', action='store_true',
                        help='Work with JSON input and output (inference mode).')

    args = params.parse_args()

    main(args)
