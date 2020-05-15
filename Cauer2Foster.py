# # Cauer to Foster
# 2019/05/06 created by Tom HARA
import argparse
import sympy
import numpy as np
import matplotlib.pyplot as plt
import datetime

# version of this script
myVersion = '0.0.01'

##############################################################################
# arg parsing
##############################################################################
parser = argparse.ArgumentParser(
    prog='Cauer2Foster.py',
    usage='Convert Cauer RC network to Foster RC network.',
    epilog='end',
    add_help=True
    )

parser.add_argument('input_file', help='specify input filename',
                    action='store', type=str)
parser.add_argument('output_file', help='specify output filename',
                    action='store', type=str)

parser.add_argument('-r', '--rational_rth',
                    help='better accuracy but computationally ' +
                    'extremely expensive (strongly not recommended)',
                    action='store_true')
parser.add_argument('-g', '--save_graph', help='save Zth graph image generated by matplotlib (.png)',
                    action='store_true')
parser.add_argument('-s', '--show_graph', help='show Zth graph image generated by matplotlib (.png)',
                    action='store_true')
parser.add_argument('--version', action='version',
                    version='%(prog)s ' + myVersion)

args = parser.parse_args()

# Input file, output file, and flag(s):
input_file = args.input_file
output_file = args.output_file
rational_rth = args.rational_rth

save_graph = args.save_graph
show_graph = args.show_graph

# either of the graph setting is on, it's on
graph_enabled = save_graph or show_graph


##############################################################################

"""
https://stackoverflow.com/questions/13890935/does-pythons-time-time-return-the-local-or-utc-timestamp
"""
# time stamp when the script started.
timestamp = str(datetime.datetime.now()).split('.')[0].replace(":", "-")


sympy.init_printing()

s, t = sympy.symbols('s, t')
cf1, rf1, tauf1 = sympy.symbols(r"C_f1, R_f1, \tau_{f1}")
cf2, rf2, tauf2 = sympy.symbols(r"C_f2, R_f2, \tau_{f2}")
cf3, rf3, tauf3 = sympy.symbols(r"C_f3, R_f3, \tau_{f3}")


# FosterMatSample3x3 used for debugging at jupyter
FosterMatSample3x3 = sympy.Matrix([[cf1, rf1, tauf1],
                                  [cf2, rf2, tauf2],
                                  [cf3, rf3, tauf3]])


# ## Input data from the following file:

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


FosterMat = sympy.zeros(stages, 3)    # Final results will be stored here.

CauerMat = sympy.zeros(stages, 3)    # Input data will be stored here


for i in range(stages):
    CauerMat[i, 0] = sympy.Rational(c_list[i])

    # By default, reduced the accuracy level by not Rationalizing Rth.
    CauerMat[i, 1] = sympy.Rational(r_list[i]) if rational_rth else r_list[i]

    CauerMat[i, 2] = CauerMat[i, 0] * CauerMat[i, 1]


# ### As shown in the FosterMatSample3x3, variables line up in ascending order.
# Cf1 and Rf1 pair represents the first stage of the Foster model.
# They are next to Junction.
# So as the Cc1 and Rc1 of the Cauer model.


# # CauerMatrix
# This is a faster way to calculate the coeffcients of pc and qc
# in higher stages.

aMatCauer = sympy.zeros(stages, stages+1)
bMatCauer = sympy.zeros(stages+1, stages+1)

aMatCauer[0, 1] = CauerMat[stages-1, 1]
bMatCauer[0, 1] = 1
bMatCauer[1, 1] = CauerMat[stages-1, 2]

for i in range(2, stages+1):
    aMatCauer[:i, i] = \
        CauerMat[stages - i, 1] * bMatCauer[:i, i-1] + \
        aMatCauer[:i-1, i-1].row_insert(i-1, sympy.Matrix([0]))

    bMatCauer[:i+1, i] = \
        CauerMat[stages - i, 2] * \
        bMatCauer[:i, i-1].row_insert(0, sympy.Matrix([0])) + \
        bMatCauer[:i, i-1].row_insert(i, sympy.Matrix([0])) + \
        CauerMat[stages - i, 0] * \
        aMatCauer[:i-1, i-1].\
        row_insert(i-1,
                   sympy.Matrix([0])).row_insert(0,
                                                 sympy.Matrix([0]))

svector4Coeff_a = sympy.Matrix(stages, 1, lambda i, j: s**i)
svector4Coeff_b = sympy.Matrix(stages+1, 1, lambda i, j: s**i)
svector4Coeff_a, svector4Coeff_b, stages


