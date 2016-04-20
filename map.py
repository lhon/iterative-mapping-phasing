import os, sys

# https://github.com/lh3/readfq
def readfq(fp): # this is a generator function
    last = None # this is a buffer keeping the last unprocessed line
    while True: # mimic closure; is it a bad idea?
        if not last: # the first record or a record following a fastq
            for l in fp: # search for the start of the next record
                if l[0] in '>@': # fasta/q header line
                    last = l[:-1] # save this line
                    break
        if not last: break
        name, seqs, last = last[1:].partition(" ")[0], [], None
        for l in fp: # read the sequence
            if l[0] in '@+>':
                last = l[:-1]
                break
            seqs.append(l[:-1])
        if not last or last[0] != '+': # this is a fasta record
            yield name, ''.join(seqs), None # yield a fasta record
            if not last: break
        else: # this is a fastq record
            seq, leng, seqs = ''.join(seqs), 0, []
            for l in fp: # read the quality
                seqs.append(l[:-1])
                leng += len(l) - 1
                if leng >= len(seq): # have read enough quality
                    last = None
                    yield name, seq, ''.join(seqs); # yield a fastq record
                    break
            if last: # reach EOF before reading enough quality
                yield name, seq, None # yield a fasta record instead
                break

def as_fasta(id, seq):
    lines = ['>%s' % id,]
              
    for i in range(0, len(seq), 50):
        lines.append(seq[i:i+50])
              
    return '\n'.join(lines)

class SAMConsumer:
    ''' Writes out SAM output as it processes the results '''

    def __init__(self, out_filename):
        self.first = True
        self.outf_filename = out_filename
    
    def consume(self, filename):
        write_mode = 'w' if self.first else 'a'
        with open(self.outf_filename, write_mode) as fout:
            for line in open(filename):
                if line.startswith('@'):
                    if self.first:
                        # keep header the first time through
                        print >>fout, line,
                    continue
                    
                #print >>fout, line,
                cols = line.strip().split()
                idcols = cols[0].split('/')
                id = '/'.join(idcols[:-1])
                seq_range = idcols[-1].split('_')
                range_start = int(seq_range[0])
                range_end = int(seq_range[1])
                qstart_str = cols[13]
                qend_str = cols[14]
                #print qstart_str, qend_str
                assert(qstart_str.startswith('XS:i:'))
                assert(qend_str.startswith('XE:i:'))
                qstart = int(qstart_str[5:])
                qend = int(qend_str[5:])
                
                print >>fout, '\t'.join([id]+cols[1:])
                
                yield id, qstart, qend, range_start, range_end
        
        self.first = False

def map_segments(input_fasta, ref_fa, out_filename, subset_prefix):
    seqs = dict([id, seq] for id, seq, _ in readfq(open(input_fasta)) if subset_prefix is None or id.startswith(subset_prefix))
    ranges = [(id, 0, len(seq)) for id, seq in seqs.iteritems()]
    query_fa = 'temp.fasta'
    
    with open(query_fa, 'w') as f:
        for id, start, end in ranges:
            print >>f, as_fasta('%s/%d_%d' % (id, start, end), seqs[id][start:end])
    
    sam_consumer = SAMConsumer(out_filename)
    
    ref_sa = ref_fa+'.sa'
    ref_ctab = ref_fa+'.ctab'
    
    while True:
        cmd = 'blasr {query_fa} {ref_fa} -sa {ref_sa} -ctab {ref_ctab} -bestn 1 -nproc 24 -sam -noSplitSubreads -indelRate 0.1 -sdpIns 100 -sdpDel 100 -out out.sam'.format(
            query_fa=query_fa, ref_fa=ref_fa, ref_sa=ref_sa, ref_ctab=ref_ctab)
        os.system(cmd)

        count = 0
        min_segment = 20
        wiggle = 10
        with open(query_fa, 'w') as f:
            for id, qstart, qend, range_start, range_end in sam_consumer.consume('out.sam'):
                if qstart-range_start > min_segment:
                    start = range_start
                    end = min(qstart+wiggle, range_end)
                    print >>f, as_fasta('%s/%d_%d' % (id, start, end), 'N'*start + seqs[id][start:end])
                    count += 1
                if range_end-qend > min_segment:
                    start = max(qend-wiggle, range_start)
                    end = range_end
                    print >>f, as_fasta('%s/%d_%d' % (id, start, end), 'N'*start + seqs[id][start:end])
                    count += 1
                print id, qstart, qend, range_start, range_end
        
        if count == 0: break

if __name__ == '__main__':
    filename = sys.argv[1]
    reference_path = sys.argv[2]
    out_filename = sys.argv[3]
    subset = None
    if len(sys.argv) > 4:
        subset = sys.argv[4]
    map_segments(filename, reference_path, out_filename, subset)
