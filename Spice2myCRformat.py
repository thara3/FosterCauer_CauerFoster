# # Spice SubCircuit format to myCR data format converter
# 2019/05/06 created by Tom HARA
import argparse
import datetime

# version of this script
myVersion = '0.0.01'

##############################################################################
# arg parsing
##############################################################################
parser = argparse.ArgumentParser(
    prog='Spice2myCRformat.py',
    usage='Spice SubCircuit format to myCR data format converter.',
    epilog='end',
    add_help=True
    )

parser.add_argument('input_file', help='specify input filename',
                    action='store', type=str)
parser.add_argument('output_file', help='specify output filename',
                    action='store', type=str)

parser.add_argument('--version', action='version',
                    version='%(prog)s ' + myVersion)

args = parser.parse_args()

# Input file and output file:
input_file = args.input_file
output_file = args.output_file

##############################################################################

"""
https://stackoverflow.com/questions/13890935/does-pythons-time-time-return-the-local-or-utc-timestamp
"""
# time stamp when the script started.
timestamp = str(datetime.datetime.now()).split('.')[0].replace(":", "-")

with open(input_file, 'r', encoding="utf-8") as fileobj:
    datastr = fileobj.read()         # read all data from a file
    adatastr = datastr.rstrip()      # remove the last "\n"
    datalist = adatastr.split("\n")  # create a list (size: n row * 1 column)

c_list = list()                      # a list for foster network Cth
r_list = list()                      # a list for foster network Rth
comment_list = list()                # a list for comment rows

for line in datalist:                # read one row at a time
    tmplist = line.split()       # split a row into a list
    # print(tmplist)
    if tmplist == []:                # skip empty rows
        continue
    if tmplist[0][0] == '*':
        comment_list.append(line)
        continue
    if tmplist[0][0:7] == ".SUBCKT":
        #  Number of Stages = LastNodeNum - 1
        stages = int(tmplist[3]) - 1
        print("stages = " + str(stages))
        continue
    # start reading actual data
    if tmplist[0][0] == 'C':
        c_list.append(float(tmplist[3]))
    elif tmplist[0][0] == 'R':
        r_list.append(float(tmplist[3]))

assert len(r_list) == len(c_list), \
    "error! r_list and c_list has different size!"
assert len(r_list) == stages,  \
    "error! r_list size is not equal to # of stages!"

with open(output_file, "w") as fileobj:
    tmpstring = ""
    # header
    tmpstring = "## Spice SubCircuit format to myCR data format\n"
    fileobj.write(tmpstring)
    tmpstring = "## Created: " + timestamp + "\n"
    fileobj.write(tmpstring)
    tmpstring = "# First stage (C1 and R1) is connected to Junction.\n"
    fileobj.write(tmpstring)
    tmpstring = "# Comments from original file:\n"
    fileobj.write(tmpstring)
    for comments in comment_list:
        tmpstring = "# " + comments + "\n"
        fileobj.write(tmpstring)

    tmpstring = "STAGES=\t" + str(stages) + "\n\n"
    fileobj.write(tmpstring)

    tmpstring = "# stage" + "\t" + "C" + "\t\t\t" + \
                "R" + "\t\t\t" + "tau\n"
    fileobj.write(tmpstring)

    for stageNum, (cval, rval) in enumerate(zip(c_list, r_list), 1):
        tmpstring = str(stageNum) + "\t" + \
            str(cval) + "\t" + \
            str(rval) + "\t" + \
            str(cval * rval) + "\n"
        fileobj.write(tmpstring)
