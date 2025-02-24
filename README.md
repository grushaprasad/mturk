# Scripts for automatically creating HITs on MTurk for psycholinguistic experiments

MTurk adds extra 20% charge on HITs with >9 participants. To avoid this it is ideal to automatically create HITs in batches of 9. 
However in doing this, it is important to ensure that the same participants do not participate in multiple batches. 
This can be done by assigning participants a qualification. 

* `create_hits.py` has code to do this, as well as apply some commonly used filters for experiments in psycholinguistics. 
* Before running `create_hits.py`, it is necessary to create custom qualification for each study. `create_qualification.py` does this. 
* `create_hits.sh` has an example run of `create_hits`. 

COMING SOON: 
More detailed instructions on how to setup the client and on the workflow for accepting or reejcting HITs. 
