import h5py
import numpy as np
import random
import torch
from torch.utils.data import Dataset
import cv2 
import os 

from utils import utils


def to_tensor(img):
    return torch.as_tensor(img/255, dtype=torch.float32).permute(2,0,1).contiguous()

class TrainSet(Dataset):
    def __init__(self, args):
        self.args = args
        self.pch_size = args.patch_size
        f = h5py.File(args.train_path, 'r')
        self.keys = f.keys()
        self.clear = [f[x]['clear'][y] for x in self.keys for y in range(1500)]
        self.trans = [f[x]['trans'][y] for x in self.keys for y in range(1500)]
        self.hazy = [f[x]['hazy'][y] for x in self.keys for y in range(1500)]

    def __len__(self):
        return (len(self.clear))

    def __getitem__(self, idx):
        clear, hazy, trans = self.clear[idx], self.hazy[idx], np.expand_dims(self.trans[idx],-1)
        # A = torch.tensor(self.A[idx]).reshape(1,1,1).float()
        A = torch.tensor(utils.get_A(hazy)).reshape(1,1,1).float()
        if self.args.patch_size:
            clear, hazy, trans = self.random_crop(clear, hazy, trans)
        if np.random.choice([0,1]):
            clear, hazy, trans = np.flip(clear,1), np.flip(hazy,1), np.flip(trans,1)
        if np.random.choice([0,1]):
            clear, hazy, trans = np.flip(clear,0), np.flip(hazy,0), np.flip(trans,0)
        clear, hazy, trans = to_tensor(clear), to_tensor(hazy), to_tensor(trans)
        return (clear, hazy, trans, A)

    def random_crop(self, *im):
        H, W = im[0].shape[:2]
        if H < self.pch_size or W < self.pch_size:
            H = max(self.pch_size, H)
            W = max(self.pch_size, W)
            im = cv2.resize(im, (W, H))
        ind_H = random.randint(0, H-self.pch_size)
        ind_W = random.randint(0, W-self.pch_size)
        return [x[ind_H:ind_H+self.pch_size, ind_W:ind_W+self.pch_size] for x in im]

class TestSet(Dataset):
    def __init__(self, args):
        self.args = args
        f = h5py.File(args.test_path, 'r')
        self.keys = f.keys()
        self.clear = [f[x]['clear'][y] for x in self.keys for y in range(500)]
        self.hazy = [f[x]['hazy'][y] for x in self.keys for y in range(500)]
    
    
    def __len__(self):
        return (len(self.clear))

    def __getitem__(self, idx):
        clear, hazy = to_tensor(self.clear[idx]), to_tensor(self.hazy[idx])
        return (clear, hazy)

