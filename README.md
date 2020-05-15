# FosterCauer_CauerFoster

A simple Foster to Cauer / Cauer to Foster conversion tools using Python3.7.

### Usage

First of all, an input file which has a specific format is required.
For your convenience, I added a conversion tool from Spice format to "myCR" format.

Since it is a simple format, it can be prepared manually.
Please use input.txt as an example.

input.txt
```
# make sure to put a space (or a tab) between "STAGES=" and the number here.
STAGES=	3

# Empty rows will be ignored.

# stage	C	        R
1       1.00E-06	5.00E-02
2	1.10E-03	7.00E-01
3	1.20E-00	4.00E-00
```

Here is an example to convert Foster network to Cauer.
```
$ python Foster2Cauer.py input.txt output.txt
```

Here is an example converting Spice format to "myCR" format.
```
$ python Spice2myCR.py inputSpice.txt output.txt
```

Alternatively, "myCR" format can be converted back to Spice format.
If the network is Foster network, use "-f" flag (By default, it generates Cauer network Spice format).
```
$ python myCRformat2Spice.py input.txt output.txt
```

Either tools accept "-h" for help.


### Limitation

Be careful using this tool for higher number of network stages (let's say, n>30).
Calculation cost increases O(n^2) for Foster2Cauer.py and O(exp(n)) for Cauer2Foster.py.

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details
