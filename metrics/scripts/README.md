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