class BaseTrainSet(Dataset): 
    def __init__(self, args):
        self.args = args
        self.pch_size = args.patch_size
        with h5py.File(args.train_path, 'r') as f:
            self.clear = np.array(f['clear'])
            self.hazy = np.array(f['hazy'])

    def __len__(self):
        return (len(self.clear))

    def __getitem__(self, idx):
        clear, hazy = self.random_crop(self.clear[idx//10], self.hazy[idx])
        if np.random.choice([0,1]):
            clear, hazy= np.flip(clear,1), np.flip(hazy,1)
        if np.random.choice([0,1]):
            clear, hazy= np.flip(clear,0), np.flip(hazy,0)
        clear, hazy = to_tensor(clear), to_tensor(hazy)
        edge = utils.edge_compute(hazy)
        hazy = torch.cat([hazy,edge],dim=0)
        return (clear, hazy)

    def random_crop(self, *im):
        H, W = im[0].shape[:2]
        if H < self.pch_size or W < self.pch_size:
            H = max(self.pch_size, H)
            W = max(self.pch_size, W)
            im = cv2.resize(im, (W, H))
        ind_H = random.randint(0, H-self.pch_size)
        ind_W = random.randint(0, W-self.pch_size)
        return [x[ind_H:ind_H+self.pch_size, ind_W:ind_W+self.pch_size] for x in im]

class TrainOutFolder(Dataset): 
    def __init__(self,args):
        self.args = args
        self.pch_size = args.patch_size
        self.root = args.train_path
        self.img_names = os.listdir(os.path.join(self.root, 'hazy'))
        self.img_num = len(self.img_names)

    def __len__(self):
        return self.img_num

    def __getitem__(self, idx):
        cv2.setNumThreads(0)
        cv2.ocl.setUseOpenCL(False)

        img_name = self.img_names[idx]
        hazy = cv2.imread(os.path.join(self.root, 'hazy', img_name))[:,:,::-1]
        clear = cv2.imread(os.path.join(self.root, 'clear', img_name.split('_')[0]+'.jpg'))[:,:,::-1]
        trans = np.expand_dims(cv2.imread(os.path.join(self.root, 'trans', img_name), cv2.IMREAD_GRAYSCALE), -1)
        
        A = torch.tensor(utils.get_A(hazy)).reshape(1,1,1).float()

        if self.args.patch_size:
            clear, hazy, trans = self.random_crop(clear, hazy, trans)
        if np.random.choice([0,1]):
            clear, hazy, trans = np.flipud(clear), np.flipud(hazy), np.flipud(trans)
        # if np.random.choice([0,1]):
        #     clear, hazy, trans = np.flip(clear,0), np.flip(hazy,0), np.flip(trans,0)
        clear, hazy, trans = to_tensor(clear), to_tensor(hazy), to_tensor(trans)
        return (clear, hazy, trans, A)

    def random_crop(self, *im):
        H, W = im[0].shape[:2]
        if H < self.pch_size or W < self.pch_size:
            H = max(self.pch_size, H)
            W = max(self.pch_size, W)
            im = cv2.resize(im, (W, H))
        ind_H = random.randint(0, H-self.pch_size)
        ind_W = random.randint(0, W-self.pch_size)
        return [x[ind_H:ind_H+self.pch_size, ind_W:ind_W+self.pch_size] for x in im]

class TestOut(Dataset): 
    def __init__(self,args):
        self.args = args
        self.root = args.test_path
        self.img_names = os.listdir(os.path.join(self.root, 'hazy'))

    def __len__(self):
        return len(self.img_names)

    def __getitem__(self, idx):
        img_name = self.img_names[idx]
        clear = cv2.imread(os.path.join(self.root, 'clear', img_name))[:,:,::-1]
        hazy = cv2.imread(os.path.join(self.root, 'hazy', img_name))[:,:,::-1]
        clear, hazy= to_tensor(clear), to_tensor(hazy)
        return (clear, hazy)

class TrainRepoFolder(Dataset): 
    def __init__(self,args):
        self.args = args
        self.pch_size = args.patch_size
        self.root = args.train_path
        self.img_names = os.listdir(os.path.join(self.root, 'hazy'))
        self.img_num = len(self.img_names)

    def __len__(self):
        return self.img_num

    def __getitem__(self, idx):
        cv2.setNumThreads(0)
        cv2.ocl.setUseOpenCL(False)

        img_name = self.img_names[idx]
        hazy = cv2.imread(os.path.join(self.root, 'hazy', img_name))[:,:,::-1]
        clear = cv2.imread(os.path.join(self.root, 'clear', img_name.split('_')[0]+'.jpg'))[:,:,::-1]

        if self.args.patch_size:
            clear, hazy = self.random_crop(clear, hazy)
        if np.random.choice([0,1]):
            clear, hazy = np.flipud(clear), np.flipud(hazy)
        # if np.random.choice([0,1]):
        #     clear, hazy, trans = np.flip(clear,0), np.flip(hazy,0), np.flip(trans,0)
        clear, hazy = to_tensor(clear), to_tensor(hazy)
        return (clear, hazy)

    def random_crop(self, *im):
        H, W = im[0].shape[:2]
        if H < self.pch_size or W < self.pch_size:
            H = max(self.pch_size, H)
            W = max(self.pch_size, W)
            im = cv2.resize(im, (W, H))
        ind_H = random.randint(0, H-self.pch_size)
        ind_W = random.randint(0, W-self.pch_size)
        return [x[ind_H:ind_H+self.pch_size, ind_W:ind_W+self.pch_size] for x in im]


class TrainHaze4k(Dataset): 
    def __init__(self, args): 
        self.args = args
        self.path = args.train_path
        self.patch_size = args.patch_size
        f = h5py.File(args.train_path, 'r')
        self.keys = f.keys()
        self.clear = [f[x]['clear'][y] for x in self.keys for y in range(1500)]
        self.trans = [f[x]['trans'][y] for x in self.keys for y in range(1500)]
        self.hazy = [f[x]['hazy'][y] for x in self.keys for y in range(1500)]

    
    def __getitem__(self, idx):
        clear = self.clear[idx]
        trans = np.expand_dims(self.trans[idx], -1)
        hazy = self.hazy[idx]
        A = torch.tensor(utils.get_A(hazy)).reshape(1,1,1).float()
        clear, hazy, trans = self.random_crop(clear, hazy, trans)
        if np.random.choice([0,1]):
            clear, hazy, trans = np.flip(clear,1), np.flip(hazy,1), np.flip(trans,1)
        if np.random.choice([0,1]):
            clear, hazy, trans = np.flip(clear,0), np.flip(hazy,0), np.flip(trans,0)
        clear, hazy, trans = to_tensor(clear), to_tensor(hazy), to_tensor(trans)
        edge = utils.edge_compute(hazy)
        edge = torch.cat([hazy,edge],dim=0)
        return (clear, hazy, trans, A, edge)
    
    def __len__(self):
        return len(self.hazy)
         
    def random_crop(self, *img):
        H, W = img[0].shape[:2]
        if H < self.patch_size or W < self.patch_size:
            H = max(self.patch_size, H)
            W = max(self.patch_size, W)
            img = cv2.resize(img, (W, H))
        h_ind = random.randint(0, H-self.patch_size)
        w_ind = random.randint(0, W-self.patch_size)
        return [x[h_ind : h_ind + self.patch_size, w_ind : w_ind + self.patch_size] for x in img]

class TestHaze4k(Dataset): 
    def __init__(self, args): 
        self.args = args
        f = h5py.File(args.test_path, 'r')
        self.keys = f.keys()
        self.clear = [f[x]['clear'][y] for x in self.keys for y in range(500)]
        self.hazy = [f[x]['hazy'][y] for x in self.keys for y in range(500)]
    
    def __getitem__(self, idx):
        clear, hazy = to_tensor(np.array(self.clear[idx])), to_tensor(np.array(self.hazy[idx]))
        edge = utils.edge_compute(hazy)
        edge = torch.cat([hazy,edge],dim=0)
        return (clear, hazy)
    
    def __len__(self):
        return len(self.hazy)
