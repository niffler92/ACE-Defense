from argparse import Namespace
import numpy as np
import torch.nn as nn

import torchvision.models as torch_models
from common.torch_utils import get_model

__all__ = ['ace', 'ace_resnet101', 'ace_densenet121', 'ace_vgg19', 'ace_vgg19_bn']
__all__ += ['ace_resnet101_random', 'ace_densenet121_random', 'ace_vgg19_random']
__all__ += ['ace_cifar', 'ace_cifar_random']


class ACE(nn.Module):
    """Induce and evade adversarial attacks by the checkerboard artifact"""
    def __init__(self, classifiers, autoencoders, stacks, lambdas, shifts,
                 args, **kwargs):
        super(ACE, self).__init__()
        self.args = Namespace(**vars(args))
        args = Namespace(**vars(args))
        args.multigpu = False

        # Load all possible combinations
        self.classifiers = nn.ModuleList([])
        self.autoencoders = nn.ModuleList([])
        self.shifts = []

        # Classifiers are always frozen
        for c in classifiers:
            args.model = c
            model, _ = get_model(args)
            if not args.fine_tune:
                for param in model.parameters():
                    param.requires_grad = False
            self.classifiers.append(model)

        self.stacks = stacks

        # Autoencoders can be trained
        for a in autoencoders:
            args.model = a
            model, _ = get_model(args)
            self.autoencoders.append(model)
            self.shifts.append(shifts[a])

        self.lambdas = lambdas

    def forward(self, x, ae_only=False):
        classifier = np.random.choice(self.classifiers)
        stacks = np.random.choice(self.stacks)

        # TODO: zip??
        autoencoders = np.random.choice(self.autoencoders, stacks)
        lambdas = np.random.choice(self.lambdas, stacks)

        shifts = []
        for _ in range(stacks):
            idx = np.random.choice(len(self.shifts))

        for idx, autoencoder in enumerate(autoencoders):
            shift = np.random.choice(self.shifts[autoencoder]
            l, r, u, d = self.pad_shape(*shifts[idx])
            x_pad = nn.ZeroPad2d(padding=(l,r,u,d))(x)
            w, h = x_pad.shape[-1], x_pad.shape[-2]

            x_shift = x_pad[:,:,d:h-u,r:w-l].contiguous()
            x = lambdas[idx]*autoencoder(x_shift) + (1 - lambdas[idx])*x_shift

        out = x if ae_only else classifier(x)

        return out

    def pad_shape(self, x, y):
        left = x*(x > 0)
        right = -x*(x < 0)
        up = y*(y > 0)
        down = -y*(y < 0)

        return left, right, up, down


# Default configurations
classifiers = ['densenet121', 'resnet50', 'vgg19', 'vgg19_bn', 'alexnet']
autoencoders = ['unet', 'unet_v1', 'unet_v2']
stacks = [5]
lambdas = [0, 0.5, 1]
shifts = {'unet': [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1, -1), (1,-1), (-1,1)],
          'unet_v1': [(1,0), (-1,0)],
          'unet_v2': [(0,1), (0,-1)],
          }


def ace(args, **kwargs):
    assert args.dataset == "ImageNet"
    global classifiers, autoencoders, stacks, lambdas, shifts
    return ACE(classifiers, autoencoders, stacks, lambdas, shifts, args, **kwargs)

def ace_resnet50(args, **kwargs):
    assert args.dataset == "ImageNet"
    global autoencoders, stacks, shifts
    classifiers = ['resnet50']
    lambdas = [1]
    shifts = {'unet': [(0,0)], 'unet_v1': [(0,0)], 'unet_v2': [(0,0)]}
    return ACE(classifiers, autoencoders, stacks, lambdas, shifts, args, **kwargs)

def ace_resnet101(args, **kwargs):
    assert args.dataset == "ImageNet"
    global autoencoders, stacks, shifts
    classifiers = ['resnet101']
    lambdas = [1]
    shifts = {'unet': [(0,0)], 'unet_v1': [(0,0)], 'unet_v2': [(0,0)]}
    return ACE(classifiers, autoencoders, stacks, lambdas, shifts, args, **kwargs)

def ace_densenet121(args, **kwargs):
    assert args.dataset == "ImageNet"
    global autoencoders, stacks, shifts
    classifiers = ['densenet121']
    lambdas = [1]
    shifts = {'unet': [(0,0)], 'unet_v1': [(0,0)], 'unet_v2': [(0,0)]}
    return ACE(classifiers, autoencoders, stacks, lambdas, shifts, args, **kwargs)

def ace_vgg19(args, **kwargs):
    assert args.dataset == "ImageNet"
    global autoencoders, stacks, shifts
    classifiers = ['vgg19']
    lambdas = [1]
    shifts = {'unet': [(0,0)], 'unet_v1': [(0,0)], 'unet_v2': [(0,0)]}
    return ACE(classifiers, autoencoders, stacks, lambdas, shifts, args, **kwargs)

def ace_vgg19_bn(args, **kwargs):
    assert args.dataset == "ImageNet"
    global autoencoders, stacks, shifts
    classifiers = ['vgg19_bn']
    lambdas = [1]
    shifts = {'unet': [(0,0)], 'unet_v1': [(0,0)], 'unet_v2': [(0,0)]}
    return ACE(classifiers, autoencoders, stacks, lambdas, shifts, args, **kwargs)


def ace_resnet101_random(args, **kwargs):
    assert args.dataset == "ImageNet"
    global autoencoders, stacks, shifts
    classifiers = ['resnet101']
    lambdas = [1]
    return ACE(classifiers, autoencoders, stacks, lambdas, shifts, args, **kwargs)

def ace_densenet121_random(args, **kwargs):
    assert args.dataset == "ImageNet"
    global autoencoders, stacks, shifts
    classifiers = ['densenet121']
    lambdas = [1]
    return ACE(classifiers, autoencoders, stacks, lambdas, shifts, args, **kwargs)

def ace_vgg19_random(args, **kwargs):
    assert args.dataset == "ImageNet"
    global autoencoders, stacks, shifts
    classifiers = ['vgg19']
    lambdas = [1]
    return ACE(classifiers, autoencoders, stacks, lambdas, shifts, args, **kwargs)


def ace_cifar(args, **kwargs):
    assert "CIFAR" in args.dataset
    global autoencoders, stacks
    classifiers = ['ResNet18']
    lambdas = [1.0]
    shifts = {'unet': [(0,0)], 'unet_v1': [(0,0)], 'unet_v2': [(0,0)]}
    return ACE(classifiers, autoencoders, stacks, lambdas, shifts, args, **kwargs)

def ace_cifar_random(args, **kwargs):
    assert "CIFAR" in args.dataset
    global autoencoders, stacks, shifts
    classifiers = ['ResNet18']
    lambdas = [1.0]
    return ACE(classifiers, autoencoders, stacks, lambdas, shifts, args, **kwargs)
