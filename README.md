# rotation-plots3d

A package written in Python 3.12 to assist with generating 3D plots and statistical analysis of time series X, Y, Z, roll, pitch, yaw data.

![3D Scatterplot](/assets/3D%20plot.png)

## Description

This package contains methods to generate 3D plots of x, y, z, roll, pitch, yaw data and analyze for repeatability of measurements using a gage repeatability method. It will also generate a stats dataframe for the x, y, z, roll, pitch, yaw and x-prime, y-prime, and z-prime axes.

## Installation

To install this python package locally, please use:  
`pip install rotation-plots3d`

## Basic Usage

The following examples provide a high-level summary of how to use the API.

### Instantitating the OTA Class

Create the ObjectTrackingAnimation class and run the format_raw_data() method.

```python
from rotation_plots3d import ObjectTrackingAnimation

ota = ObjectTrackingAnimation(input_path='files', graph_title="My Creative Title")
```

### Load Data and Create a Graph

```python
ota.load() # loads data into the class as an attribute
ota.create_graph('example.csv','1')
# will generate a plot of the example.csv file located in the output_path directory.
```

### Run Statistics on Data

```python
import os

files = os.listdir('files')

# create a list of every output file repeated by the number
# of dataranges per file. In this case 8x.
filenames = []
for file in files:
    filenames += 8 * [file]

# indicate which device to track for each file. In this case, it is
# device "1" for every file.
device = ['1'] * len(filenames)

# for each file, create a list of start and stop time ranges
datarange = [[0,3],[3,6],[6,9],[9,12],[145,150],[150,155],[155,160],[160,165]]

# create the stats dataframe
df = ota.stats_dataframe(filename=filenames,device=device,datarange=datarange)

print(df)
#    Parameter                                               mean  ... angle_of_shift_degrees_vs_initial  angle_of_shift_degrees_vs_initial_error
# 0          X                                           2.401588  ...                               NaN                                      NaN
# 1          X                                           2.401905  ...                               NaN                                      NaN
# 2          X                                           2.402598  ...                               NaN                                      NaN
# 3          X                                           2.403336  ...                               NaN                                      NaN
# 4          X                                           2.391486  ...                               NaN                                      NaN
# ..       ...                                                ...  ...                               ...                                      ...
# 3    z_prime  [0.6388455401133175, 0.00028297720143531126, -...  ...                          0.057028                                 0.000948
# 4    z_prime  [0.6446987414563102, 0.002794264889296324, -0....  ...                          0.405209                                 0.000726
# 5    z_prime  [0.6440696849596658, 0.0028438830124556712, -0...  ...                          0.362399                                 0.000474
# 6    z_prime  [0.6499854657845796, -0.0005017454685925038, -...  ...                          0.781513                                 0.175948
# 7    z_prime  [0.6443998187565277, 0.0021319551787689173, -0...  ...                          0.372250                                 0.013982

# generate gage repeatability reports
ota.gage_repeatability(filename=filenames,device=device,datarange=datarange)

# will return 6 matplotlib plots and print the following to the console:
#                     StdDev (SD)  StudyVar (6*SD)  % Study Var
# Source                                                       
# Gage Repeatability     0.000256         0.001539     6.922392
# Part to Part           0.003696         0.022175    99.760115
# Total variation        0.003705         0.022228   100.000000

# Automotive Industry Action Group (AIAG) measurement system assessment:
# -------------------
# Total Gage Repeatability factor: 6.922
# <10% --> Acceptable measurement system
```

![gage_R](assets/Z_repeatability_gage_R.png)

## Authors and acknowledgment

John Glauber  
<johnbglauber@gmail.com>

This software relies heavily upon the Plotly package and the pyPETB package. A huge thanks to those teams for creating such awesome tools.

## License

MIT.

## Project status

In development.
