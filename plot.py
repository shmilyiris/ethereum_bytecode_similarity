import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import roc_curve
import numpy as np


def get_acc(df, t):
    pred_pos = df[df['score'] > t]
    pred_neg = df[df['score'] <= t]
    acc = (pred_pos[pred_pos['label'] == 1].shape[0] + pred_neg[pred_neg['label'] == -1].shape[0]) / \
          df.shape[0]
    return acc


class Plot():
    def __init__(self, eclone_res, baseline_res):
        self.eclone_res = pd.read_csv(eclone_res, encoding='utf-8-sig')
        self.baseline_res = pd.read_csv(baseline_res, encoding='utf-8-sig')

    def acc(self):
        thresholds = [0.98, 0.96, 0.94, 0.92, 0.9, 0.88, 0.86, 0.84, 0.82, 0.8, 0.7, 0.6]
        eclone_acc, baseline_acc = [], []
        for t in thresholds:
            eclone_acc.append(get_acc(self.eclone_res, t))
            baseline_acc.append(get_acc(self.baseline_res, t))
        bar_width = 0.3
        idx_eclone = np.arange(len(thresholds))
        idx_baseline = idx_eclone + bar_width
        plt.bar(idx_eclone, height=eclone_acc, width=bar_width, color='white', edgecolor='black', label='EClone')
        plt.bar(idx_baseline, height=baseline_acc, width=bar_width, color='white', hatch='xxx', edgecolor='#4625fd',
                label='Baseline')
        plt.xticks(idx_eclone + bar_width / 2, thresholds)
        plt.xlabel('Threshold')
        plt.ylabel('Accuracy of Clone Detection (%)')
        plt.title('Accuracy')
        plt.legend(loc='best')
        plt.savefig('./result/Accuracy_test.png', dpi=300)

    def roc(self):
        fpr_ec, tpr_ec, thresholds_ec = roc_curve(list(self.eclone_res['label']), list(self.eclone_res['score']))
        fpr_bl, tpr_bl, thresholds_bl = roc_curve(list(self.baseline_res['label']), list(self.baseline_res['score']))
        plt.plot(fpr_ec, tpr_ec, label='EClone', color='r')
        plt.plot(fpr_bl, tpr_bl, label='Baseline', color='g', linestyle='--')
        plt.title('ROC')
        plt.xlabel("False Positive Rate (%)", fontsize=15)
        plt.ylabel("True Positive Rate (%)", fontsize=15)
        plt.legend(loc='best')
        plt.savefig('./result/ROC_test.png', dpi=300)


if __name__ == '__main__':
    p = Plot('./test_EClone_final.csv', './test_Baseline_final.csv')
    # p.roc()
    p.acc()
