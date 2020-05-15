# # Foster to Cauer
# 2019/05/06 created by Tom HARA
import argparse
import sympy
import datetime

# version of this script
myVersion = '0.0.01'

##############################################################################
# arg parsing
##############################################################################
parser = argparse.ArgumentParser(
    prog='Foster2Cauer.py',
    usage='Convert Foster RC network to Cauer RC network.',
    epilog='end',
    add_help=True
    )

parser.add_argument('input_file', help='specify input filename',
                    action='store', type=str)
parser.add_argument('output_file', help='specify output filename',
                    action='store', type=str)

parser.add_argument('-r', '--rational_rth',
                    help='better accuracy but computationally expensive',
                    action='store_true')
parser.add_argument('--version', action='version',
                    version='%(prog)s ' + myVersion)

args = parser.parse_args()

# Input file, output file, and flag(s):
input_file = args.input_file
output_file = args.output_file
rational_rth = args.rational_rth

##############################################################################

"""
https://stackoverflow.com/questions/13890935/does-pythons-time-time-return-the-local-or-utc-timestamp
"""
# time stamp when the script started.
timestamp = str(datetime.datetime.now()).split('.')[0].replace(":", "-")


sympy.init_printing()

s = sympy.Symbol('s')
cc1, rc1, tauc1 = sympy.symbols(r"C_c1, R_c1, \tau_{c1}")
cc2, rc2, tauc2 = sympy.symbols(r"C_c2, R_c2, \tau_{c2}")
cc3, rc3, tauc3 = sympy.symbols(r"C_c3, R_c3, \tau_{c3}")

# CauerMatSample3x3 used for debugging at jupyter
CauerMatSample3x3 = sympy.Matrix([[cc1, rc1, tauc1],
                                 [cc2, rc2, tauc2],
                                 [cc3, rc3, tauc3]])


with open(input_file, 'r', encoding="utf-8") as fileobj:
    datastr = fileobj.read()         # read all data from a file
    adatastr = datastr.rstrip()      # remove the last "\n"
    datalist = adatastr.split("\n")  # create a list (size: n row * 1 column)

c_list = list()                      # a list for foster network Cth
r_list = list()                      # a list for foster network Rth

for line in datalist:                # read one row at a time
    tmplist = line.split()           # split a row into a list
    # print(tmplist)
    if tmplist == []:                # skip empty rows
        continue
    if tmplist[0][0] == '#':         # skip comment rows
        continue
    if tmplist[0][0:6] == "STAGES":  # number of RC stages
        stages = int(tmplist[1])
        print("stages = " + str(stages))
        continue
    # start reading actual data
    # (1st column is stage number)
    c_list.append(tmplist[1])        # Cth on the 2nd column
    r_list.append(tmplist[2])        # Rth on the 3rd column


CauerMat = sympy.zeros(stages, 3)    # Final results will be stored here.

FosterMat = sympy.zeros(stages, 3)   # Input data will be stored here

for i in range(stages):
    FosterMat[i, 0] = sympy.Rational(c_list[i])

    # By default, reduced the accuracy level by not Rationalizing Rth.
    FosterMat[i, 1] = sympy.Rational(r_list[i]) if rational_rth else r_list[i]

    FosterMat[i, 2] = FosterMat[i, 0] * FosterMat[i, 1]


# ### As shown in the CauerMatSample3x3, variables line up in ascending order.
# Cc1 and Rc1 pair represents the first stage of the Cauer model.
# They are next to Junction.
# So as the Cf1 and Rf1 of the Foster model.


# # FosterMatrix
# This is a faster way to calculate the coeffcients of pf and qf,
# in higher stages.

aMatFoster = sympy.zeros(stages, stages+1)
bMatFoster = sympy.zeros(stages+1, stages+1)

aMatFoster[0, 1] = FosterMat[stages-1, 1]
bMatFoster[0, 1] = 1
bMatFoster[1, 1] = FosterMat[stages-1, 2]

