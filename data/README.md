# MedHop data

This repository does not distribute MedHop data, document supports, or
GraphRAG artifacts derived from those documents.

To create local GraphRAG input files, install the project dependencies and
run the following commands from the repository root:

```bash
python scripts/download_medhop.py
python scripts/prepare_medhop.py
```

The download script stores the selected BigBio MedHop split in
`data/raw/medhop/`. The preparation script writes its unique document supports
to `graphrag_npu_0722/input/`. Both locations are ignored by Git.

## License and attribution

MedHop is licensed under the Creative Commons Attribution-ShareAlike 3.0
Unported license (CC BY-SA 3.0). If you redistribute MedHop data or derived
content, provide attribution, link to the license, identify modifications, and
apply the applicable ShareAlike terms.

Citation:

```text
Johannes Welbl, Pontus Stenetorp, and Sebastian Riedel.
"Constructing Datasets for Multi-hop Reading Comprehension Across Documents."
Transactions of the Association for Computational Linguistics, 2018.
https://aclanthology.org/Q18-1021
```

Source dataset card: `medhop/README.md`

