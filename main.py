from __future__ import print_function
import os
import argparse
import shutil
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import pandas as pd
import numpy as np
from torchvision import datasets, transforms
from torch.autograd import Variable
import models
import time


def appendDFToCSV_void(df, csvFilePath, sep=","):
    import os
    if not os.path.isfile(csvFilePath):
        df.to_csv(csvFilePath, mode='a', index=False, sep=sep)
    elif len(df.columns) != len(pd.read_csv(csvFilePath, nrows=1, sep=sep).columns):
        raise Exception("Columns do not match!! Dataframe has " + str(len(df.columns)) + " columns. CSV file has " + str(len(pd.read_csv(csvFilePath, nrows=1, sep=sep).columns)) + " columns.")
    elif not (df.columns == pd.read_csv(csvFilePath, nrows=1, sep=sep).columns).all():
        raise Exception("Columns and column order of dataframe and csv file do not match!!")
    else:
        df.to_csv(csvFilePath, mode='a', index=False, sep=sep, header=False)

# Training settings
parser = argparse.ArgumentParser(description='PyTorch Slimming CIFAR training')
parser.add_argument('--dataset', type=str, default='cifar100',
                    help='training dataset (default: cifar100)')
parser.add_argument('--sparsity-regularization', '-sr', dest='sr', action='store_true',
                    help='train with channel sparsity regularization')
parser.add_argument('--s', type=float, default=0.0001,
                    help='scale sparse rate (default: 0.0001)')
parser.add_argument('--refine', default='', type=str, metavar='PATH',
                    help='path to the pruned model to be fine tuned')
parser.add_argument('--batch-size', type=int, default=64, metavar='N',
                    help='input batch size for training (default: 64)')
parser.add_argument('--test-batch-size', type=int, default=64, metavar='N',
                    help='input batch size for testing (default: 256)')
parser.add_argument('--epochs', type=int, default=160, metavar='N',
                    help='number of epochs to train (default: 160)')
parser.add_argument('--start-epoch', default=0, type=int, metavar='N',
                    help='manual epoch number (useful on restarts)')
parser.add_argument('--lr', type=float, default=0.1, metavar='LR',
                    help='learning rate (default: 0.1)')
parser.add_argument('--momentum', type=float, default=0.9, metavar='M',
                    help='SGD momentum (default: 0.9)')
parser.add_argument('--weight-decay', '--wd', default=1e-4, type=float,
                    metavar='W', help='weight decay (default: 1e-4)')
parser.add_argument('--resume', default='', type=str, metavar='PATH',
                    help='path to latest checkpoint (default: none)')
parser.add_argument('--no-cuda', action='store_true', default=False,
                    help='disables CUDA training')
parser.add_argument('--name', default='VggNet19', type=str,
                    help='name of experiment')
parser.add_argument('--log-interval', type=int, default=100, metavar='N',
                    help='how many batches to wait before logging training status')
parser.add_argument('--save', default='./logs', type=str, metavar='PATH',
                    help='path to save prune model (default: current directory)')
parser.add_argument('--arch', default='vgg', type=str, 
                    help='architecture to use')
parser.add_argument('--beta', type=float, default=1.0, metavar='LR',
                    help='quadratic penalty parameter (default: 1.0)')
parser.add_argument('--depth', default=19, type=int,
                    help='depth of the neural network')

args = parser.parse_args()
args.cuda = not args.no_cuda and torch.cuda.is_available()

args.name += '_{}_{}_{}'.format(args.arch, args.depth, args.dataset)

if not os.path.exists(args.save):
    os.makedirs(args.save)

train_loss_vector = []
objective_loss_vector = []
test_loss_vector = []

kwargs = {'num_workers': 1, 'pin_memory': True} if args.cuda else {}
if args.dataset == 'cifar10':
    train_loader = torch.utils.data.DataLoader(
        datasets.CIFAR10('./data.cifar10', train=True, download=True,
                       transform=transforms.Compose([
                           transforms.Pad(4),
                           transforms.RandomCrop(32),
                           transforms.RandomHorizontalFlip(),
                           transforms.ToTensor(),
                           transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
                       ])),
        batch_size=args.batch_size, shuffle=True, **kwargs)
    test_loader = torch.utils.data.DataLoader(
        datasets.CIFAR10('./data.cifar10', train=False, transform=transforms.Compose([
                           transforms.ToTensor(),
                           transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
                       ])),
        batch_size=args.test_batch_size, shuffle=True, **kwargs)
