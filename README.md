# FastqHeat

This program (wrapper) was created to help to download metagenomic data from SRA database.
It uses the software **fastq-dump** converting data from **sra** format to **fastq** format. 

Language: **Python3**  
Author: **Anna Ivanova**  

## The problems this wrapper decides:

For downloading data from [SRA database](https://www.ncbi.nlm.nih.gov/sra/) often use the program **fastq-dump**. It is the convenient tool but it has its flaws.  

 - It's possible to download only one by one a SRA experiments. User must run the command for each experiment and manually input the identifier of each.
 - For batch download it is recommended to use [while cycle](https://bioinformaticsworkbook.org/dataAcquisition/fileTransfer/sra.html). But this method is inconvenient when you need to download only certain list of identifiers or visa versa you do not want to download certain large files you previously downloaded. You can not exclude these files.  
 - In time of downloading of a file the connect to SRA database can be lost. Because of that after downloading you need to manually check the size of the loaded data. This is additional user's operation.  

So this project is a tool for:

 - downloading all experiments by one command;
 - downloading only certain experiments or exclude from list any experiments;
 - checking results of downloading.

## How it works.
The fastqHeat connect with NCBI database through API and has API key. It use NCBI services **esearch** and **efetch**.

**Warning:** The tool fastq-dump (sra toolkit) must be preinstalled.  
[Installation of sra toolkit](https://ncbi.github.io/sra-tools/install_config.html).  
[Installation of sra toolkit from binaries](https://github.com/ncbi/sra-tools/wiki/HowTo:-Binary-Installation) - more useful (it's my opinion)  

Also you need to add a path to the tools permanently(!).  
On MacOS you need add the lines `/Users/username/path_to_the_sra/sratoolkit.(version)/bin` into the file `/etc/paths`.(And restart the terminal).
To check adding type `which fastq-dump`. You must see the path to the sra tools.

The tool fastq-dump as a parameter use a run identifier. A run id is within an experiment and has SRR prefix.  
For this wrapper you need to put SRA Study identifier. It starts from SRP prefix.  


        Parameters:
    
    positional arguments:
            term              The name of SRA Study identifier, looks like SRP... or ERP... or DRP...

    optional arguments:
        -h, --help            show this help message and exit
        -L, --log             To point logging level (debug, info, warning, error. "info" by default)
        -N, --only            The only_list. The list of the certain items to download.
                              To write with '"," and without spaces.
        -P, --skip            The skip_list. The list of the items to do not download. To write with ',' and without spaces.
                              Warning: Skip parameter has the biggest priority.
                              If one run id has been pointed in skip_list and in only_list, this run will be skipped.
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
    
     
    
### To do in the future  

1. CI/CD
3. To manage fastq-dump parameters 
4. To add a possibility of downloading from [European Nucleotide Archive](https://www.ebi.ac.uk/ena/data/view/PRJEB21528)
  