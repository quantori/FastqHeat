## Installation instructions
* Ensure you have fastq-dump installed. [Installation of sra toolkit from binaries](https://github.com/ncbi/sra-tools/wiki/HowTo:-Binary-Installation)

* Also you need to add a path to the tools permanently(!).  
On MacOS you need add the lines `/Users/username/path_to_the_sra/sratoolkit.(version)/bin` into the file `/etc/paths`. (And restart the terminal).
To check adding type `which fastq-dump`. You must see the path to the sra tools.

* Download the repository

`git clone https://github.com/quantori/FastqHeat.git`

`cd FastqHeat`

* Install python dependencies

`pip3 install -r requirements.txt`

* Script is ready to be used

`py.test -v tests/test_input.py`

`python3 fastqheat.py -h`

