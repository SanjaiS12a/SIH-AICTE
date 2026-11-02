import hashlib
from django.test import SimpleTestCase
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace
from tests.research.representations import representations, passages


class LiteralRepresentationTests(SimpleTestCase):
    def setUp(self):
        self.tokenizer=Tokenizer(WordLevel({'[UNK]':0},unk_token='[UNK]'));self.tokenizer.pre_tokenizer=Whitespace()

    def test_long_unicode_description_preserves_offsets_and_every_word(self):
        description='  An allegation 🏫 about a refund.\n\n'+' '.join(['Evidence']*700)+'\n\nAcademic year 2026.'
        row={'summary':'Please investigate.','description':description}
        result=representations(row,self.tokenizer,limit=32)
        self.assertGreater(result['coverage']['description_passages'],20)
        self.assertFalse(result['coverage']['whole_description_in_combined_input'])
        for items in result['representations'].values():
            for item in items:
                self.assertLessEqual(len(self.tokenizer.encode(item['text']).ids),32)
                for part in item['parts']:
                    source=row[part['field']]
                    self.assertEqual(source[part['start']:part['end']],part['text'])
                    self.assertEqual(part['source_digest'],hashlib.sha256(source.encode()).hexdigest())
        recovered=''.join(p['text'] for p in passages('description',description,self.tokenizer,32))
        self.assertEqual(recovered.count('Evidence'),700)
        self.assertIn('Academic year 2026.',recovered)

    def test_missing_description_and_overlong_summary_are_explicit(self):
        result=representations({'summary':'word '*300,'description':''},self.tokenizer)
        self.assertEqual(result['representations']['summary'],[])
        self.assertEqual(result['representations']['summary_selected_description'],[])
        self.assertEqual(result['coverage']['description_passages'],0)

    def test_no_extraction_or_fact_inference_is_fabricated(self):
        row={'summary':'Review refund','description':'Paid in August, year unknown. Please return the fee.'}
        result=representations(row,self.tokenizer)
        self.assertEqual(result['representations']['paragraphs'][-1]['text'],row['description'])
        self.assertNotIn('incident_date',result)
