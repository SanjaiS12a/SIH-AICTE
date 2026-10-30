import unittest
from scripts.prepare_public_pairs import clean_training, normalized, split_dev, texts


class PublicDataTests(unittest.TestCase):
    def pair(self, left, right, label=1):
        return {'sentence1': left, 'sentence2': right, 'label': label}

    def test_training_rejects_heldout_duplicates_and_conflicting_labels(self):
        rows = [self.pair('heldout', 'x'), self.pair('A', 'B'), self.pair('B', 'A'),
                self.pair('conflict', 'other', 0), self.pair('other', 'conflict', 1)]
        cleaned, audit = clean_training(rows, {'heldout'})
        self.assertEqual(cleaned, [rows[1]])
        self.assertEqual(audit['heldout_sentence_overlap'], 1)
        self.assertEqual(audit['duplicate_pair'], 2)
        self.assertEqual(audit['conflicting_pair_groups_removed'], 1)

    def test_validation_components_never_cross_calibration_boundary(self):
        rows = [self.pair('a', 'b'), self.pair('b', 'c'), self.pair('d', 'e')]
        split = split_dev(rows)
        self.assertFalse(texts(split['validation']) & texts(split['calibration']))
        self.assertEqual(sum(map(len, split.values())), 3)
        self.assertEqual(normalized('  A\tB  '), 'a b')


if __name__ == '__main__':
    unittest.main()
