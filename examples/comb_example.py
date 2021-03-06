# -*- coding: utf-8 -*-
"""
Example of combining multiple base outlier decision_scores_
Four combination frameworks are demonstrated

1. Mean: take the average of all base detectors
2. Max : take the maximum score across all detectors as the score
3. Average of Maximum (AOM)
4. Maximum of Average (MOA)

"""
import os, sys

# temporary solution for relative imports in case pyod is not installed
# if pyod is installed, no need to use the following line
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from scipy.io import loadmat

from pyod.models.knn import KNN
from pyod.models.combination import aom, moa
from pyod.utils.utility import precision_n_scores
from pyod.utils.utility import standardizer
from pyod.utils.load_data import generate_data

if __name__ == "__main__":

    n_clf = 20  # number of base detectors
    ite = 10  # number of iterations

    mat_file = 'cardio.mat'

    try:
        mat = loadmat(os.path.join('example_data', mat_file))

    except TypeError:
        print('{data_file} does not exist. Use generated data'.format(
            data_file=mat_file))
        X, y, _ = generate_data(train_only=True)  # load data
    except IOError:
        print('{data_file} does not exist. Use generated data'.format(
            data_file=mat_file))
        X, y, _ = generate_data(train_only=True)  # load data
    else:
        X = mat['X']
        y = mat['y'].ravel()

    # lists for storing roc information
    roc_mean = []
    roc_max = []
    roc_aom = []
    roc_moa = []

    prn_mean = []
    prn_max = []
    prn_aom = []
    prn_moa = []

    print('Combining {n_clf} kNN detectors'.format(n_clf=n_clf))
    for t in range(ite):
        X_train, X_test, y_train, y_test = train_test_split(X, y,
                                                            test_size=0.4)

        # standardizing data for processing
        X_train_norm, X_test_norm = standardizer(X_train, X_test)

        # initialize 20 base detectors for combination
        k_list = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140,
                  150, 160, 170, 180, 190, 200]

        train_scores = np.zeros([X_train.shape[0], n_clf])
        test_scores = np.zeros([X_test.shape[0], n_clf])

        for i in range(n_clf):
            k = k_list[i]

            clf = KNN(n_neighbors=k, method='largest')
            clf.fit(X_train_norm)

            train_scores[:, i] = clf.decision_scores_
            test_scores[:, i] = clf.decision_function(X_test_norm)

        # decision_scores_ have to be normalized before combination
        train_scores_norm, test_scores_norm = standardizer(train_scores,
                                                           test_scores)

        # combination by mean
        comb_by_mean = np.mean(test_scores_norm, axis=1)
        roc_mean.append(roc_auc_score(y_test, comb_by_mean))
        prn_mean.append(precision_n_scores(y_test, comb_by_mean))
        print('ite', t + 1, 'comb by mean,',
              'ROC:', roc_auc_score(y_test, comb_by_mean),
              'precision@n_train_:', precision_n_scores(y_test, comb_by_mean))

        # combination by max
        comb_by_max = np.max(test_scores_norm, axis=1)
        roc_max.append(roc_auc_score(y_test, comb_by_max))
        prn_max.append(precision_n_scores(y_test, comb_by_max))
        print('ite', t + 1, 'comb by max,', 'ROC:',
              roc_auc_score(y_test, comb_by_max),
              'precision@n_train_:', precision_n_scores(y_test, comb_by_max))

        # combination by aom
        comb_by_aom = aom(test_scores_norm, 5)
        roc_aom.append(roc_auc_score(y_test, comb_by_aom))
        prn_aom.append(precision_n_scores(y_test, comb_by_aom))
        print('ite', t + 1, 'comb by aom,', 'ROC:',
              roc_auc_score(y_test, comb_by_aom),
              'precision@n_train_:', precision_n_scores(y_test, comb_by_aom))

        # combination by moa
        comb_by_moa = moa(test_scores_norm, 5)
        roc_moa.append(roc_auc_score(y_test, comb_by_moa))
        prn_moa.append(precision_n_scores(y_test, comb_by_moa))
        print('ite', t + 1, 'comb by moa,', 'ROC:',
              roc_auc_score(y_test, comb_by_moa),
              'precision@n_train_:', precision_n_scores(y_test, comb_by_moa))

        print()

    ##########################################################################
    print('summary of {ite} iterations'.format(ite=ite))
    print('comb by mean, ROC: {roc}, precision@n_train_: {prn}'.format(
        roc=np.mean(roc_mean), prn=np.mean(prn_mean)))
    print('comb by max, ROC: {roc}, precision@n_train_: {prn}'.format(
        roc=np.mean(roc_max), prn=np.mean(prn_max)))
    print('comb by aom, ROC: {roc}, precision@n_train_: {prn}'.format(
        roc=np.mean(roc_aom), prn=np.mean(prn_aom)))
    print('comb by moa, ROC: {roc}, precision@n_train_: {prn}'.format(
        roc=np.mean(roc_moa), prn=np.mean(prn_moa)))
