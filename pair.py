import sys
import subprocess
import cStringIO
import copy

def setup_pairing(f, group):
    # encode sam output as paired end
    id = group[0][0].replace("/ccs", "")
    for i in range(len(group)-1):
        for j in range(i+1, len(group)):
            c1 = copy.copy(group[i])
            c2 = copy.copy(group[j])
            c1[1] = str(int(c1[1]) | 0x1 | 0x2 | 0x40)
            c2[1] = str(int(c2[1]) | 0x1 | 0x2 | 0x80)
            c1[0] = id
            c2[0] = id
            c1[6] = '='
            c2[6] = '='
            c1[7] = c2[3]
            c2[7] = c1[3]

            print >>f, '\t'.join(c1)
            print >>f, '\t'.join(c2)

def run(input_filename, output_filename, genomic_coordinates):
    target_chrom, coord_range = genomic_coordinates.split(':')
    coords = coord_range.split('-')
    target_start = int(coords[0].replace(',', ''))
    target_end = int(coords[1].replace(',', ''))
    print target_chrom, target_start, target_end

    f = open(output_filename, 'w')

    # copy header
    for line in open(input_filename):
        if line.startswith('@'):
            print >>f, line,
        else:
            break

    # sort by read id
    p = subprocess.Popen(["sort", input_filename], stdout = subprocess.PIPE)
    fh = cStringIO.StringIO(p.communicate()[0])
    last_id = None
    group = []
    for line in fh:
        if line.startswith('@'): continue
        cols = line.strip().split()

        # use ontarget alignments only
        chrom = cols[2]
        pos = int(cols[3])
        if chrom != target_chrom or pos < target_start or pos > target_end: continue

        id = cols[0]
        if id != last_id:
            if len(group) > 1: 
                setup_pairing(f, group)
            elif len(group) == 1:
                print >>f, '\t'.join(group[0])
            group = [cols]
            last_id = id
        else:
            group.append(cols)
    f.close()        

if __name__ == '__main__':
    run(*sys.argv[1:])