pc = sympy.Poly(sympy.transpose(aMatCauer.col(stages)).dot(svector4Coeff_a), s)
qc = sympy.Poly(sympy.transpose(bMatCauer.col(stages)).dot(svector4Coeff_b), s)
rootVector = sympy.solve(qc, s)

for i in range(stages):
    # Tau_i is 1/abs(root_i)
    FosterMat[i, 2] = sympy.re((1/abs(rootVector[i])).simplify().together())
    # C_i can be calculated by reciprocal of pc/ ( d(qc)/ds ) |s=root_i,
    # from reference papers.
    FosterMat[i, 0] = \
        sympy.re((1/(pc/sympy.diff(qc, s)).
                  subs(s, rootVector[i])).simplify().together())
    # R_i can be yielded from Tau_i and C_i
    FosterMat[i, 1] = \
        sympy.re((FosterMat[i, 2]/FosterMat[i, 0]).simplify().together())


# # Final results in floating values

FosterMat_float = sympy.zeros(stages, 3)
for i in range(stages):
    for j in range(3):
        FosterMat_float[i, j] = float(FosterMat[i, j])

# ## draw Zth curve

if graph_enabled:
    # Draw each lines
    drawEachLines = 1

    Zth = 0
    Zth_each = sympy.zeros(stages)

    for i in range(stages):
        Zth_each[i] = \
            FosterMat_float[i, 1] * \
            (1 - sympy.exp(-t/FosterMat_float[i, 2]))
        Zth += Zth_each[i]

    type(int(sympy.ceiling(sympy.log(FosterMat_float[stages-1, 2] * 10, 10))))

    # time range is up to max Tau * 10 sec.
    tm = np.logspace(-6, int(sympy.ceiling(
        sympy.log(FosterMat_float[stages-1, 2] * 10, 10))))

    us = np.zeros(len(tm))
    if drawEachLines == 1:
        us_each = list()
        for j in range(stages):
            us_each.append(np.zeros(len(tm)))

    # substitute numeric values for u and y
    for i in range(len(tm)):
        us[i] = Zth.subs(t, tm[i])
    if drawEachLines == 1:
        for j in range(stages):
            for i in range(len(tm)):
                us_each[j][i] = Zth_each[j].subs(t, tm[i])

    # plot results
    plt.figure()

    plt.semilogx(tm, us, label='Zth')
    if drawEachLines == 1:
        for j in range(stages):
            plt.semilogx(tm, us_each[j], label="Zth_" + str(j+1))
    plt.legend()
    plt.xlabel('Time[log(t)]')
    plt.ylabel("Rth[K/W]")

    if save_graph :
        plt.savefig("OutputC2F_" + timestamp + "_semilog.png")

    if show_graph :
        plt.show()

    plt.loglog(tm, us, label='Zth')
    if drawEachLines == 1:
        for j in range(stages):
            plt.loglog(tm, us_each[j], label="Zth_" + str(j+1))
    plt.legend()
    plt.xlabel('Time[log(t)]')
    plt.ylabel("Rth[K/W]")

    if save_graph :
        plt.savefig("OutputC2F_" + timestamp + "_loglog.png")

    if show_graph :
        plt.show()


# # Resistance sum value check
Rc_all = 0
Rf_all = 0
for i in range(stages):
    Rc_all = Rc_all + CauerMat[i, 1]
    Rf_all = Rf_all + FosterMat_float[i, 1]
print("Rc_all = %g, Rf_all = %g" % (Rc_all, Rf_all))

epsilon = 1e-8
res = float(abs(Rc_all - Rf_all))
if res > epsilon:
    print("Rc_all and Rf_all don't match, ERROR!!!")


# # output results
with open(output_file, "w") as fileobj:
    tmpstring = ""
    # header
    tmpstring = "## Cauer2Foster results " + str(stages) + "stages\n"
    fileobj.write(tmpstring)
    tmpstring = "## Created: " + timestamp + "\n"
    fileobj.write(tmpstring)
    tmpstring = "# First stage (Cf1 and Rf1) is connected to Junction.\n"
    fileobj.write(tmpstring)
    tmpstring = "STAGES=\t" + str(stages) + "\n\n"
    fileobj.write(tmpstring)

    tmpstring = "# stage" + "\t" + "C_foster" + "\t\t" + \
                "R_foster" + "\t\t" + "tau_foster\n"
    fileobj.write(tmpstring)
    for i in range(stages):
        tmpstring = str(i+1) + "\t" + \
            str(FosterMat_float[i, 0]) + "\t" + \
            str(FosterMat_float[i, 1]) + "\t" + \
            str(FosterMat_float[i, 2]) + "\n"
        fileobj.write(tmpstring)