elif args.dataset == 'SVHN':
    train_set = datasets.SVHN('./data.SVHN', split = "train", download = True, transform =transforms.Compose([transforms.ToTensor(),
            transforms.Normalize((0.4376821, 0.4437697, 0.47280442), (0.19803012, 0.20101562, 0.19703614))]))
    extra_set = datasets.SVHN('./data.SVHN', split = "extra", download = True, transform =transforms.Compose([transforms.ToTensor(),
            transforms.Normalize((0.4376821, 0.4437697, 0.47280442), (0.19803012, 0.20101562, 0.19703614))]))
    train_loader = torch.utils.data.DataLoader(torch.utils.data.ConcatDataset([train_set, extra_set]),
        batch_size =args.test_batch_size, shuffle = True, **kwargs)
    test_loader = torch.utils.data.DataLoader(
        datasets.SVHN('./data.SVHN', split = "test", download = True, transform =transforms.Compose([transforms.ToTensor(),
            transforms.Normalize((0.4376821, 0.4437697, 0.47280442), (0.19803012, 0.20101562, 0.19703614))])),
        batch_size =args.test_batch_size, shuffle = True, **kwargs)
elif args.dataset == 'cifar100':
    train_loader = torch.utils.data.DataLoader(
        datasets.CIFAR100('./data.cifar100', train=True, download=True,
                       transform=transforms.Compose([
                           transforms.Pad(4),
                           transforms.RandomCrop(32),
                           transforms.RandomHorizontalFlip(),
                           transforms.ToTensor(),
                           transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
                       ])),
        batch_size=args.batch_size, shuffle=True, **kwargs)
    test_loader = torch.utils.data.DataLoader(
        datasets.CIFAR100('./data.cifar100', train=False, transform=transforms.Compose([
                           transforms.ToTensor(),
                           transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
                       ])),
        batch_size=args.test_batch_size, shuffle=True, **kwargs)


if args.refine:
    checkpoint = torch.load(args.refine)
    model = models.__dict__[args.arch](dataset=args.dataset, depth=args.depth, cfg=checkpoint['cfg'])
    model.load_state_dict(checkpoint['state_dict'])
    args.name = args.name+'_refine'
else:
    model = models.__dict__[args.arch](dataset=args.dataset, depth=args.depth)

if args.cuda:
    model.cuda()

#set parameter for regularization method
alpha = 1/args.lr

optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=args.momentum, weight_decay=args.weight_decay)
lr_schedule = [int(args.epochs*0.5), int(args.epochs*0.75)]

if args.resume:
    if os.path.isfile(args.resume):
        print("=> loading checkpoint '{}'".format(args.resume))
        checkpoint = torch.load(args.resume)
        args.start_epoch = checkpoint['epoch']
        best_prec1 = checkpoint['best_prec1']
        model.load_state_dict(checkpoint['state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer'])
        print("=> loaded checkpoint '{}' (epoch {}) Prec1: {:f}"
              .format(args.resume, checkpoint['epoch'], best_prec1))
    else:
        print("=> no checkpoint found at '{}'".format(args.resume))

#proximal operator for l1
def proxl1(v, lambda_reg):
    l1_threshold = torch.nn.Softshrink(lambda_reg)
    return(l1_threshold(v))

#function to update scaling factors
def update_scaling_factor(s, alpha, beta, model):
    j=0
    for m in model.modules():
        if isinstance(m, nn.BatchNorm2d):
            n = model.scaling_factor_copy[j]
            m.weight.data.mul_(alpha)
            m.weight.data.add_(beta*n.data.cuda())
            m.weight.data.div_(alpha+beta)
            model.scaling_factor_copy[j].data = proxl1((alpha*n.data+beta*m.weight.data.cpu())/(alpha+beta), s/(alpha+beta))
            j+=1

