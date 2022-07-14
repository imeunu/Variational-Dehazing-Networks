import h5py
import numpy as np
import random
import torch
from torch.utils.data import Dataset
import cv2 

from utils import utils


def to_tensor(img):
    return torch.as_tensor(img/255).permute(2,0,1).contiguous()

class TrainSet(Dataset):
    def __init__(self, args):
        self.args = args
        self.pch_size = args.patch_size
        with h5py.File(args.train_path, 'r') as f:
            self.clear = np.array(f['clear'])
            self.hazy = np.array(f['hazy'])
            self.trans = np.array(f['trans'])

    def __len__(self):
        return (10 * len(self.clear))

    def __getitem__(self, idx):
        clear, hazy, trans = self.clear[idx//10], self.hazy[idx], self.trans[idx]
        clear, hazy, trans = self.random_crop(clear, hazy, trans)
        A = utils.get_A(hazy)
        if self.args.augmentation and np.random.choice([0,1]):
            clear, hazy, trans = np.flip(clear,1), np.flip(hazy,1), np.flip(trans,1)
        clear, hazy, trans = to_tensor(clear), to_tensor(hazy), to_tensor(trans)
        return (clear, hazy, trans, A)
    
    def random_crop(self, *img):
        H, W = img[0].shape[:2]
        if H < self.pch_size or W < self.pch_size:
            H = max(self.pch_size, H)
            W = max(self.pch_size, W)
            img = cv2.resize(img, (W, H))
        h_ind = random.randint(0, H-self.pch_size)
        w_ind = random.randint(0, W-self.pch_size)
        return [x[h_ind : h_ind + self.pch_size, w_ind : w_ind + self.pch_size] for x in img]

class TestSet(Dataset):
    def __init__(self, args):
        self.args = args
        with h5py.File(args.test_path, 'r') as f:
            self.clear = np.array(f['clear'])
            self.hazy = np.array(f['hazy'])
    
    def __len__(self):
        return (10 * len(self.clear))

    def __getitem__(self, idx):
        return (to_tensor(self.clear[idx//10]), to_tensor(self.hazy[idx]))

class Train_DnCNN(Dataset): 
    def __init__(self, args):
        self.args = args
        with h5py.File(args.train_path, 'r') as f:
            self.clear = np.array(f['clear'])
            self.hazy = np.array(f['hazy'])

    def __len__(self):
        return (10 * len(self.clear))

    def __getitem__(self, idx):
        clear, hazy = self.clear[idx//10], self.hazy[idx]
        if self.args.augmentation and np.random.choice([0,1]):
            clear, hazy= np.flip(clear,1), np.flip(hazy,1)
        clear, hazy= to_tensor(clear), to_tensor(hazy)
        return (clear, hazy) 

class Train_Trans_DnCNN(Dataset): 
    def __init__(self, args):
        self.args = args
        with h5py.File(args.train_path, 'r') as f:
            self.clear = np.array(f['clear'])
            self.trans = np.array(f['trans'])
        self.pch_size = args.patch_size

    def __len__(self):
        return (10 * len(self.clear))

    def __getitem__(self, idx):
        clear, trans = self.crop_patch(self.clear[idx//10], self.trans[idx])
        if self.args.augmentation and np.random.choice([0,1]):
            clear, trans= np.flip(clear,1), np.flip(trans,1)
        clear, trans= to_tensor(clear), to_tensor(trans)
        return (clear, trans)     

    def crop_patch(self, *im):
        H, W = im[0].shape[:2]
        if H < self.pch_size or W < self.pch_size:
            H = max(self.pch_size, H)
            W = max(self.pch_size, W)
            im = cv2.resize(im, (W, H))
        ind_H = random.randint(0, H-self.pch_size)
        ind_W = random.randint(0, W-self.pch_size)
        return [x[ind_H:ind_H+self.pch_size, ind_W:ind_W+self.pch_size] for x in im]