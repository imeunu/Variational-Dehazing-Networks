import torch 
import torch.nn as nn 
import cv2 

class Coarse_Scale_Net(nn.Module): 
    def __init__(self, in_channels = 1): 
        super(Coarse_Scale_Net, self).__init__()
        self.relu = nn.ReLU()
        self.conv1 = nn.Conv2d(in_channels= in_channels, out_channels=5, kernel_size=11)
        self.conv2 = nn.Conv2d(in_channels=5, out_channels=5, kernel_size=11)
        self.conv3 = nn.Conv2d(in_channels=5, out_channels=10, kernel_size=9)
        self.conv4 = nn.Conv2d(in_channels=10, out_channels=1, kernel_size=7)
    def forward(self, x): 
        out = self.relu(self.conv1(x))
        out = self.relu(self.conv2(out))
        out = self.relu(self.conv3(out))
        out = self.conv4(out)
        return out 

class Fine_Scale_Net(nn.Module): 
    def __init__(self): 
        super(Fine_Scale_Net, self).__init__()
        self.relu = nn.ReLU()
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=4, kernel_size=7)
        self.conv2 = nn.Conv2d(in_channels=5, out_channels=5, kernel_size=5)
        self.conv3 = nn.Conv2d(in_channels=5, out_channels=10, kernel_size=3)
        self.conv4 = nn.Conv2d(in_channels=10, out_channels=1, kernel_size=3)

    def forward(self, x, y): 
        out = self.relu(self.conv1(x)) 
        out = self.relu(self.conv2(torch.cat([out, y], dim=1)))
        out = self.relu(self.conv3(out))
        out = self.conv4(out)
        return out

class MSCNN(nn.Module): 
    def __init__(self): 
        super(MSCNN, self).__init__()
        self.coarse_net = Coarse_Scale_Net()
        self.fine_net = Fine_Scale_Net()
        self.relu = nn.ReLU()
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=4, kernel_size=3)
        self.conv2 = nn.Conv2d(in_channels=6, out_channels=5, kernel_size=3)
        self.conv3 = nn.Conv2d(in_channels=5, out_channels=10, kernel_size=3)
        self.conv4 = nn.Conv2d(in_channels=10, out_channels=1, kernel_size=3)
    
    def forward(self, x, canny): 
        out1 = self.coarse_net(x)
        out2 = self.fine_net(x, out1)
        out = self.relu(self.conv1(x))
        out = self.relu(self.conv2(torch.cat([out, out2, canny], dim=1)))
        out = self.relu(self.conv3(out))
        out = self.conv4(out) 
        return out 

if __name__ == '__main__': 
    image = torch.rand((3,1,620,460))
    canny = torch.rand((1,1,620,460))
    net = MSCNN()
    print(net(image,canny).shape)
    