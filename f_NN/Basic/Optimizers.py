import numpy as np

from Util.Metas import TimingMeta


class Optimizer:
    def __init__(self, lr=0.01, cache=None):
        self.lr = lr
        self._cache = cache

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return str(self)

    def feed_variables(self, variables):
        self._cache = [
            np.zeros(var.shape) for var in variables
        ]

    def run(self, i, dw):
        pass

    def update(self):
        pass


class MBGD(Optimizer, metaclass=TimingMeta):
    def run(self, i, dw):
        return self.lr * dw


class Momentum(Optimizer, metaclass=TimingMeta):
    def __init__(self, lr=0.01, cache=None, epoch=100, floor=0.5, ceiling=0.999):
        Optimizer.__init__(self, lr, cache)
        self._momentum = floor
        self._step = (ceiling - floor) / epoch
        self._floor, self._ceiling = floor, ceiling

    def run(self, i, dw):
        velocity = self._cache
        velocity[i] = velocity[i] * self._momentum + self.lr * dw
        return velocity[i]

    def update(self):
        if self._momentum < self._ceiling:
            self._momentum += self._step


class NAG(Momentum, metaclass=TimingMeta):
    def run(self, i, dw):
        dw *= self.lr
        velocity = self._cache
        velocity[i] = self._momentum * velocity[i] + dw
        return self._momentum * velocity[i] + dw


class Adam(Optimizer, metaclass=TimingMeta):
    def __init__(self, lr=0.01, cache=None, beta1=0.9, beta2=0.999, eps=1e-8):
        Optimizer.__init__(self, lr, cache)
        self.beta1, self.beta2, self.eps = beta1, beta2, eps

    def feed_variables(self, variables):
        self._cache = [
            [np.zeros(var.shape) for var in variables],
            [np.zeros(var.shape) for var in variables],
        ]

    def run(self, i, dw):
        self._cache[0][i] = self._cache[0][i] * self.beta1 + (1 - self.beta1) * dw
        self._cache[1][i] = self._cache[1][i] * self.beta2 + (1 - self.beta2) * (dw ** 2)
        return self.lr * self._cache[0][i] / (np.sqrt(self._cache[1][i] + self.eps))


class RMSProp(Optimizer, metaclass=TimingMeta):
    def __init__(self, lr=0.01, cache=None, decay_rate=0.9, eps=1e-8):
        Optimizer.__init__(self, lr, cache)
        self.decay_rate, self.eps = decay_rate, eps

    def run(self, i, dw):
        self._cache[i] = self._cache[i] * self.decay_rate + (1 - self.decay_rate) * dw ** 2
        return self.lr * dw / (np.sqrt(self._cache[i] + self.eps))


# Factory

class OptFactory:
    available_optimizers = {
        "MBGD": MBGD, "Momentum": Momentum, "NAG": NAG, "Adam": Adam, "RMSProp": RMSProp
    }

    def get_optimizer_by_name(self, name, variables, lr, epoch):
        try:
            _optimizer = self.available_optimizers[name](lr)
            if variables is not None:
                _optimizer.feed_variables(variables)
            if epoch is not None and isinstance(_optimizer, Momentum):
                _optimizer.epoch = epoch
            return _optimizer
        except KeyError:
            raise NotImplementedError("Undefined Optimizer '{}' found".format(name))
