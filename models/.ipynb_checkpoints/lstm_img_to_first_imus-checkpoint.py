"""
=================
This model is a Recurrent model for Inferring the action of the dog. Given a sequence of images, infer the imu changes corresponding to those frames.
=================
"""

import torch
import torch.nn as nn
import pdb
import torch.nn.functional as F
import torch.optim as optim
import numpy as np

from torchvision.models import alexnet as torchvision_alexnet
from extensions.multi_label_cross_entropy import MultiLabelCrossEntropyLoss
from .basemodel import BaseModel
from torch.autograd import Variable
from .lstm import Lstm
from training import metrics


class LstmImg2FirstImus(BaseModel):
    metric = [metrics.SequenceMultiClassMetric, metrics.AngleEvaluationMetric]

    def __init__(self, args):
        super(LstmImg2FirstImus, self).__init__()

        assert (args.sequence_length == args.input_length and
                args.input_length >= args.output_length)

        self.input_length = args.input_length
        self.output_length = args.output_length
        self.class_weights = args.dataset.CLASS_WEIGHTS[torch.LongTensor(
            args.imus)]

        self.embedding_input = nn.Linear(args.image_feature, args.hidden_size)
        self.lstm = Lstm(args)

    def forward(self, input, target):
        input = input[:, :self.input_length]
        output_indices = list(range(0, self.output_length))
        target = target[:, :self.output_length]
        input = input.transpose(0, 1)
        embedded_input = self.embedding_input(input)
        full_output = self.lstm(embedded_input, None)
        return full_output.transpose(
            0, 1), target, torch.LongTensor(output_indices)

    def loss(self):
        return MultiLabelCrossEntropyLoss(self.class_weights)

    def optimizer(self):
        return optim.Adam(self.parameters(), lr=0.001)

    def learning_rate(self, epoch):
        base_lr = 0.001
        decay_rate = 0.1
        step = 90
        assert 1 <= epoch
        if 1 <= epoch <= step:
            return base_lr
        elif step <= epoch <= step * 2:
            return base_lr * decay_rate
        elif step * 2 <= epoch <= step * 3:
            return base_lr * decay_rate * decay_rate
        else:
            return base_lr * decay_rate * decay_rate * decay_rate
