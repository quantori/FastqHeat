[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)](https://github.com/quantori/FastqHeat/blob/master/CODE_OF_CONDUCT.md)

# FastqHeat

Copyright © 2021 [Quantori](https://www.quantori.com/). Custom Software Solutions. All rights reserved.

This program (wrapper) was created to help to download metagenomic data from SRA database.
It uses 3 different methods to download data depending on user's choice: **fasterq-dump** to download runs from NCBI's Sequence Read Archive (SRA), **FTP** and **Aspera** to download runs from European Nucleotide Archive (ENA).
This program allows to download metadata from **ENA Portal API** too.

Language: **Python3**  
Author: **Anna Ivanova**  

## The problems this wrapper decides:

For downloading data from [SRA database](https://www.ncbi.nlm.nih.gov/sra/) often use the program **fasterq-dump**. It is the convenient tool but it has its flaws.  

 - It's possible to download only one by one a SRA experiments. User must run the command for each experiment and manually input the identifier of each.
 - For batch download it is recommended to use [while cycle](https://bioinformaticsworkbook.org/dataAcquisition/fileTransfer/sra.html). But this method is inconvenient when you need to download only certain list of identifiers or visa versa you do not want to download certain large files you previously downloaded. You can not exclude these files.  
 - In time of downloading of a file the connect to SRA database can be lost. Because of that after downloading you need to manually check the size of the loaded data. This is additional user's operation.  

So this project is a tool for:

 - downloading all experiments by one command;
 - downloading only certain experiments or exclude from list any experiments;
 - checking results of downloading;
 - downloading experimens using different faster methods;
 - downloading metadata in different file formats;
 - downloading multiple study accession as well as signle one.

## Installation.
Read [DEVNOTES.md](https://github.com/quantori/FastqHeat/blob/master/DEVNOTES.md)

## How it works.
The fastqHeat connect with NCBI database through API and has API key. It use NCBI services **esearch** and **efetch**.

**Warning:** The tool fasterq-dump (sra toolkit) must be preinstalled in case runs are downloaded with fasterq_dump, but if runs are downloaded using Aspera, then Asper CLI should be preinstalled.   


The tool fasterq-dump as a parameter use a run identifier. A run id is within an experiment and has SRR prefix.  
For this wrapper you need to put SRA Study identifier, which starts from SRP prefix, or name of .txt file, which contains multiple study accessions.  

    Parameters:

    positional arguments:
            term              The name of Study/Sample/Experiment/Submission
                              Accession or the name of the file with
                              Study Accessions

    optional arguments:
        -h, --help            show this help message and exit
        -L, --log             To point logging level (debug, info, warning,
                              error. "info" by default)
        -M, --method          Method of downloading fastq or fastq.gz file.
                              There are 3 options for downloading data: FTP,
                              Aspera and fasterq_dump. To use Aspera specify
                              after -M command a, to use FTP specify f, and
                              for fasterq_dump specify q.
        -E, --explore         Explorer chooses between 2 options of what to do
                              with accession download metadata or run
                              itself from SRA/ENA. To download metadata
                              it should be followed with i, to download
                              runs- r.
        -F, --format          File format of downloaded metadata file.
                              3 options are available: CSV, JSON, YAML.
                              To download CSV choose c, JSON- j and YAML- y.
        -V, --value           Values for ENA report to retrieve metadata. By
                              default values are provided, but can be manually
                              entered too. Default values are: study_accession,
                              sample_accession,experiment_accession,read_count,base_count.
                              To write with '"," and without spaces.
        -N, --only            The only_list. The list of the certain items
                              to download.
                              To write with '"," and without spaces.
        -P, --skip            The skip_list. The list of the items to do not
                              download. To write with ',' and without spaces.
                              Warning: Skip parameter has the biggest priority.
                              If one run id has been pointed in skip_list and
                              in only_list, this run will be skipped.
        -O, --out             Output directory
        -S, --show            show lxml file with all Run data (yes/no)

    Template of query:
            fastqheat.py {SRA Study identifier name SRP...} --skip_list {run id SRR...} --show yes 
            
            fastqheat.py {SRA Study identifier name SRP...} --only_list {run id SRR...} 

    Ex 1: download all into the directory
                        python3 fastqheat.py SRP163674 --out /home/user/tmp
    Ex 2: download all files except some pointed items.
                        python3 fastqheat.py SRP163674 -P "SRR7969889,SRR7969890,SRR7969890"
    Ex 3: download only pointed items and show the details of the loading process.
                        python3 fastqheat.py SRP163674 -N "SRR7969891,SRR7969892" --show yes
    Ex 4: download all files using Aspera
                        python3 fastqheat.py SRP163674 -M a
    Ex 5: download metadata and format of file is CSV
                        python3 fastqheat.py SRP163674 -E i -F c
    Ex 6: download metadata, format of file is YAML and values are experiment_title, base_count
                        python3 fastqheat.py SRP163674 -E i -F c -V "experiment_title,base_count"
    Ex 7: download runs of multiple study accessions from .txt file using fasterq_dump
                        python3 fastqheat.py *.txt -M q
