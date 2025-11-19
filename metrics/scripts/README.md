# Albumentations data augmentation

1. Create conda env (albumentation requires python >=3.9)
```bash
conda create -n albumentation "python>=3.9"
```
2. Activate the env
```bash
conda activate albumentation
```

3. Add albumentation 
```bash
pip install -U git+https://github.com/albumentations-team/AlbumentationsX
```

4. Dependencies
```bash
pip install pillow torchvision
```

5. Proceed with the python script ```data_augmentation.py```

eg. python3 data_augmentation.py -a rain_torrential -d /home/mae/Documents/GIT/Research/SafeGNM/src/visualnav-transformer/deployment/topomaps/images -n bunker_mist_corridor


# Image analysis


**This assumes you are running the code within the docker for the model (Nomad, Vint, Crossformer)**




# Troubleshooting


## ValueError: Multi-dimensional indexing 

Error message:
```
ValueError: Multi-dimensional indexing (e.g. obj[:, None]) is no longer supported. Convert to a numpy array before indexing instead.
```
```
pip install seaborn matplotlib pandas --target /workspace/.packages_{package_name}/ --upgrade
```


# Bag data processing 

run python3 process_bags.py --proc bag2df to process the bags in metrics/bags based on robots, augmentations envrionments and experiments related parameters stipulated in config/experiments.yaml

run python3 process_bags.py --proc unify_dfs to have a single dataframe that regroups the previous generated datframes

# Closest node

**CHANGE DF WITH PREVIOUS UNIFIED DF IN THE FILE**

In order to fairly have the node prediction error, we are looking at what would have been the closes node given the trajectory position based on the reference trajectory ({robot}_{env}_reference.bag).
To do we first 1) run python process_closest_node.py to retrieve poses and ground truth node (topomap node) of all the bags tagged reference in metrics/bags
The dataframees will be stored in metrics/dataframes/closest_node_analysis folder

2) 
**CHANGE DF WITH PREVIOUS UNIFIED DF IN THE FILE**
process_node_error.py 