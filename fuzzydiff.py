import click
from collections import Counter
# from ansicolor import green, red

"""
example usage:
python fuzzydiff.py dumpdiff doc01todoc03.diff --rate 0.10 > 1-3-10.cmp.diff
python fuzzydiff.py mark_src doc01_lines.txt doc03_lines.txt doc01todoc03.lines.diff
"""

# 'doc02todoc03.lines.diff'
# 'doc02todoc03.diff'

class vstr(str):
    def __init__(self, score=0):
        super(vstr, self).__init__()
        self.score = score
        self.prefix = ''

class WordGene(object):
    """ compare strings in fuzzy way """
    def __init__(self, string, rate=0.9):
        self.string = string
        self.d = Counter(self.string)
        self.rate = rate
        assert type(rate) == float

    def __hash__(self):
        return str.__hash__(self.string)

    def __eq__(self, y):
        all_chars = set(self.d.keys()) | set(y.d.keys())
        ml = 0
        score = 0
        for c in all_chars:
            d_c = self.d.get(c,0)
            y_c = y.d.get(c,0)
            degree = max(d_c, y_c)
            ml += degree
            score += degree - abs(d_c - y_c)
        try:
            val = 1.0*score/ml
        except ZeroDivisionError as e:
            print("self.string: %s" % self.string)
            raise e

        if self.rate < val:
            return True
        else:
            return False

    def __str__(self):
        return self.string

def getall(start, lines):
    return [
        l[1:] for l in lines
        if l.startswith(start) and len(l[1:]) > 0
    ]

def get_diffs(oridiff, rate):
    with open(oridiff) as f:
        lines = f.readlines()
        lines = [l.strip() for l in lines if len(l.strip()) > 0]

    all_m = [ WordGene(l, rate=rate) for l in getall('-', lines) ]
    all_p = [ WordGene(l, rate=rate) for l in getall('+', lines) ]

    same_list = []

    for wgm in all_m:
        for wgp in all_p:
            if wgm == wgp:
                # print('>>> they are same!!! {0} >>> {1}'.format(wgm, wgp))
                same_list.append(wgm)
                same_list.append(wgp)

    same_list = list(set(same_list))
    ms = [o.string for o in all_m]
    ps = [o.string for o in all_p]
    ss = [o.string for o in same_list]


    only_m = set(ms) - set(ss)
    only_p = set(ps) - set(ss)

    print("len(lines): %s" % len(list(set(lines))))
    print("len(ss): %s" % len(ss))
    print("len(only_m): %s" % len(only_m))
    print("len(only_p): %s" % len(only_p))

    return only_m, only_p

############### CLI COMMAND #################

@click.group()
def cli():
    pass

@click.command()
@click.argument('oridiff')
@click.option('--rate', default=0.9, help='fuzzy rate')
def dumpdiff(oridiff, rate):
    click.echo('dump the fuzzy diff')
    only_m, only_p = get_diffs(oridiff, rate)
    for om in only_m:
        print("-%s" % om)
    for op in only_p:
        print("+%s" % op)

@click.command()
@click.argument('old_f')
@click.argument('new_f')
@click.argument('oridiff')
def mark_src(old_f, new_f, oridiff):
    click.echo('mark fuzzy level at source txt file')
    with open(old_f, 'r') as oldr, open(new_f, 'r') as newr:
        oldlines = [ vstr(l.strip()) for l in oldr.readlines() ]
        newlines = [ vstr(l.strip()) for l in newr.readlines() ]

    dd = {}
    score_map = {
        0.9: 1,
        0.6: 2,
        0.3: 3,
    }
    for rate in [0.9, 0.6, 0.3]:
        only_m, only_p = get_diffs(oridiff, rate)
        dd[rate] = {
            'only_m': only_m,
            'only_p': only_p,
        }
        for m in only_m:
            for l in [ l for l in oldlines if m == l]:
                l.prefix = score_map[rate] * '-'

        for p in only_p:
            for l in [ l for l in newlines if p == l]:
                l.prefix = score_map[rate] * '+'

    n_old_f = u'{0}-base-on-{1}.fuzzy.diff'.format(old_f, oridiff.split('.')[0])
    n_new_f = u'{0}-base-on-{1}.fuzzy.diff'.format(new_f, oridiff.split('.')[0])
    with open(n_old_f, 'w') as oldr, open(n_new_f, 'w') as newr:
        oldr.write('\n'.join([ l.prefix+l for l in oldlines ]))
        newr.write('\n'.join([ l.prefix+l for l in newlines ]))

cli.add_command(dumpdiff)
cli.add_command(mark_src)


if __name__ == '__main__':
    cli()
