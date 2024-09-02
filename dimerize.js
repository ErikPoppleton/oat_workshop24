//helper function cms
const computeCMS = (bases) => {
    let cms = new THREE.Vector3(0,0,0);
    bases.forEach( base =>{
        cms.add(base.getPos());
    });
    cms.divideScalar(bases.size);
    return cms;
}

// we assume that the first system is the one we want to copy around
systems[0].select();

// we store the number of bases comprising the system 
const n_elements = selectedBases.size;

// compute the center of mass of the origami
let cms_old = computeCMS(selectedBases);

// prepare to copy around
cutWrapper(); 
//paste in a new structure, true keeps the position 
pasteWrapper(true);
//make sure everything is its own cluster
selectionToCluster();


// we handle just the homodimer case
//paste in a new structure, true keeps the position 
pasteWrapper(true);
//make sure everything is its own cluster
selectionToCluster();
let cms_new = new THREE.Vector3().copy(cms_old);
// adjust the position of the new system as needed
cms_new.z -= 105;
//move the origami
translateElements(selectedBases, cms_new);




// find everything that is more than 5 ox units away from its n3
let p3_extended = new Set();
elements.forEach((b,id) => {
      if(b.n3){
          let p1 = b.getPos();
          let p2 = b.n3.getPos();
          let dist = p1.distanceTo(p2);
          if(dist > 5){ 
              p3_extended.add(b)
          }
      }
    });

// color the victims
[... p3_extended].map(b=>b.strand).forEach(s=>{
    colorElements(new THREE.Color(1,0,1), s.getMonomers())
});

// now we need to find corresonding sequences between the strands 
// we want pairs of same strands, hence we have homo dimers 
let seq_to_strands = {};
[... p3_extended].map(b=>{
    let strand = b.strand;
    let seq = strand.getSequence();
    //chech if sequnce is in seq_to_strands 
    if(seq in seq_to_strands)
        seq_to_strands[seq].push([b,strand]);
    else
        seq_to_strands[seq] = [[b,strand]];

})
//iterate over the seqs 
Object.keys(seq_to_strands).forEach((seq) => {
    // Access the value associated with the current key
    const [[b1, strand1], [b2, strand2]] = seq_to_strands[seq];

    //before we nick we need a handle of the other side 
    let strand1n3 = b1.n3;
    let strand2n3 = b2.n3;
    

    // //we need to nick @b1 and @b2 and interconnect the resulting strands 
    edit.nick(b1)
    edit.nick(b2)
    
    edit.ligate(b1,strand2n3);
    edit.ligate(b2,strand1n3);
    
   
});