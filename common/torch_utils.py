import os
from collections import OrderedDict
from argparse import Namespace

import torch
import numpy as np

from nsml import DATASET_PATH, NSML_NFS_OUTPUT


def get_model(args):
    import submodules.models as models
    import submodules.autoencoders as autoencoders

    model = getattr(models, args.model)(args)
    if args.pretrained:
        if NSML_NFS_OUTPUT:
            path = os.path.join(NSML_NFS_OUTPUT, args.ckpt_dir)
        elif DATASET_PATH:
            path = os.path.join(DATASET_PATH, 'train', args.ckpt_dir)
        else:
            path = os.path.join(PROJECT_ROOT, args.ckpt_dir)
        
        ckpt = torch.load(path, map_location=lambda storage, loc: storage)
        model_state = ckpt['model']

        model_state_cpu = OrderedDict()
        for k in model_state.keys():
            if k.startswith("module."):
                k_new = k[7:]
                model_state_cpu[k_new] = model_state[k]
            else:
                model_state_cpu[k] = model_state[k]
        model.load_state_dict(model_state_cpu)
    
    else:
        init_params(model, args=args)

    model.cuda() if args.cuda else model.cpu()
    if args.multigpu:
        model = nn.DataParallel(model)
    if args.half:
        model.half()

    if args.model in dir(autoencoders):
        def compute_loss(model, images, labels):
            outputs = model(images)
            criterion = nn.MSELoss()
            if args.cuda:
                criterion = criterion.cuda()
            if args.half:
                criterion = criterion.half()   
            loss = criterion(outputs, images)
            return None, loss
        return model, compute_loss

    else:
        def compute_loss(model, images, labels):
            outputs = model(images)
            criterion = nn.CrossEntropyLoss()
            if args.cuda:
                criterion = criterion.cuda()
            if args.half:
                criterion = criterion.half()
            loss = criterion(outputs, labels)
            return outputs, loss
        return model, compute_loss


def get_optimizer(optimizer, params, args):
    optimizer = optimizer.lower()
    assert optimizer in ['sgd', 'adam', 'rmsprop', 'sgd_nn', 'adadelta']
    params = filter(lambda p: p.requires_grad, params)

    if optimizer == 'sgd':
        return torch.optim.SGD(
            params, args.learning_rate, momentum=args.momentum,
            nesterov=True, weight_decay=args.weight_decay
        )
    elif optimizer == 'adam':
        return torch.optim.Adam(
            params, args.learning_rate,
            weight_decay=args.weight_decay
        )
    elif optimizer == 'rmsprop':
        return torch.optim.RMSprop(
            params, args.learning_rate,
            weight_decay=args.weight_decay
        )
    elif optimizer == 'sgd_nn':
        return torch.optim.SGD(
            params, args.learning_rate, momentum=0,
            nesterov=False, weight_decay=0
        )
    elif optimizer == 'adadelta':
        return torch.optim.Adadelta(
            params, args.learning_rate,
            weight_decay=args.weight_decay
        )


def init_params(model, args=None):
    """
    Initialize parameters in model

    Conv2d      : Xavier-Normal
    BatchNorm2d : Weight=1, Bias=0
    Linear      : Xavier-Normal

    """
    for m in model.modules():
        if isinstance(m, nn.Conv2d):
            nn.init.xavier_normal_(m.weight)
            if m.bias is not None:
                m.bias.data.zero_()

        elif isinstance(m, nn.Linear):
            nn.init.xavier_normal_(m.weight)
            m.bias.data.zero_()

        elif hasattr(m, '_modules'):
            for module in m._modules:
                try: init_params(module, args=args)
                except: continue
