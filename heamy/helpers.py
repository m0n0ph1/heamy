# coding:utf-8
from collections import defaultdict

import numpy as np
import pandas as pd
import shutil
import os
from scipy.optimize import minimize
from six.moves import range


def report_score(scores, metric=None):
    if metric is not None:
        print('Metric: %s' % metric.__name__)
    if len(scores) == 1:
        print('Accuracy: %s' % scores[0])
    else:
        print('Folds accuracy: %s' % scores)
        print('Mean accuracy: %s' % np.mean(scores))
        print('Standard Deviation: %s' % np.std(scores))
        print('Variance: %s' % np.var(scores))


def tsplit(df, shape):
    """Split array into two parts."""
    if isinstance(df, (pd.DataFrame, pd.Series)):
        return df.iloc[0:shape], df.iloc[shape:]
    else:
        return df[0:shape], df[shape:]


def concat(*args):
    """Concatenate a sequence of pandas or numpy objects into one entity."""
    if all([isinstance(df, (pd.DataFrame, pd.Series)) for df in args]):
        return pd.concat(args)
    else:
        return np.concatenate(args)


def reshape_1d(df):
    """If parameter is 1D row vector then convert it into 2D matrix."""
    shape = df.shape
    if len(shape) == 1:
        return df.reshape(shape[0], 1)
    else:
        return df


def idx(df, index):
    if isinstance(df, (pd.DataFrame, pd.Series)):
        return df.iloc[index]
    else:
        return df[index, :]


def generate_columns(df, name):
    if len(df.shape) == 1:
        col_count = 1
    else:
        col_count = df.shape[1]
    if col_count == 1:
        return [name]
    else:
        return ['%s_%s' % (name, i) for i in range(col_count)]


class Optimizer(object):
    def __init__(self, models, scorer, test_size=0.2):
        self.test_size = test_size
        self.scorer = scorer
        self.models = models
        self.predictions = []
        self.y = None

        self._predict()

    def _predict(self):
        for model in self.models:
            y_true_list, y_pred_list = model.validate(k=1, test_size=self.test_size)
            if self.y is None:
                self.y = y_true_list[0]
            self.predictions.append(y_pred_list[0])

    def loss_func(self, weights):
        final_prediction = 0
        for weight, prediction in zip(weights, self.predictions):
            final_prediction += weight * prediction
        return self.scorer(self.y, final_prediction)

    def minimize(self, method):
        starting_values = [0.5] * len(self.predictions)
        cons = ({'type': 'eq', 'fun': lambda w: 1 - sum(w)})
        bounds = [(0, 1)] * len(self.predictions)
        res = minimize(self.loss_func, starting_values, method=method, bounds=bounds, constraints=cons)
        print('Best Score (%s): %s' % (self.scorer.__name__, res['fun']))
        print('Best Weights: %s' % res['x'])
        return res['x']


def group_models(models, params):
    y_preds_grouped = defaultdict(list)
    y_true_grouped = {}
    for model in models:
        y_true_list, y_pred_list = model.validate(**params)
        for i, (y_true, y_pred) in enumerate(zip(y_true_list, y_pred_list)):
            if i not in y_true_grouped:
                y_true_grouped[i] = y_true
            y_preds_grouped[i].append(y_pred)
    return y_preds_grouped, y_true_grouped


def flush_cache():
    cache_dir = '.cache/heamy/'
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)