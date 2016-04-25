
Iterative Mapping and Phasing
-------------

This repository describes a workflow that takes a [Cergentis TLA](http://www.cergentis.com/tla-technology/tla-technology) prepared sample sequenced on a PacBio&reg; RS II and extracts phasing information based on heterozygous SNPs.

Installation
-------------

To use the scripts, first clone this repository:

```
git clone https://github.com/lhon/iterative-mapping-phasing.git
```

The scripts require BLASR, samtools, and bcftools to be in your path. One way to get these tools is to install them using [LinuxBrew](http://brew.sh/linuxbrew/):

```
brew install blasr samtools bcftools
```

The workflow was tested with the following software versions on Linux:

```
python=2.7
blasr=2.1
samtools=1.2
bcftools=1.2
```

[HAPCUT](https://sites.google.com/site/vibansal/software/hapcut) was recompiled with a change to allow paired end analysis to work properly; the resulting binaries are included in this repository. The change is documented at https://github.com/lhon/hapcut 

Running
----------

First generate Reads of Insert from SMRT&reg; cell data. The easiest way is to use the `RS_ReadsOfInsert` protocol in SMRT Portal, using default parameters.

The data from `reads_of_insert.fasta` can then be aligned and phased using a command similar to this:

```
/path/to/phase.sh reads_of_insert.fasta hg19.fasta chr17:41,194,312-41,279,500 output_dir/
```

This performs the following steps:

* Iteratively aligns `reads_of_insert.fasta` to `hg19.fasta` using `map.py` and `blasr`
* Determines SNPs in BRCA1 (`chr17:41,194,312-41,279,500`) using `samtools` and `bcftools`
* Generates a paired end formatted sam file for use with `HAPCUT` using the `pair.py` script
* Calculates phasing using the high quality SNPs via `HAPCUT`

The intermediate files and results are placed in `output_dir/`. The key output is `output_haplotype_file` which reports the phasing information. The file format is described at https://github.com/vibansal/hapcut#format-of-input-and-output-files

Notes on the Analysis
---------------------

Each read typically consists of several segments ligated together, generally from nearby genomic locations on the same allele. To get mapping information for each segment, we first map the entire read, and then for unmapped portions of the read, iteratively repeat the process. This is done via `map.py`.

The phasing is performed by HAPCUT, which supports mate pair style reads. Because the Cergentis/PacBio data can have more than two segment per read, the data needs to be represented in a mate pair style manner. This is done via `pair.py`.

Analysis of BRCA1 using this workflow was presented at [AGBT 2016](http://www.pacb.com/wp-content/uploads/chromosomal-scale-targeted-haplotype-assembly-long-range-data-from-tla-smrt-sequencing.pdf).
