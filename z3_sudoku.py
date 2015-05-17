#!/usr/bin/python2
from __future__ import print_function
import z3

def conv_sudoku_char_to_int(s) :
    '''Convert a string of 1..9,. to int(1)..int(9), None. Also space becomes None'''
    valid_chars = '123456789.'
    s_to_num = lambda c: None if c == '.' else int(c)
    arr = [ s_to_num(c) for c in s.replace(' ','.') if c in valid_chars ]
    if len(arr) < 9 :
        return None
    return arr[0:9]

def read_board(fn) :
    '''Read a sudoku board file and return a list of lists of (int or None)'''
    lineno = 0
    ret = list()
    for line in open(fn, 'rt') :
        lineno += 1
        line = line.strip()
        if not line or line.startswith('#') or line.startswith(';') :
            continue
        arr = conv_sudoku_char_to_int(line)
        if arr is None :
            raise RuntimeError('Bad line in sudoku file %s:%d.'%(fn, lineno))
        ret.append(arr)
    if len(ret) < 9 :
        RuntimeError('Not enough lines in sudoku file %s.'%(fn))
    return ret

def print_board(arr) :
    '''Print the sudoku board, arr is a list of lists of (int or None),
    depending on whether it's a number or empty square.'''
    cell_to_char = lambda i: '.' if i is None else '%d'%(i)
    for row in arr :
        print(' '.join(map(cell_to_char,row)))

def product(*arr) :
    '''for a,b,c,... in product(itera, iterb, iterc, ...)
    is a shorthand for the nested for a in itera: for b in iterb: ...'''
    if len(arr) == 1 :
        for k in arr[0] :
            yield (k,)
        return

    this = arr[0]
    remains = arr[1:]

    for k in this :
        for r in product(*remains) :
            yield (k,)+r

def gen_groups() :
    '''Generate a list of list of (row, col) tuples that form a group in a
    sudoku, e.g. that have to be unique. First 18 groups are rows and columns,
    followed by the 9 squares.'''
    ret = list()
    for i in range(0,9) :
        ret.append([(i,n) for n in range(0,9)])
        ret.append([(n,i) for n in range(0,9)])

    for outer_rc in product(range(0,3), range(0,3)) :
        l = list()
        for inner_rc in product(range(0,3), range(0,3)) :
            r = 3*outer_rc[0] + inner_rc[0]
            c = 3*outer_rc[1] + inner_rc[1]
            l.append((r,c))
        ret.append(l)
    return ret

def gen_sudoku_solver() :
    '''gen_sudoku_solver() generates a z3 solver instance and adds
    all the variables, value constraints (1..9) and group constraints
    (distinct values in each row, column, square) to it. Returns
    the solver instance, and a dictionary holding references to the z3
    integer variables.

    solver, cells = gen_sudoku_solver()
    cells[(2,3)] is the z3.Int() named r2c3 for third row, fourth column'''

    solver = z3.Solver()
    cells = dict()
    for rc in product(range(0,9), range(0,9)) :
        v = z3.Int('r%dc%d'%rc)
        cells[rc] = v
        solver.add(v > 0)
        solver.add(v < 10)
    for group in gen_groups() :
        members = [cells[rc] for rc in group]
        solver.add(z3.Distinct(*members))
    return solver, cells

def solver_add_board(solver, cells, board) :
    '''Add constraints for a loaded board (list of lists of ints/None) to a
    z3 solver instance with cells corresponding to z3.Int variables.

    solver_add-board(solver, cells, board)
        solver: z3.Solver
        cells:  dict[(row, column)] of z3.Int variables
        board:  list of lists of int/none: board[row][column] = 1..9 or None'''
    for r, row in enumerate(board) :
        for c, el in enumerate(row) :
            if el is None :
                continue
#            print('Board constraint: %d,%d = %d'%(r,c,el))
            v = cells[(r,c)]
            solver.add(v == el)

def main() :
    import optparse

    parser = optparse.OptionParser(usage='%prog [opts] sudoku_file.txt')
    parser.add_option('-s','--smt2',dest='smt2',metavar='SMT2FILE',
        default=None,help='Dump solver data to SMT2 file.')
    opts, args = parser.parse_args()

    if len(args) != 1 :
        parser.error('Specify exactly one sudoku input file.')

    board = read_board(args[0])

    print('Generating solver...')
    solver, cells = gen_sudoku_solver()

    print('Adding board constraint to solver...')
    solver_add_board(solver, cells, board)
    print_board(board)

    if opts.smt2 :
        open(opts.smt2,'wt').write(solver.to_smt2())

    print('Checking solver...')
    print('Solver: is solvable?',solver.check())

    model = solver.model()
    for rc in product(range(0,9), range(0,9)) :
        r, c = rc
        val = model[cells[rc]].as_long()
        if board[r][c] is not None :
            b = board[r][c]
            if b != val :
                print('*** Error, %s is %d in file, %d in model!'%(rc, b, val))
        board[r][c] = val

    print_board(board)

if __name__ == '__main__':
    main()
