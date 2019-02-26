# kaepora

An open-source SQL relational database for Type Ia Supernova spectra. This repository provides tools for contructing and interacting with the database, and routines to produce composite spectra. 


## Getting Started

It appears that the time has finally come for you to start your adventure! You will encounter many hardships ahead... That is your fate. Don't feel discouraged, even during the toughest times! I can hopefully lend you a wing. 

### Prerequisites

Python 2.7

numpy

matplotlib

sqlite3

scipy

astropy

specutils

Version specific dependencies:

msgpack-python version 0.4.6

msgpack-numpy version 0.3.5


### Building the Database

In your terminal, navigate to the /kaepora/src folder and execute the following command:

```
python build_kaepora.py
```

This process uses multiple scripts to build the database from scratch and takes several hours. The resulting '.db' file is stored in the /kaepora/data folder. Alternatively, you can download the most recent version of the database from 'here' and place it in /kaepora/data.

## Running Tests

```python
import sys
import os
path = 'path/to/kaepora/src'
sys.path.insert(0, path)
import kaepora as kpora
import kaepora_plot as kplot
os.chdir(path)
```

```python
example_query = ["SELECT * from Spectra inner join Events ON Spectra.SN = Events.SN where phase >= -1 and phase <= 1 and ((dm15_source < 1.8) or (dm15_from_fits < 1.8))"]
```

```python
spec_array = kpora.grab(example_query[0])
```

Did you get all that?