for i in range(2, stages+1):
    aMatFoster[:i, i] = \
        FosterMat[stages - i, 2] * \
        aMatFoster[:i-1, i-1].row_insert(0, sympy.Matrix([0])) + \
        aMatFoster[:i-1, i-1].row_insert(i-1, sympy.Matrix([0])) + \
        FosterMat[stages - i, 1] * bMatFoster[:i, i-1]

    bMatFoster[:i+1, i] = \
        FosterMat[stages - i, 2] * \
        bMatFoster[:i, i-1].row_insert(0, sympy.Matrix([0])) + \
        bMatFoster[:i, i-1].row_insert(i, sympy.Matrix([0]))

svector4Coeff_a = sympy.Matrix(stages, 1, lambda i, j: s**i)
svector4Coeff_b = sympy.Matrix(stages+1, 1, lambda i, j: s**i)
svector4Coeff_a, svector4Coeff_b, stages

Zfall = \
    sympy.Poly(sympy.transpose(
        aMatFoster.col(stages)).dot(svector4Coeff_a), s) / \
    sympy.Poly(sympy.transpose(
        bMatFoster.col(stages)).dot(svector4Coeff_b), s)


# # Recursive Foster to Cauer conversion
# For details, check
#  "20190504_Foster2Cauer3rdOrder_MatrixCalc.ipynb" and
#  "20190504_Foster2Cauer3rdOrder_MatrixCalc_recursive_pre.ipynb"

for i in range(stages):
    (pf, qf) = sympy.fraction(Zfall)
    pf = sympy.Poly(pf, s)
    qf = sympy.Poly(qf, s)
    CauerMat[i, 0] = qf.nth(stages-i)/pf.nth(stages-1-i)

    Yfall = (1/Zfall - CauerMat[i, 0]*s).cancel()
    (qf, pf) = sympy.fraction(Yfall)
    qf = sympy.Poly(qf, s)
    pf = sympy.Poly(pf, s)
    CauerMat[i, 1] = pf.nth(stages-1-i)/qf.nth(stages-1-i)

    # calculate tauc
    CauerMat[i, 2] = CauerMat[i, 0] * CauerMat[i, 1]

    Zfall = (1/Yfall - CauerMat[i, 1]).cancel()


# # Final results in floating values

CauerMat_float = sympy.zeros(stages, 3)
for i in range(stages):
    for j in range(3):
        CauerMat_float[i, j] = float(CauerMat[i, j])


# # Resistance sum value check
Rc_all = 0
Rf_all = 0
for i in range(stages):
    Rc_all = Rc_all + CauerMat_float[i, 1]
    Rf_all = Rf_all + FosterMat[i, 1]
print("Rc_all = %g, Rf_all = %g" % (Rc_all, Rf_all))

epsilon = 1e-8
res = float(abs(Rc_all - Rf_all))
if res > epsilon:
    print("Rc_all and Rf_all don't match, ERROR!!!")


# # output results
with open(output_file, "w") as fileobj:
    tmpstring = ""
    # header
    tmpstring = "## Foster2Cauer results " + str(stages) + "stages\n"
    fileobj.write(tmpstring)
    tmpstring = "## Created: " + timestamp + "\n"
    fileobj.write(tmpstring)
    tmpstring = "# First stage (Cc1 and Rc1) is connected to Junction.\n"
    fileobj.write(tmpstring)
    tmpstring = "STAGES=\t" + str(stages) + "\n\n"
    fileobj.write(tmpstring)

    tmpstring = "# stage" + "\t" + "C_cauer" + "\t\t\t" + \
                "R_cauer" + "\t\t\t" + "Tau_cauer\n"
    fileobj.write(tmpstring)
    for i in range(stages):
        tmpstring = str(i+1) + "\t" + \
            str(CauerMat_float[i, 0]) + "\t" + \
            str(CauerMat_float[i, 1]) + "\t" + \
            str(CauerMat_float[i, 2]) + "\n"
        fileobj.write(tmpstring)