def train(epoch):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        if args.cuda:
            data, target = data.cuda(), target.cuda()
        data, target = Variable(data), Variable(target)
        optimizer.zero_grad()
        output = model(data)
        loss = F.cross_entropy(output, target)
        pred = output.data.max(1, keepdim=True)[1]
        loss.backward()
        optimizer.step()
        if args.sr:
            update_scaling_factor(args.s, alpha, args.beta, model)
        
        if batch_idx % args.log_interval == 0:
            print('Train Epoch: {} [{}/{} ({:.1f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * len(data), len(train_loader.dataset),
                100. * batch_idx / len(train_loader), loss.item()))
    train_loss = 0
    for data, target in train_loader:
        if args.cuda:
            data, target = data.cuda(), target.cuda()
        data, target = Variable(data, volatile=True), Variable(target)
        output = model(data)
        train_loss += F.cross_entropy(output, target, size_average=False).data.item()
    train_loss /= len(train_loader.dataset)
    train_loss_vector.append(train_loss)
    for m in model.modules():
        if isinstance(m, nn.BatchNorm2d):
            train_loss = train_loss + args.s*torch.norm(m.weight.data, p=1).data.item()
    objective_loss_vector.append(train_loss)

def test():
    model.eval()
    test_loss = 0
    correct = 0
    for data, target in test_loader:
        if args.cuda:
            data, target = data.cuda(), target.cuda()
        data, target = Variable(data, volatile=True), Variable(target)
        output = model(data)
        test_loss += F.cross_entropy(output, target, size_average=False).data.item() # sum up batch loss
        pred = output.data.max(1, keepdim=True)[1] # get the index of the max log-probability
        correct += pred.eq(target.data.view_as(pred)).cpu().sum()

    test_loss /= len(test_loader.dataset)
    test_loss_vector.append(test_loss)
    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.1f}%)\n'.format(
        test_loss, correct, len(test_loader.dataset),
        100. * correct.float()*1.0 / len(test_loader.dataset)))
    return correct.float()*1.0 / float(len(test_loader.dataset))

def save_checkpoint(state, is_best, filepath):
    torch.save(state, os.path.join(filepath, args.name+'checkpoint.pth.tar'))
    if is_best:
        shutil.copyfile(os.path.join(filepath, args.name+'checkpoint.pth.tar'), os.path.join(filepath, args.name+'model_best.pth.tar'))

best_prec1 = 0.
epoch_time = []
for epoch in range(args.start_epoch, args.epochs):
    if epoch in lr_schedule:
        alpha *= 10
        for param_group in optimizer.param_groups:
            param_group['lr'] *= 0.1
    t0 = time.time()
    train(epoch)
    print('{} seconds'.format(time.time() - t0))
    epoch_time.append(time.time()-t0)
    prec1 = test()
    is_best = prec1 > best_prec1
    best_prec1 = max(prec1, best_prec1)
    save_checkpoint({
        'epoch': epoch + 1,
        'state_dict': model.state_dict(),
        'best_prec1': best_prec1,
        'optimizer': optimizer.state_dict(),
    }, is_best, filepath=args.save)

print("Best accuracy: "+str(best_prec1.item()))

if args.refine:
    data = [args.name, args.arch, args.depth, args.dataset, best_prec1.item()]
    info_df = pd.DataFrame(data)
    info_df = info_df.transpose()
    info_df.columns =  ['Name', 'Architecture', 'Depth', 'Dataset', 'Best Accuracy']

    appendDFToCSV_void(info_df, os.path.join(args.save, 'refine_record.csv'))
else:
    data = [args.name, args.arch, args.depth, args.dataset, args.s, args.beta, best_prec1.item()]
    info_df = pd.DataFrame(data)
    info_df = info_df.transpose()
    info_df.columns =  ['Name', 'Architecture', 'Depth', 'Dataset', 'Sparsity Parameter', 'Beta Parameter', 'Best Accuracy']

    appendDFToCSV_void(info_df, os.path.join(args.save, 'record2.csv'))

objective_result = pd.DataFrame([train_loss_vector, objective_loss_vector, test_loss_vector]).T
objective_result.columns = ['Training Loss', 'Objective', 'Test Loss']
objective_result.to_csv(os.path.join(args.save, args.name+'objective.csv'))
epoch_time = pd.DataFrame(epoch_time)
epoch_time.to_csv(os.path.join(args.save, args.name+'epoch_time.csv'))
