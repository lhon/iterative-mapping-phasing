#!/bin/bash

# http://stackoverflow.com/questions/5750450/bash-print-each-command-before-executing
set -x

#############
# Input parameters

INPUT_ROI="$(cd "$(dirname "$1")"; pwd)/$(basename "$1")" # get full path
REFERENCE_FASTA="$(cd "$(dirname "$2")"; pwd)/$(basename "$2")"
GENOMIC_COORDINATES=$3 # e.g. chr17:41,194,312-41,279,500
SUBDIR=$4
IDSUBSET=$5 # optional

# more params
MIN_QUAL=30

# get path to scripts
# http://stackoverflow.com/questions/59895/can-a-bash-script-tell-what-directory-its-stored-in
SCRIPT_PATH=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

############
# Prep index files for blasr; assumes directory that reference fasta is in is writeable
if [ ! -e $REFERENCE_FASTA.sa ]; then
    echo Creating $REFERENCE_FASTA.sa
    sawriter $REFERENCE_FASTA -blt 8 -welter 
fi

if [ ! -e $REFERENCE_FASTA.ctab ]; then
    echo Creating $REFERENCE_FASTA.ctab
    printTupleCountTable $REFERENCE_FASTA.ctab $REFERENCE_FASTA
fi

##########
# Workflow

mkdir -p $SUBDIR
cd $SUBDIR

echo iteratively map reads
python $SCRIPT_PATH/map.py $INPUT_ROI $REFERENCE_FASTA all.sam $IDSUBSET
samtools view -bS all.sam | samtools sort - all.sorted
samtools index all.sorted.bam

echo identify high quality SNPs
samtools mpileup -I -vf ~/fasta/hg19_M_sorted.fasta -r $GENOMIC_COORDINATES all.sorted.bam | bcftools call -c -v - | bcftools filter -i"%QUAL>$MIN_QUAL" > var-subset.vcf

echo represent mapped segments on the same molecule \(ZMW\) as paired end reads
python $SCRIPT_PATH/pair.py all.sam all-paired.sam $GENOMIC_COORDINATES
samtools view -bS all-paired.sam | samtools sort - all-paired.sorted
samtools index all-paired.sorted.bam

echo run HAPCUT
$SCRIPT_PATH/extractHAIRS --VCF var-subset.vcf --bam all-paired.sorted.bam --maxIS 10000000 > fragment_matrix_file
$SCRIPT_PATH/HAPCUT --fragments fragment_matrix_file --VCF var-subset.vcf --output output_haplotype_file --maxiter 100 > hapcut.log




