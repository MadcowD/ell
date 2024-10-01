

import torch as th


weights = th.nn.Parameter(th.randn(10))


def forward(x):
    return x * weights


x = th.randn(10)

print(forward(x))
print(weights)

# OOOH WAHT IF WE DID MANY TYPES OF LEARNABLES in