[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)](https://github.com/quantori/FastqHeat/blob/master/CODE_OF_CONDUCT.md)

# FastqHeat

Copyright © 2021 [Quantori](https://www.quantori.com/). Custom Software Solutions. All rights reserved.

This program (wrapper) was created to help to download metagenomic data from
[SRA database](https://www.ncbi.nlm.nih.gov/sra/).
It uses one of the three different methods to download data depending on user's choice:
**fasterq-dump** to download runs from NCBI's Sequence Read Archive (SRA), **FTP** or
**Aspera** to download runs from European Nucleotide Archive (ENA). This program also uses
the **ENA Portal API** to retrieve metadata.

Author: **Anna Ivanova**

## How it works

This program takes either an SRA study identifier or run id, *or* a name of a `.txt` file
containing SRA study identifiers or runs ids on separate lines. It will then download the
relevant files directly, or delegate downloading to `fasterq-dump` or Aspera CLI. This program
will also take care of checksum verification of the downloaded files and retry failed downloads.

## Compatibility

FastqHeat needs Python 3.7 or newer.

## Installation

Clone the project from GitHub or download it as an archive, then install it directly
with `pip` (consider creating a fresh [virtual environment](https://docs.python.org/3/library/venv.html#creating-virtual-environments) for that). Example:

```bash
~$ git clone git@github.com:quantori/FastqHeat.git
~$ pip install FastqHeat/
```

Depending on the method you choose for downloading data, you may have to install additional
command-line utilities, as explained below.

## Supported methods

### Fasterq-dump

Requires `fasterq-dump` executable installed and added to `PATH`. Consult the
[SRA Toolkit documentation](https://github.com/ncbi/sra-tools/wiki/HowTo:-Binary-Installation)
for detailed instructions. After downloading files, this program will compress them with
[`pigz`](https://github.com/madler/pigz) (can be installed with `apt` on Debian-based systems).

### Aspera CLI

Requires that you have [Aspera CLI](https://www.ibm.com/docs/en/aci/3.9.2?topic=aspera-command-line-interface-user-guide-linux) installed and added to your `PATH`.
Specifically, this program will invoke the `ascp` executable to transfer files.

### FTP

Will download files directly from ENA.

## CLI

```
usage: __main__.py [-h] [-L {debug,info,warning,error}] [-O OUT] [-M METHOD] [-c CORES] [-r RETRIES] term

positional arguments:
  term                  The name of SRA Study identifier, looks like SRP... or ERP... or DRP...
                        or .txt file name which includes multiple SRA Study identifiers

options:
  -h, --help            show this help message and exit
  -L {debug,info,warning,error}, --log {debug,info,warning,error}
                        Logging level
  -O OUT, --out OUT     Output directory
  -M METHOD, --method METHOD
                        Choose different type of methods that should be used for data retrieval:
                        Aspera (a), FTP (f), fasterq_dump (q). By default it is fasterq_dump (q)
  -c CORES, --cores CORES
                        Number of CPU cores to utilise (for subcommands that support parallel execution)
  -r RETRIES, --retries RETRIES
                        Retry failed requests this number of times
```

This is also accessible as `python3 -m fastqheat -h/--help`.

## Examples

```bash
# Download SRP163674 data to the current directory using fasterq-dump
$ python3 -m fastqheat SRP163674
# Same, but output files to /tmp instead
$ python3 -m fastqheat SRP163674 --out /tmp
# Download data related to SRP163674 using FTP
$ python3 -m fastqheat SRP163674 -M f
# Download data related to SRP163674 using Aspera CLI
$ python3 -m fastqheat SRP163674 -M a
# Download data for multiple SRA studies from a prepared .txt file using FTP
$ cat input_file.txt
SRP163674
SRP150545
$ python3 -m fastqheat input_file.txt -M f
```

## Development

Refer to [DEVNOTES.md](DEVNOTES.md).
