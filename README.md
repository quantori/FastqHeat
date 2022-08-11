[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)](https://github.com/quantori/FastqHeat/blob/master/CODE_OF_CONDUCT.md)

# FastqHeat

Copyright © 2021 [Quantori](https://www.quantori.com/). Custom Software Solutions. All rights reserved.

This program (wrapper) was created to help to download data from [SRA database](https://www.ncbi.nlm.nih.gov/sra/)
or [European Nucleotide Archive](https://www.ebi.ac.uk/ena/browser/home). It uses one of the three different methods to
download data depending on user's choice: **fasterq-dump** to download runs from NCBI's Sequence Read Archive (SRA), **
FTP** or **Aspera** to download runs from European Nucleotide Archive (ENA). This program also uses the **ENA Portal
API** to retrieve metadata.

Author: **Quantori**

## How it works

This program takes `ena` or `ncbi` as data source and a study identifier or run ids from its arguments and/or
textfile. It will then download the relevant files directly, or delegate downloading to `fasterq-dump` or Aspera CLI.
This program will also take care of obtaining required metadata, verify checksums of the downloaded files, and retry
failed downloads. Text file containing study identifiers or runs ids should have separate lines whit ids. Ids passed
to program arguments should be separated by comma `,`. For more information see CLI usage

## Installation

FastqHeat is being developed and tested under Python 3.9.x.

### Using pip

This will install the project and its external Python dependencies.
Depending on the method you choose for downloading data, you may have to install
additional command-line utilities, as explained in the [supported methods section](#supported-methods).

1. [Make sure you have installed a supported version of Python](https://www.python.org/downloads/).
2. Clone this project from GitHub or download it as an archive.
3. **Optional, but recommended:** create and activate a
   fresh [virtual environment](https://docs.python.org/3/library/venv.html#creating-virtual-environments).
4. Install it directly with `pip`.

Full example for Linux systems:

```bash:
$ git clone git@github.com:quantori/FastqHeat.git
$ python3 -m venv env
$ . env/bin/activate
$ pip install FastqHeat/
```

## CLI usage

This project supports command line usage. You can use `--help` to get information about the CLI.

```
Usage: python -m fastqheat [OPTIONS] COMMAND [ARGS]...

  This help message is also accessible via `python3 -m fastqheat --help`.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  ena
  ncbi

```

### ENA

```
Usage: python -m fastqheat ena [OPTIONS]                                     
                                                                             
Options:                                                                                       
  --skip-check BOOLEAN            Skip data check step.  [default: False]    
  --skip-download BOOLEAN         Skip data download step. Data check (if not
                                  skipped) will expect data to be in the     
                                  working directory  [default: False]        
  --attempts_interval INTEGER RANGE                                          
                                  Retry attempts interval in seconds in case 
                                  of network error.  [default: 0; x>=0]      
  --attempts INTEGER RANGE        Retry attempts in case of network error.   
                                  [default: 0; x>=0]                         
  --accession TEXT                List of accessions separated by comma. E.g 
                                  "SRP163674,SRR7969880,SRP163674"                              
  --config FILE                   Configuration file path.  [default:        
                                  (dynamic)]                                 
  --working-dir DIRECTORY         Working directory.  [default: <built-in    
                                  function getcwd>]                          
  --transport [binary|ftp]        Transport (method) to be user to download  
                                  data.  [default: binary]                   
  --metadata-file FILE            Metadata filepath  [default: (dynamic)]    
  --skip-download-metadata BOOLEAN                                           
                                  Skip metadata download step  [default:     
                                  False]                                     
  --help                          Show this message and exit.      push
```

### NCBI

```
Usage: python -m fastqheat ncbi [OPTIONS]                                    
                                                                             
Options:                                                                     
  --cpu-count INTEGER RANGE       Sets the amount of cpu-threads used by
                                  fasterq-dump (binary that downloads files
                                  from NCBI) and gzip (binary that zips files)
                                  [default: (dynamic)]                           
  --skip-check BOOLEAN            Skip data check step.  [default: False]    
  --skip-download BOOLEAN         Skip data download step. Data check (if not
                                  skipped) will expect data to be in the     
                                  working directory  [default: False]        
  --attempts_interval INTEGER RANGE                                          
                                  Retry attempts interval in seconds in case 
                                  of network error.  [default: 0; x>=0]      
  --attempts INTEGER RANGE        Retry attempts in case of network error.   
                                  [default: 0; x>=0]                         
  --accession TEXT                List of accessions separated by comma. E.g 
                                  "111,222,333"                              
  --config FILE                   Configuration file path.  [default:        
                                  (dynamic)]                                 
  --working-dir DIRECTORY         Working directory.  [default: <built-in    
                                  function getcwd>]                          
  --help                          Show this message and exit.   
```

### Working directory structure

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

## Supported methods

### Fasterq-dump

Requires `fasterq-dump` executable installed and added to `PATH`. Consult the
[official SRA Toolkit documentation](https://github.com/ncbi/sra-tools/wiki/HowTo:-Binary-Installation)
for detailed instructions. After downloading files, FastqHeat will compress them with
[`pigz`](https://github.com/madler/pigz) (can be installed with `apt` on Debian-based systems).

Both `fasterq-dump` and `pigz` support parallel execution and it's enabled by default. The `--cpu-count`
argument (see [CLI usage](#cli-usage)) controls exactly how many threads these programs will spawn.
The default number of threads is equal to the number of logical CPUs in the system.

Refer to the following sections for usage examples:

- [Download data for a single SRP via fasterq-dump](#download-data-for-a-single-srp-via-fasterq-dump)
- [Download data for a single SRR via fasterq-dump](#download-data-for-a-single-srr-via-fasterq-dump)

### Aspera Connect

Requires that you have `Aspera Connect` installed and added to your `PATH`.
Specifically, FastqHeat will invoke the `ascp` executable to transfer files.

An instruction how to install `Aspera Connect`:

#### download

`wget -qO- https://d3gcli72yxqn2z.cloudfront.net/downloads/connect/latest/bin/ibm-aspera-connect_4.2.1.116_linux.tar.gz | tar xvz`

You can find what the latest version is by going to the [official website](https://www.ibm.com/aspera/connect/),
clicking the right button of your mouse on "Download Aspera Connect <version number> for Linux" and pressing
"Copy link address".

#### run it

```
chmod +x ibm-aspera-connect_<version number>-linux_x86_64.sh

./ibm-aspera-connect_<version number>-linux_x86_64.sh
```

#### add it to the system path

```
export PATH=$PATH:~/.aspera/connect/bin/

echo 'export PATH=$PATH:~/.aspera/connect/bin/' >> ~/.bash_profile
```

#### check that everything works:

`ascp --version`

Refer to the following sections for usage examples:

- [Download data for a single SRP via Aspera CLI](#download-data-for-a-single-srp-via-aspera-cli)
- [Download data for a single SRR via Aspera CLI](#download-data-for-a-single-srr-via-aspera-cli)

### FTP

FastqHeat will download files directly from ENA.

Refer to the following sections for usage examples:

- [Download data for a single SRP via FTP](#download-data-for-a-single-srp-via-ftp)
- [Download data for a single SRR via FTP](#download-data-for-a-single-srr-via-ftp)

## Examples

### Download data for a single SRP via fasterq-dump

```bash
# Download SRP163674 data to the current directory using fasterq-dump
$ python3 -m fastqheat ncbi --accession=SRP163674
# Same, but output files to /tmp instead
$ python3 -m fastqheat ncbi --accession=SRP163674 --working-dir=/tmp
```

### Download data for a single SRR via fasterq-dump

```bash
# Download data for SRR7969880 to the current directory. Sets the number of cores
# to use by fasterq-dump and pigz, overriding the default setting
$ python3 -m fastqheat ncbi --accession=SRR7969880 --cpu-count=8
```

### Download data for a single SRP via Aspera CLI

```bash
# Download data related to SRP163674 to the current directory using Aspera CLI
$ python3 -m fastqheat ena --accession=SRP163674
# Same, but output files to /tmp instead
$ python3 -m fastqheat ena --accession=SRP163674 --working-dir=/tmp
```

### Download data for a single SRR via Aspera CLI

```bash
# Download data for SRR7969880 to /tmp
$ python3 -m fastqheat ena --accession=SRR7969880 --working-dir=/tmp
```

### Download data for a single SRP via FTP

```bash
# Download data related to SRP163674 to the current directory using FTP
$ python3 -m fastqheat ena --transport=ftp --accession=SRP163674
# Same, but output files to /tmp instead
$ python3 -m fastqheat ena --transport=ftp --accession=SRP163674 --out /tmp
```

### Download data for a single SRR via FTP

```bash
# Download data for SRR7969880 to /tmp
$ python3 -m fastqheat ena --transport=ftp --accession=SRR7969880 --out /tmp
```

### Download data for multiple SRR or SRP identifiers

```bash
$ python3 -m fastqheat ena --accession=SRR7969880,SRP150545 --out /tmp
```

Or create a `.txt` file containing identifiers of SRA studies or runs.

```bash

# Download data for every entry in input_file.txt using fasterq-dump with 6 threads
$ python3 -m fastqheat ena --accession-file=/path/to/input_file.txt --cpu-count=6
```

Each identifier should be placed on a separate line. Example of a valid file:

```bash
$ cat /path/to/input_file.txt
SRP163674
SRX4720625
SRP150545
```

## Development

Development happens on the `dev` branch. `master` is the stable branch.

Clone the project, enter the project directory, and switch to the development branch:

```bash
~$ git clone git@github.com:quantori/FastqHeat.git
~$ cd FastqHeat/
~/FastqHeat$ git checkout dev
```

Install [`poetry`](https://python-poetry.org/), then install the project:

```bash
~/FastqHeat$ poetry install  # NOTE: includes dev dependencies
```

> **NOTE**: to run commands within the project's virtual environment you will have
> to activate Poetry's shell (`poetry shell`) or run them via `poetry run`. It is also possible to, install the project
> via `pip` in editable mode (`-e`)
> instead, and then install project's dependencies with `poetry install --no-root`.

Make sure you've installed optional command-line utilities as well.
If you add new Python dependencies, they should be included in
[`pyproject.toml`](pyproject.toml) in the relevant sections (don't forget
to recreate [`poetry.lock`](poetry.lock) after you're done).

To check that everything is in order:

```bash
~/FastqHeat$ make format  # Formats code
~/FastqHeat$ make lint  # Runs linters against code
~/FastqHeat$ make test  # Runs unit tests
```

## Contributing

We welcome participation from all members of the community. We ask that all interactions
conform to our [Code of Conduct](CODE_OF_CONDUCT.md).

## Questions?

Feel free to open an [issue](https://github.com/quantori/FastqHeat/issues)!
