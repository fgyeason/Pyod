# -*- coding: utf-8 -*-
import math
import warnings

import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.utils import check_array
from sklearn.utils.validation import check_is_fitted
from sklearn.utils.multiclass import check_classification_targets

from .base import BaseDetector


class HBOS(BaseDetector):

    def __init__(self, bins=10, beta=0.5, contamination=0.1):

        super().__init__(contamination=contamination)
        self.bins = bins
        self.beta = beta
        # self.hist_ = None
        # self.bin_edges_ = None

    def fit(self, X, y=None):

        X = check_array(X)

        self.classes_ = 2  # default as binary classification
        if y is not None:
            check_classification_targets(y)
            print(np.unique(y, return_counts=True))
            self.classes_ = len(np.unique(y))
            warnings.warn(
                "y should not be presented in unsupervised learning.")

        n_train, dim_train = X.shape[0], X.shape[1]
        out_scores = np.zeros([n_train, dim_train])

        hist = np.zeros([self.bins, dim_train])
        bin_edges = np.zeros([self.bins + 1, dim_train])

        # build the bins
        for i in range(dim_train):
            hist[:, i], bin_edges[:, i] = np.histogram(X[:, i],
                                                       bins=self.bins,
                                                       density=True)
            # check the integrity
            assert (
                math.isclose(np.sum(hist[:, i] * np.diff(bin_edges[:, i])), 1))

        # calculate the threshold_
        for i in range(dim_train):
            # find histogram assignments of data points
            bin_ind = np.digitize(X[:, i], bin_edges[:, i], right=False)

            # very important to do scaling. Not necessary to use min max
            out_score = np.max(hist[:, i]) - hist[:, i]
            out_score = MinMaxScaler().fit_transform(out_score.reshape(-1, 1))

            for j in range(n_train):
                # out sample left
                if bin_ind[j] == 0:
                    dist = np.abs(X[j, i] - bin_edges[0, i])
                    bin_width = bin_edges[1, i] - bin_edges[0, i]
                    # assign it to bin 0
                    if dist < bin_width * self.beta:
                        out_scores[j, i] = out_score[bin_ind[j]]
                    else:
                        out_scores[j, i] = np.max(out_score)

                # out sample right
                elif bin_ind[j] == bin_edges.shape[0]:
                    dist = np.abs(X[j, i] - bin_edges[-1, i])
                    bin_width = bin_edges[-1, i] - bin_edges[-2, i]
                    # assign it to bin k
                    if dist < bin_width * self.beta:
                        out_scores[j, i] = out_score[bin_ind[j] - 2]
                    else:
                        out_scores[j, i] = np.max(out_score)
                else:
                    out_scores[j, i] = out_score[bin_ind[j] - 1]

        out_scores_sum = np.sum(out_scores, axis=1)
        self.hist_ = hist
        self.bin_edges_ = bin_edges
        self.decision_scores_ = out_scores_sum
        self._process_decision_scores()
        return self

    def decision_function(self, X):
        check_is_fitted(self, ['hist_', 'bin_edges_', 'decision_scores_',
                               'threshold_', 'labels_'])
        X = check_array(X)
        n_test, dim_test = X.shape[0], X.shape[1]
        out_scores = np.zeros([n_test, dim_test])

        for i in range(dim_test):
            # find histogram assignments of data points
            bin_ind = np.digitize(X[:, i], self.bin_edges_[:, i], right=False)

            # very important to do scaling. Not necessary to use min_max
            out_score = np.max(self.hist_[:, i]) - self.hist_[:, i]
            out_score = MinMaxScaler().fit_transform(out_score.reshape(-1, 1))

            for j in range(n_test):
                # out sample left
                if bin_ind[j] == 0:
                    dist = np.abs(X[j, i] - self.bin_edges_[0, i])
                    bin_width = self.bin_edges_[1, i] - self.bin_edges_[0, i]
                    # assign it to bin 0
                    if dist < bin_width * self.beta:
                        out_scores[j, i] = out_score[bin_ind[j]]
                    else:
                        out_scores[j, i] = np.max(out_score)

                # out sample right
                elif bin_ind[j] == self.bin_edges_.shape[0]:
                    dist = np.abs(X[j, i] - self.bin_edges_[-1, i])
                    bin_width = self.bin_edges_[-1, i] - self.bin_edges_[-2, i]
                    # assign it to bin k
                    if dist < bin_width * self.beta:
                        out_scores[j, i] = out_score[bin_ind[j] - 2]
                    else:
                        out_scores[j, i] = np.max(out_score)
                else:
                    out_scores[j, i] = out_score[bin_ind[j] - 1]

        out_scores_sum = np.sum(out_scores, axis=1)
        return out_scores_sum.ravel()

##############################################################################

# roc_result_hbos = []
# roc_result_knn = []
#
# prec_result_hbos = []
# prec_result_knn = []
#
# for t in range(10):
#     n_inliers = 1000
#     n_outliers = 100
#
#     n_inliers_test = 500
#     n_outliers_test = 50
#
#     offset = 2
#     contamination = n_outliers / (n_inliers + n_outliers)
#
#     # generate normal data
#     X1 = 0.3 * np.random.randn(n_inliers // 2, 2) - offset
#     X2 = 0.3 * np.random.randn(n_inliers // 2, 2) + offset
#     X = np.r_[X1, X2]
#     # generate outliers
#     X = np.r_[X, np.random.uniform(low=-6, high=6, size=(n_outliers, 2))]
#     y = np.zeros([X.shape[0], 1])
#     color = np.full([X.shape[0], 1], 'b', dtype=str)
#     y[n_inliers:] = 1
#     color[n_inliers:] = 'r'
#
#     # generate normal data
#     X1_test = 0.3 * np.random.randn(n_inliers_test // 2, 2) - offset
#     X2_test = 0.3 * np.random.randn(n_inliers_test // 2, 2) + offset
#     X_test = np.r_[X1_test, X2_test]
#     # generate outliers
#     X_test = np.r_[
#         X_test, np.random.uniform(low=-8, high=8, size=(n_outliers_test, 2))]
#     y_test = np.zeros([X_test.shape[0], 1])
#     color_test = np.full([X_test.shape[0], 1], 'b', dtype=str)
#     y_test[n_inliers_test:] = 1
#     color_test[n_inliers_test:] = 'r'
#
#     clf = Hbos(contamination=contamination, alpha=0.2, beta=0.5, bins=5)
#     clf.fit(X)
#     pred_score_hbos = clf.decision_function(X_test)
#     labels_ = clf.predict(X_test)
#
#     roc_result_hbos.append(roc_auc_score(y_test, pred_score_hbos))
#     prec_result_hbos.append(get_precn(y_test, pred_score_hbos))
#
#     clf_knn = Knn(n_neighbors=10, contamination=contamination, method='mean')
#     clf_knn.fit(X)
#     pred_score_knn = clf_knn.sample_scores(X_test)
#     roc_result_knn.append(roc_auc_score(y_test, pred_score_knn))
#     prec_result_knn.append(get_precn(y_test, pred_score_knn))
#     # print(get_precn(y_test, clf.decision_function(X_test)))
#     # print(roc_auc_score(y_test, clf.decision_function(X_test)))
#
# print(np.mean(roc_result_hbos), np.mean(prec_result_hbos))
# print(np.mean(roc_result_knn), np.mean(prec_result_knn))
#
# plt.figure(figsize=(9, 7))
# plt.scatter(X_test[:, 0], X_test[:, 1], c=labels_)
# plt.show()
