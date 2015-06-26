
Iterative Mapping and Phasing
-------------

This repository describes a workflow that takes a [Cergentis TLA](http://www.cergentis.com/tla-technology/tla-technology) prepared sample sequenced on PacBio and extracts phasing information based on heterozygote SNPs.

Installation
-------------

The scripts require BLASR, samtools, bcftools, and HAPCUT to be in your path. One way to get the first three tools is to install them using [LinuxBrew](http://brew.sh/linuxbrew/):

```
brew install blasr samtools bcftools
```

HAPCUT binaries can be downloaded from: https://sites.google.com/site/vibansal/software/hapcut

After extracting, it can be placed on your path for the current session:

```
export PATH=/path/to/HAPCUT-v0.7/:$PATH
```

The workflow was tested with these versions of the software on Linux:

```
python=2.7
blasr=2.1
samtools=1.2
bcftools=1.2
HAPCUT=0.7
```

Running
----------

First generate Reads of Insert from SMRT&reg; cell data. The easiest way is to use the `RS_ReadsOfInsert` protocol in SMRT Portal, using default parameters.

The data from `reads_of_insert.fasta` can be aligned and phased using an invocation similar to this:

```
/path/to/phase.sh reads_of_insert.fasta hg19.fasta chr17:41,194,312-41,279,500 output_dir/
```

This does the following steps:

* Iteratively aligns `reads_of_insert.fasta` to `hg19.fasta` using `map.py` and `blasr`
* Determines SNPs in BRCA1 (`chr17:41,194,312-41,279,500`) using `samtools` and `bcftools`
* Generates a paired end formatted sam file for use with `HAPCUT` using the `pair.py` script
* Calculates phasing using the high quality SNPs via `HAPCUT`

The intermediate files and results are placed in `output_dir/`. The key output is `output_haplotype_file` which reports the phasing information. The file format is described at https://github.com/vibansal/hapcut#format-of-input-and-output-files

Notes on the Analysis
---------

Each read typically consists of several fragments ligated together, all from nearby genomic locations on the same allele. To get mapping information for each fragment, we first map the entire read, and then for unmapped portions of the read, iteratively repeat the process. This is done via `map.py`.

The phasing is performed by HAPCUT, which supports mate pair style reads. Because the Cergentis/PacBio data can have more than two fragments per read, the data needs to be represented in a mate pair style manner. This is done via `pair.py`.

