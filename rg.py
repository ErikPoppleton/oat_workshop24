import time
start_time = time.time()
import argparse
import numpy as np
from os import path
from json import dump
from collections import namedtuple
from oxDNA_analysis_tools.UTILS.logger import log, logger_settings
from oxDNA_analysis_tools.UTILS.RyeReader import describe, get_confs, inbox
from oxDNA_analysis_tools.UTILS.data_structures import TrajInfo, TopInfo
from oxDNA_analysis_tools.UTILS.oat_multiprocesser import oat_multiprocesser, get_chunk_size

ComputeContext = namedtuple("ComputeContext", ["top_info", "traj_info"])

# The parallelized function which actually does hard things
def compute(ctx:ComputeContext, chunk_size:int, chunk_id:int):
    confs = get_confs(ctx.top_info, ctx.traj_info, chunk_id*chunk_size, chunk_size)
    poses = np.array([inbox(c).positions for c in confs])
    com = np.mean(poses, axis=1, keepdims=True)
    dists = np.linalg.norm(poses-com, axis=2)
    sq_dists = np.power(dists, 2)
    msd = np.sum(sq_dists, axis=1)/ctx.top_info.nbases
    rg = np.sqrt(msd)
    return(rg)

def rg(top_info:TopInfo, traj_info:TrajInfo, ncpus:int=1) -> np.ndarray:
    """
    Compute radius of gyration for the provided trajectory

    Parameters:
        top_info (TopInfo): Information about the topology
        traj_info (TrajInfo): Information about the trajectory
        ncpus (int) : (optional) How many cpus to parallelize the operation. default=1

    Returns:
        np.ndarray: Radius of gyration at each configuration
    """
    # The ctx is the arguments for the parallelized function
    ctx = ComputeContext(top_info, traj_info)

    # Figure out how much stuff each process is working on
    chunk_size = get_chunk_size()

    # Take the output from each chunk and 
    output = np.zeros(traj_info.nconfs)
    def callback(i, r): # i is the number of the chunk, r is the data that comes back from processing the chunk
        nonlocal output
        output[i*chunk_size:i*chunk_size+len(r)] = r 

    # Call <compute> with args <ctx> <ncpus> times to process <nconfs> things then package the results with <callback>
    oat_multiprocesser(traj_info.nconfs, ncpus, compute, callback, ctx)

    return output

# This is what gets picked up by the cli documentation builder
def cli_parser(prog="program_name"):
    parser = argparse.ArgumentParser(prog = prog, description="Calculate radius of gyration over a trajectory")
    parser.add_argument('trajectory', type=str, help='The trajectory file you wish to analyze')
    parser.add_argument('-p', '--parallel', metavar='num_cpus', type=int, dest='parallel', help="(optional) How many cores to use")
    parser.add_argument('-o', '--output', metavar='output_file', help='The filename to save the output to')
    parser.add_argument('-q', '--quiet', metavar='quiet', dest='quiet', action='store_const', const=True, default=False, help="Don't print 'INFO' messages to stderr")
    return parser

# All main does is handle i/o
def main():
    # Get arguments from the CLI
    parser = cli_parser(path.basename(__file__))
    args = parser.parse_args()

    #run system checks
    logger_settings.set_quiet(args.quiet)
    from oxDNA_analysis_tools.config import check
    check(["python", "numpy"])

    # Parse CLI input
    traj = args.trajectory
    top_info, traj_info = describe(None, traj)

    # -p sets the number of cores to use.  Default is 1.
    ncpus = args.parallel if args.parallel else 1

    # -o names the output file
    if args.output:
        outfile = args.output
    else:
        outfile = "rg.json"
        log(f"No outfile name provided, defaulting to \"{outfile}\"")

    # TODO: Add indexing and a matplotlib output

    # Actually process data
    out = rg(top_info, traj_info, ncpus=ncpus)

    # Drop output as an oxView OP file
    with open(outfile, 'w+') as f:
        out_obj = {"rg" : [o for o in out]}
        dump(out_obj, f)
        log(f"Wrote output to file {outfile}")

    print("--- %s seconds ---" % (time.time() - start_time))

if __name__ == '__main__':
    main()