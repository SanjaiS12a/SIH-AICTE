import unittest

import numpy as np

from scripts.compare_fresh_models import education_pairs, summarize, unseen


class FreshComparisonTests(unittest.TestCase):
    def test_prior_sentence_excludes_either_side_and_preserves_new_pairs(self):
        rows = [{'sentence1': ' A\tB ', 'sentence2': 'new'},
                {'sentence1': 'new', 'sentence2': 'a b'},
                {'sentence1': 'fresh', 'sentence2': 'other'}]
        self.assertEqual(unseen(rows, {'a b'}), ([rows[2]], 2))

    def test_labels_and_frozen_threshold_account_for_all_predictions(self):
        fixture = {'families': [dict(id=str(i), anchor=f'a{i}', paraphrase=f'b{i}', distinct=f'c{i}') for i in range(2)]}
        rows = education_pairs(fixture)
        self.assertEqual([r['label'] for r in rows], [1, 0, 0, 1, 0, 0])
        result = summarize(np.array([.8, .9, .1, .4, .2, .3]), rows, .5)
        self.assertEqual((result['tp'], result['fp'], result['fn'], result['tn']), (1, 1, 1, 3))
        self.assertEqual(result['threshold'], .5)
        self.assertAlmostEqual(result['f1'], .5)


if __name__ == '__main__':
    unittest.main()
