__author__ = 'belinkov'

from netCDF4 import Dataset
from utils import *
from data_utils import load_extracted_data, Word
import numpy as np
import sys


def collect_predictions(num_labels, pred_filename):

    print 'collecting predictions'
    pred_classes = []
    with open(pred_filename) as f:
        count = 0
        for line in f:
            count += 1
            # if count % 1000 == 0:
            # print 'sequence:', count
            splt = line.strip().split(';')
            seq_id = splt[0]
            probs = [float(p) for p in splt[1:]]
            for letter_probs in grouper(probs, num_labels, 0):
                arg_best = np.argmax(letter_probs)
                pred_classes.append(arg_best)
    return pred_classes


def convert_file(word_filename, word_diac_filename, pred_csv_filename, pred_output_filename, train_nc_filename):
    """
    Convert Currennt output to predictions

    :param word_filename (str): file with words (non-diac)
    :param word_diac_filename (str): file with words (diac)
    :param pred_csv_filename (str): file in csv format with predictions
    :param pred_output_filename (str): file to write predictions in Kaldi format (bw-currennt)
    :param train_nc_filename (str): file in Currennt format that was used to train the model
    :return:
    """

    sequences = load_extracted_data(word_filename, word_diac_filename)

    train_nc_file = Dataset(train_nc_filename)
    num_labels = len(train_nc_file.dimensions['numLabels'])
    nc_labels = [''.join(l.data) for l in train_nc_file.variables['labels']]
    class2label = dict(zip(range(len(nc_labels)), nc_labels))
    print class2label

    g = open(pred_output_filename, 'w')
    f = open(pred_csv_filename)
    pred_lines = f.readlines()
    if len(pred_lines) != len(sequences):
        sys.stderr.write('Error: incompatible predicted lines and input sequences. Quitting.\n')
        return

    for i in xrange(len(pred_lines)):
        line = pred_lines[i]
        splt = line.strip().split(';')
        seq_id_pred = splt[0]
        probs = [float(p) for p in splt[1:]]
        sequence = sequences[i]
        if seq_id_pred != sequence.seq_id:
            sys.stderr.write('Error: seq id in text file ' + sequence.seq_id + \
                             ' != seq id in predicted currennt file ' + seq_id_pred + '. Quitting.\n')
            return
        g.write(sequence.seq_id)
        letters = sequences[i].get_sequence_letters(include_word_boundary=True)
        letter_idx = 0
        cur_word, cur_word_diac_pred = '', ''
        for letter_probs in grouper(probs, num_labels, 0):
            letter = letters[letter_idx]
            letter_idx += 1
            if letter == Word.WORD_BOUNDARY:
                if cur_word:
                    # print cur_word + ':' + cur_word_diac_pred
                    g.write(' ' + cur_word + ':' + cur_word_diac_pred)
                    cur_word, cur_word_diac_pred = '', ''
                continue
            cur_word += letter
            arg_best = np.argmax(letter_probs)
            pred_label = class2label[arg_best]
            # print letter, ':', pred_label
            cur_word_diac_pred += letter + pred_label
        g.write('\n')


    f.close()
    g.close()


def main():

    if len(sys.argv) == 6:
        convert_file(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        print 'USAGE: python ' + sys.argv[0] + ' <word file> <word diac file> <currennt pred csv file> <pred out file> <train nc file>'


if __name__ == '__main__':
    main()
