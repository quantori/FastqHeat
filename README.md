[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)](https://github.com/quantori/FastqHeat/blob/master/CODE_OF_CONDUCT.md)

# FastqHeat

Copyright © 2021 [Quantori](https://www.quantori.com/). Custom Software Solutions. All rights reserved.

This program (wrapper) was created to help to download data from
[SRA database](https://www.ncbi.nlm.nih.gov/sra/).
It uses one of the three different methods to download data depending on user's choice:
**fasterq-dump** to download runs from NCBI's Sequence Read Archive (SRA), **FTP** or
**Aspera** to download runs from European Nucleotide Archive (ENA). This program also uses
the **ENA Portal API** to retrieve metadata.

Author: **Anna Ivanova**

## How it works

This program takes either an SRA study identifier or run id, *or* path to a `.txt` file
that contains SRA study identifiers or runs ids on separate lines. It will then download the
relevant files directly, or delegate downloading to `fasterq-dump` or Aspera CLI. This program
will also take care of obtaining required metadata, verify checksums of the downloaded files,
and retry failed downloads.

## CLI usage

This project supports command line usage. Here's the complete list of supported arguments
along with explanation:

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
  -a ATTEMPTS, --attempts ATTEMPTS
                        Number of attempts to download files (two by default)
```

This help message is also accessible via `python3 -m fastqheat --help`.

## Compatibility

FastqHeat is being developed and tested under Python 3.9.x.

## Installation

 1. [Make sure you have installed a supported version of Python](https://www.python.org/downloads/).

 2. Clone this project from GitHub or download it as an archive.

 3. **Optional, but recommended:** create and activate a fresh
 [virtual environment](https://docs.python.org/3/library/venv.html#creating-virtual-environments).

 4. Install it directly with `pip`.

Full example for Linux systems:

```bash
$ git clone git@github.com:quantori/FastqHeat.git
$ python3 -m venv env
$ . env/bin/activate
$ pip install FastqHeat/
```

This will install the project and its external Python dependencies (currently the only external Python
dependency is `requests`). Depending on the method you choose for downloading data, you may have to install
additional command-line utilities, as explained in the section below.

## Supported methods

### Fasterq-dump

Requires `fasterq-dump` executable installed and added to `PATH`. Consult the
[official SRA Toolkit documentation](https://github.com/ncbi/sra-tools/wiki/HowTo:-Binary-Installation)
for detailed instructions. After downloading files, FastqHeat will compress them with
[`pigz`](https://github.com/madler/pigz) (can be installed with `apt` on Debian-based systems).

Both `fasterq-dump` and `pigz` support parallel execution and it's enabled by default. The `-c`/`--cores`
argument (see [CLI usage](#cli-usage)) controls exactly how many threads these programs will spawn.
The default number of threads is equal to the number of logical CPUs in the system.

Refer to the following sections for usage examples:

 - [Download data for a single SRP via fasterq-dump](#download-data-for-a-single-srp-via-fasterq-dump)
 - [Download data for a single SRR via fasterq-dump](#download-data-for-a-single-srr-via-fasterq-dump)

### Aspera CLI

Requires that you have [Aspera CLI](https://www.ibm.com/docs/en/aci/3.9.2?topic=aspera-command-line-interface-user-guide-linux) installed and added to your `PATH`.
Specifically, FastqHeat will invoke the `ascp` executable to transfer files.

Refer to the following sections for usage examples:

 - [Download data for a single SRP via Aspera CLI](#download-data-for-a-single-srp-via-aspera-cli)
 - [Download data for a single SRR via Aspera CLI](#download-data-for-a-single-srr-via-aspera-cli)
 
### FTP

FastqHeat will download files directly from ENA.

Refer to the following sections for usage examples:

 - [Download data for a single SRP via FTP](#download-data-for-a-single-srp-via-ftp)
 - [Download data for a single SRR via FTP](#download-data-for-a-single-srr-via-ftp)
 
## Using FastqHeat

For every study or run given, FastqHeat will download data for all runs and place them in
a specific hierarchical directory structure.

For example, if you wish to download data for `SRP163674` to `/some/output/directory`,
FastqHeat will arrange downloaded files for runs in the following directory structure:

```
/some/output/directory/
├── SRR7969880
│ └── SRR7969880.fastq.gz
├── SRR7969881
│ └── SRR7969881.fastq.gz
├── SRR7969882
│ └── SRR7969882.fastq.gz
├── SRR7969883
│ └── SRR7969883.fastq.gz
├── SRR7969884
│ └── SRR7969884.fastq.gz
...
```

Here's an example for `SRX4720625`:

```
/some/output/directory/
└── SRR7882015
  ├── SRR7882015_1.fastq.gz
  └── SRR7882015_2.fastq.gz
```

If instead you download data just for `SRR7969880`:

```
/some/output/directory/
└── SRR7969880
    └── SRR7969880.fastq.gz
```

Note that the directory structure will always be exactly the same, regardless of the method
you selected.

### Download data for a single SRP via fasterq-dump

```bash
# Download SRP163674 data to the current directory using fasterq-dump
$ python3 -m fastqheat SRP163674 -M q
# Same, but output files to /tmp instead (note that -M q is the default)
$ python3 -m fastqheat SRP163674 --out /tmp
```

### Download data for a single SRR via fasterq-dump

```bash
# Download data for SRR7969880 to the current directory. Sets the number of cores
# to use by fasterq-dump and pigz, overriding the default setting
$ python3 -m fastqheat SRR7969880 --cores 8
```

### Download data for a single SRP via Aspera CLI

```bash
# Download data related to SRP163674 to the current directory using Aspera CLI
$ python3 -m fastqheat SRP163674 -M a
# Same, but output files to /tmp instead
$ python3 -m fastqheat SRP163674 -M a --out /tmp
```

### Download data for a single SRR via Aspera CLI

```bash
# Download data for SRR7969880 to /tmp
$ python3 -m fastqheat SRR7969880 -M a -O /tmp
```

### Download data for a single SRP via FTP

```bash
# Download data related to SRP163674 to the current directory using FTP
$ python3 -m fastqheat SRP163674 -M f
# Same, but output files to /tmp instead
$ python3 -m fastqheat SRP163674 -M f --out /tmp
```

### Download data for a single SRR via FTP

```bash
# Download data for SRR7969880 to /tmp
$ python3 -m fastqheat SRR7969880 -M f -O /tmp
```

### Download data for multiple SRR or SRP identifiers

Create a `.txt` file containing identifiers of SRA studies or runs. Each identifier should be
placed on a separate line. Example of a valid file:

```bash
$ cat /path/to/input_file.txt
SRP163674
SRX4720625
SRP150545
```

Provide the path to this file as the first command line argument. Other command line arguments
have the same meaning as for downloads by a single identifier:

```bash
# Download data for every entry in input_file.txt using fasterq-dump with 6 threads
$ python3 -m fastqheat /path/to/input_file.txt -M q --cores 6
```

## Development

Refer to [DEVNOTES.md](DEVNOTES.md).

## Contributing

We welcome participation from all members of the community. We ask that all interactions
conform to our [Code of Conduct](CODE_OF_CONDUCT.md).

## Questions?

Feel free to open an [issue](https://github.com/quantori/FastqHeat/issues)!
